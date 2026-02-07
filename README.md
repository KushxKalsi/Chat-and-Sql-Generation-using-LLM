# LLaMA Chat & SQL Generator

Flask application using LLaMA 3.2 3B model for chat and SQL query generation. Uses llama.cpp's server backend for efficient inference.

## Prerequisites

- Python 3.8+
- Windows (tested on Windows 10/11)
- Your LLaMA model file: `llama-3.2-3b-instruct-q8_0.gguf` in the project root

## Installation

### 1. Install llama.cpp

The app requires llama.cpp's server component. Install via winget:

```cmd
winget install llama.cpp
```

This installs `llama-server.exe` which the Flask app uses as a backend.

### 2. Install Python Dependencies

```cmd
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- requests (HTTP client for llama-server communication)

## Usage

### Start the Application

```cmd
python app.py
```

The app will:
1. Start llama-server in the background (takes ~10-30 seconds to load the model)
2. Wait for the server to be ready
3. Start the Flask web interface on http://127.0.0.1:5000

### Access the Web Interface

Open your browser to: **http://localhost:5000**

## Features

### 💬 Chat Interface
- General conversation with the LLaMA 3.2 3B model
- Supports multi-turn conversations
- Temperature: 0.7 (balanced creativity)
- Max tokens: 512 per response

### 🗄️ SQL Query Generator
- Convert natural language to SQL queries
- Optional database schema input for context-aware generation
- Temperature: 0.3 (more deterministic)
- Max tokens: 256 per query

**Example:**
- Schema: `users(id, name, email), orders(id, user_id, total, created_at)`
- Request: "Get all users who placed orders over $100 in the last month"
- Output: SQL query

## Architecture

```
┌─────────────┐      HTTP        ┌──────────────┐
│   Browser   │ ◄──────────────► │ Flask App    │
│  (Port 5000)│                  │ (app.py)     │
└─────────────┘                  └──────┬───────┘
                                        │ HTTP
                                        │ (Port 8080)
                                 ┌──────▼───────┐
                                 │ llama-server │
                                 │ (Background) │
                                 └──────────────┘
```

- **Flask App**: Handles web requests and UI
- **llama-server**: Runs the LLaMA model and provides completion API
- Communication via HTTP on localhost:8080

## Configuration

Edit `app.py` to customize:

```python
# Model settings
MODEL_PATH = "llama-3.2-3b-instruct-q8_0.gguf"  # Model file path
LLAMA_SERVER_URL = "http://127.0.0.1:8080"      # Server endpoint

# llama-server parameters (in start_llama_server function)
"-t", "4"        # CPU threads (increase for faster inference)
"-ngl", "0"      # GPU layers (set to -1 for full GPU offload if you have CUDA)
"--port", "8080" # Server port

# Generation parameters (in route handlers)
"n_predict": 512      # Max tokens for chat
"temperature": 0.7    # Chat randomness (0.0-1.0)
"temperature": 0.3    # SQL generation (lower = more deterministic)
```

## Troubleshooting

### Server fails to start
- Ensure llama.cpp is installed: `winget list llama.cpp`
- Check if port 8080 is available
- Verify model file exists in project directory

### Slow responses
- Increase CPU threads: Change `-t` parameter in `start_llama_server()`
- Use GPU acceleration: Change `-ngl` to `-1` (requires CUDA-capable GPU)
- Reduce max tokens in generation parameters

### Out of memory
- Use a smaller quantized model (e.g., Q4_K_M instead of Q8_0)
- Reduce context size by adding `-c 2048` to llama-server args

## API Endpoints

### POST /chat
Generate chat responses

**Request:**
```json
{
  "message": "Hello, how are you?"
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you! How can I help you today?"
}
```

### POST /generate-sql
Generate SQL queries

**Request:**
```json
{
  "request": "Get all active users",
  "schema": "users(id, name, email, active)"
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM users WHERE active = 1;"
}
```

## Production Deployment

Flask's built-in server is **not suitable for production**. Here's how to deploy properly:

### Option 1: Gunicorn (Linux/Unix)

**1. Install Gunicorn:**
```bash
pip install gunicorn
```

**2. Create a WSGI entry point (`wsgi.py`):**
```python
from app import app

if __name__ == "__main__":
    app.run()
```

**3. Run with Gunicorn:**
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
```

**4. Use systemd for auto-restart (Linux):**

Create `/etc/systemd/system/llama-flask.service`:
```ini
[Unit]
Description=LLaMA Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/your/app
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable llama-flask
sudo systemctl start llama-flask
```

