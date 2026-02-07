from flask import Flask, request, jsonify, render_template
import requests
import subprocess
import time
import os
import atexit
import pymysql
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

MODEL_PATH = os.path.abspath("llama-3.2-3b-instruct-q8_0.gguf")
LLAMA_SERVER_URL = f"http://127.0.0.1:{os.getenv('LLAMA_SERVER_PORT', '8080')}"
llama_process = None

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

print(f"Database config: {DB_CONFIG['host']}:{DB_CONFIG['port']} / {DB_CONFIG['database']}")

def get_db_connection():
    """Create a database connection"""
    try:
        print(f"Attempting to connect to {DB_CONFIG['host']}:{DB_CONFIG['port']} as {DB_CONFIG['user']}")
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        print("✓ Database connection successful!")
        return connection
    except pymysql.err.OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  User: {DB_CONFIG['user']}")
        print(f"  Database: {DB_CONFIG['database']}")
        return None
    except Exception as e:
        print(f"✗ Unexpected database error: {e}")
        return None

def get_table_schema():
    """Get schema information for all tables in the database"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            
            schema_info = {}
            for table in tables:
                # Get columns for each table
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                schema_info[table] = columns
            
            return schema_info
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return None
    finally:
        connection.close()

def execute_query(sql_query):
    """Execute a SQL query and return results"""
    connection = get_db_connection()
    if not connection:
        return {"error": "Database connection failed"}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            return {
                "success": True,
                "data": results,
                "row_count": len(results)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        connection.close()

def query_llama(prompt, max_tokens=512, temperature=0.7, stop=None):
    """Query the LLaMA model via llama-server"""
    try:
        response = requests.post(
            f"{LLAMA_SERVER_URL}/completion",
            json={
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": temperature,
                "stop": stop or ["<|eot_id|>"]
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['content'].strip()
        else:
            return f"Error: Server returned {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def start_llama_server():
    """Start llama-server in the background"""
    global llama_process
    
    # Check if we're on Windows or have llama-server
    if os.name != 'nt':
        print("Skipping llama-server (not on Windows)")
        return False
    
    llama_server_path = r"C:\Users\sanify\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"
    
    if not os.path.exists(llama_server_path):
        print("Error: llama-server not found")
        return False
    
    print(f"Starting llama-server with model: {MODEL_PATH}")
    
    llama_process = subprocess.Popen(
        [
            llama_server_path,
            "-m", MODEL_PATH,
            "--port", os.getenv('LLAMA_SERVER_PORT', '8080'),
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
    for i in range(60):
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
    
    # Check if llama-server is available
    try:
        response = requests.get(f"{LLAMA_SERVER_URL}/health", timeout=1)
        if response.status_code != 200:
            return jsonify({'error': 'LLaMA server not available. Chat feature requires Windows with llama-server.'}), 503
    except:
        return jsonify({'error': 'LLaMA server not available. Chat feature requires Windows with llama-server.'}), 503
    
    prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    
    response = query_llama(prompt, max_tokens=512, temperature=0.7)
    return jsonify({'response': response})

@app.route('/ask-database', methods=['POST'])
def ask_database():
    """Natural language database query interface"""
    data = request.json
    user_question = data.get('question', '')
    
    if not user_question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Check if llama-server is available
    try:
        response = requests.get(f"{LLAMA_SERVER_URL}/health", timeout=1)
        if response.status_code != 200:
            return jsonify({'error': 'LLaMA server not available. This feature requires Windows with llama-server. Use "Load Schema" to view database structure.'}), 503
    except:
        return jsonify({'error': 'LLaMA server not available. This feature requires Windows with llama-server. Use "Load Schema" to view database structure.'}), 503
    
    # Step 1: Get database schema
    schema = get_table_schema()
    if not schema:
        return jsonify({'error': 'Could not fetch database schema'}), 500
    
    # Format schema for the model
    schema_text = "Database Schema:\n"
    for table, columns in schema.items():
        schema_text += f"\nTable: {table}\n"
        for col in columns:
            schema_text += f"  - {col['Field']} ({col['Type']})"
            if col['Key'] == 'PRI':
                schema_text += " [PRIMARY KEY]"
            if col['Null'] == 'NO':
                schema_text += " [NOT NULL]"
            schema_text += "\n"
    
    # Step 2: Generate SQL query
    sql_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert SQL query generator. Generate ONLY the SQL query without any explanations or markdown.
{schema_text}<|eot_id|><|start_header_id|>user<|end_header_id|>
Generate a SQL query for: {user_question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
SELECT"""
    
    sql_query = "SELECT" + query_llama(sql_prompt, max_tokens=256, temperature=0.2)
    sql_query = sql_query.strip()
    
    # Clean up the query
    if '```' in sql_query:
        sql_query = sql_query.split('```')[0].strip()
    if not sql_query.endswith(';'):
        sql_query += ';'
    
    # Step 3: Execute the query
    query_result = execute_query(sql_query)
    
    if not query_result.get('success'):
        return jsonify({
            'error': 'Query execution failed',
            'sql': sql_query,
            'details': query_result.get('error')
        }), 400
    
    # Step 4: Analyze results with LLaMA
    results_json = json.dumps(query_result['data'], indent=2, default=str)
    
    analysis_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a data analyst. Analyze the query results and provide insights in natural language.<|eot_id|><|start_header_id|>user<|end_header_id|>
