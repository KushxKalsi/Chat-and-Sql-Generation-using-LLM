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

## Notes

- The app automatically stops llama-server when Flask exits
- First request may be slower as the model warms up
- Model stays loaded in memory for fast subsequent requests
- Debug mode is enabled by default (disable for production)
