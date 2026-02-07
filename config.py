# Database Configuration
# This file contains default configuration values

import os

# Try to load from environment variables, fallback to defaults
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'kushkalsilav')
DB_NAME = os.getenv('DB_NAME', 'test')

# Flask configuration
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# LLaMA configuration
LLAMA_SERVER_PORT = int(os.getenv('LLAMA_SERVER_PORT', '8081'))

print(f"[CONFIG] Database: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