### Option 2: Waitress (Windows/Cross-platform)

**1. Install Waitress:**
```cmd
pip install waitress
```

**2. Create production server file (`serve.py`):**
```python
from waitress import serve
from app import app

if __name__ == '__main__':
    print("Starting production server on http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000, threads=4)
```

**3. Run:**
```cmd
python serve.py
```

**4. Run as Windows Service:**

Use NSSM (Non-Sucking Service Manager):
```cmd
nssm install LLaMAFlask "C:\path\to\python.exe" "C:\path\to\serve.py"
nssm start LLaMAFlask
```

### Option 3: Docker Deployment

**1. Create `Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install llama.cpp dependencies
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install llama.cpp
RUN wget https://github.com/ggml-org/llama.cpp/releases/download/b7931/llama-b7931-bin-ubuntu-x64.zip \
    && unzip llama-b7931-bin-ubuntu-x64.zip -d /usr/local/bin/ \
    && rm llama-b7931-bin-ubuntu-x64.zip

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "300", "wsgi:app"]
```

**2. Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  llama-flask:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./llama-3.2-3b-instruct-q8_0.gguf:/app/llama-3.2-3b-instruct-q8_0.gguf
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

**3. Build and run:**
```bash
docker-compose up -d
```

### Option 4: Nginx Reverse Proxy

Use Nginx as a reverse proxy in front of your WSGI server:

**1. Install Nginx:**
```bash
sudo apt install nginx
```

**2. Configure Nginx (`/etc/nginx/sites-available/llama-flask`):**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

**3. Enable and restart:**
```bash
sudo ln -s /etc/nginx/sites-available/llama-flask /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 5: Cloud Platforms

#### AWS EC2
1. Launch EC2 instance (t3.large or larger recommended)
2. Install dependencies and llama.cpp
3. Use Gunicorn + systemd
4. Configure security groups (open port 80/443)
5. Use Elastic Load Balancer for scaling

#### Google Cloud Run
1. Build Docker image
2. Push to Google Container Registry
3. Deploy to Cloud Run with sufficient memory (8GB+)
4. Set timeout to 300s or higher

#### Azure App Service
1. Create App Service (Linux)
2. Deploy via Git or Docker
3. Configure startup command: `gunicorn --bind 0.0.0.0:8000 wsgi:app`
4. Scale up to appropriate tier (B2 or higher)

#### Heroku
1. Create `Procfile`:
```
web: gunicorn wsgi:app
```
2. Deploy via Git:
```bash
heroku create your-app-name
git push heroku main
```

### Production Checklist

- [ ] Disable Flask debug mode (`debug=False`)
- [ ] Use production WSGI server (Gunicorn/Waitress)
- [ ] Set up reverse proxy (Nginx/Apache)
- [ ] Enable HTTPS with SSL certificate (Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Set up logging and monitoring
- [ ] Implement rate limiting
- [ ] Add authentication if needed
- [ ] Configure environment variables for secrets
- [ ] Set up automatic backups
- [ ] Monitor resource usage (CPU/RAM)
- [ ] Implement health checks
- [ ] Set up auto-restart on failure

### Security Considerations

**1. Add API authentication:**
```python
from functools import wraps
from flask import request, jsonify

API_KEY = "your-secret-key"

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/chat', methods=['POST'])
@require_api_key
def chat():
    # ... existing code
```

**2. Add rate limiting:**
```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    # ... existing code
```

**3. Use environment variables:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
MODEL_PATH = os.getenv('MODEL_PATH', 'llama-3.2-3b-instruct-q8_0.gguf')
```

### Performance Optimization

1. **Enable GPU acceleration** (if available):
   - Change `-ngl 0` to `-ngl -1` in llama-server args
   - Requires CUDA-capable GPU

2. **Increase worker processes**:
   - Gunicorn: `--workers 4` (2-4 × CPU cores)
   - Waitress: `threads=8`

3. **Add caching**:
```bash
pip install flask-caching
```

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/chat', methods=['POST'])
@cache.cached(timeout=300, query_string=True)
def chat():
    # ... existing code
```

4. **Use CDN for static files**:
   - Serve CSS/JS from CDN
   - Use cloud storage for large assets

## Notes

- The app automatically stops llama-server when Flask exits
- First request may be slower as the model warms up
- Model stays loaded in memory for fast subsequent requests
- Debug mode is enabled by default (disable for production)
- Production deployments require 8GB+ RAM for the 3B model
- Consider using smaller quantized models (Q4_K_M) for resource-constrained environments