Question: {user_question}

SQL Query: {sql_query}

Results ({query_result['row_count']} rows):
{results_json}

Provide a clear, concise analysis of this data:<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    
    analysis = query_llama(analysis_prompt, max_tokens=512, temperature=0.7)
    
    return jsonify({
        'question': user_question,
        'sql': sql_query,
        'row_count': query_result['row_count'],
        'data': query_result['data'],
        'analysis': analysis
    })

@app.route('/schema', methods=['GET'])
def get_schema():
    """Get database schema information"""
    schema = get_table_schema()
    if schema:
        return jsonify({'schema': schema})
    else:
        return jsonify({
            'error': 'Could not fetch schema. Check database connection.',
            'details': f'Trying to connect to {DB_CONFIG["host"]}:{DB_CONFIG["port"]}'
        }), 500

@app.route('/test-db', methods=['GET'])
def test_db():
    """Test database connection"""
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                cursor.execute("SELECT DATABASE()")
                database = cursor.fetchone()
            connection.close()
            return jsonify({
                'status': 'success',
                'message': 'Database connection successful',
                'version': version,
                'database': database,
                'host': DB_CONFIG['host'],
                'port': DB_CONFIG['port']
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Query failed: {str(e)}'
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'Could not connect to database',
            'host': DB_CONFIG['host'],
            'port': DB_CONFIG['port'],
            'user': DB_CONFIG['user']
        }), 500

@app.route('/generate-sql', methods=['POST'])
def generate_sql():
    """Generate SQL query without execution"""
    data = request.json
    user_request = data.get('request', '')
    schema = data.get('schema', '')
    
    if not user_request:
        return jsonify({'error': 'No request provided'}), 400
    
    # If no schema provided, fetch from database
    if not schema:
        db_schema = get_table_schema()
        if db_schema:
            schema_text = ""
            for table, columns in db_schema.items():
                cols = [f"{col['Field']}({col['Type']})" for col in columns]
                schema_text += f"{table}({', '.join(cols)}); "
            schema = schema_text
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert SQL query generator. Generate only the SQL query without explanations.
Database schema: {schema}<|eot_id|><|start_header_id|>user<|end_header_id|>
Generate a SQL query for: {user_request}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    
    sql_query = query_llama(prompt, max_tokens=256, temperature=0.3)
    
    if not sql_query.endswith(';'):
        sql_query += ';'
    
    return jsonify({'sql': sql_query})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('FLASK_PORT', 5000)), use_reloader=False)
