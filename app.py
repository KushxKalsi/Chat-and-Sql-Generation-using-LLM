from flask import Flask, request, jsonify, render_template
import requests
import subprocess
import time
import os
import atexit

app = Flask(__name__)

MODEL_PATH = os.path.abspath("llama-3.2-3b-instruct-q8_0.gguf")
LLAMA_SERVER_URL = "http://127.0.0.1:8080"
llama_process = None

def start_llama_server():
    """Start llama-server in the background"""
    global llama_process
    
    llama_server_path = r"C:\Users\sanify\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"
    
    if not os.path.exists(llama_server_path):
        print("Error: llama-server not found")
        return False
    
    print(f"Starting llama-server with model: {MODEL_PATH}")
    
    llama_process = subprocess.Popen(
        [
            llama_server_path,
            "-m", MODEL_PATH,
            "--port", "8080",
            "--host", "127.0.0.1",
            "-ngl", "0",
            "-t", "4",
            "--log-disable"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    for i in range(60):  # Increased timeout
        try:
            response = requests.get(f"{LLAMA_SERVER_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✓ llama-server is ready!")
                return True
        except:
            time.sleep(2)
            if i % 5 == 0:
                print(f"  Still waiting... ({i*2}s)")
    
    print("Failed to start llama-server")
    return False

def stop_llama_server():
    """Stop llama-server on exit"""
    global llama_process
    if llama_process:
        print("Stopping llama-server...")
        llama_process.terminate()
        llama_process.wait()

atexit.register(stop_llama_server)

# Start the server when the app starts
if not start_llama_server():
    print("WARNING: Could not start llama-server. Requests will fail.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    
    try:
        response = requests.post(
            f"{LLAMA_SERVER_URL}/completion",
            json={
                "prompt": prompt,
                "n_predict": 512,
                "temperature": 0.7,
                "stop": ["<|eot_id|>"]
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({'response': result['content'].strip()})
        else:
            return jsonify({'error': f'Server error: {response.status_code}'}), 500
    except requests.Timeout:
        return jsonify({'error': 'Request timed out'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-sql', methods=['POST'])
def generate_sql():
    data = request.json
    user_request = data.get('request', '')
    schema = data.get('schema', '')
    
    if not user_request:
        return jsonify({'error': 'No request provided'}), 400
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert SQL query generator. Generate only the SQL query without explanations.
{f'Database schema: {schema}' if schema else ''}<|eot_id|><|start_header_id|>user<|end_header_id|>
Generate a SQL query for: {user_request}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    
    try:
        response = requests.post(
            f"{LLAMA_SERVER_URL}/completion",
            json={
                "prompt": prompt,
                "n_predict": 256,
                "temperature": 0.3,
                "stop": ["<|eot_id|>"]
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            sql_query = result['content'].strip()
            
            if not sql_query.endswith(';'):
                sql_query += ';'
            
            return jsonify({'sql': sql_query})
        else:
            return jsonify({'error': f'Server error: {response.status_code}'}), 500
    except requests.Timeout:
        return jsonify({'error': 'Request timed out'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
