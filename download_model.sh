#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Download the specific model file from Hugging Face
hf download bartowski/Qwen2.5-1.5B-Instruct-GGUF --include "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf" --local-dir .

# Rename the downloaded file to model.gguf
mv Qwen2.5-1.5B-Instruct-Q4_K_M.gguf model.gguf

# Print success message
echo "success downloaded model sucess"
