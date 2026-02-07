#!/bin/bash
# Install llama.cpp on Raspberry Pi

echo "=================================="
echo "Installing llama.cpp on Raspberry Pi"
echo "=================================="
echo ""

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# Clone llama.cpp
echo "Cloning llama.cpp..."
cd ~
if [ -d "llama.cpp" ]; then
    echo "llama.cpp already exists, pulling latest..."
    cd llama.cpp
    git pull
else
    git clone https://github.com/ggml-org/llama.cpp.git
    cd llama.cpp
fi

# Build for ARM (Raspberry Pi)
echo "Building llama.cpp for ARM..."
mkdir -p build
cd build
cmake .. -DLLAMA_NATIVE=OFF
cmake --build . --config Release -j 4

# Create symlink
echo "Creating symlink..."
sudo ln -sf ~/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
sudo ln -sf ~/llama.cpp/build/bin/llama-cli /usr/local/bin/llama-cli

# Verify installation
echo ""
echo "Verifying installation..."
if command -v llama-server &> /dev/null; then
    echo "✓ llama-server installed successfully!"
    llama-server --version
else
    echo "✗ Installation failed"
    exit 1
fi

echo ""
echo "=================================="
echo "Installation complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Download a model (e.g., llama-3.2-3b-instruct-q4_k_m.gguf)"
echo "2. Place it in your project directory"
echo "3. Update MODEL_PATH in app.py"
echo "4. Run: python app.py"
