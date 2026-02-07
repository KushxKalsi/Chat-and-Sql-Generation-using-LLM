#!/bin/bash
# Manually start llama-server for testing

MODEL_PATH="llama-3.2-3b-instruct-q8_0.gguf"
PORT=8081

echo "Starting llama-server..."
echo "Model: $MODEL_PATH"
echo "Port: $PORT"
echo ""

if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found: $MODEL_PATH"
    exit 1
fi

if ! command -v llama-server &> /dev/null; then
    echo "Error: llama-server not found in PATH"
    echo "Try: /usr/local/bin/llama-server"
    exit 1
fi

echo "Starting server (this may take a minute)..."
llama-server \
    -m "$MODEL_PATH" \
    --port $PORT \
    --host 127.0.0.1 \
    -ngl 0 \
    -t 4 \
    -c 2048

# Or if not in PATH:
# /usr/local/bin/llama-server -m "$MODEL_PATH" --port $PORT --host 127.0.0.1 -ngl 0 -t 4 -c 2048
