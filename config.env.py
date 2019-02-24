import os

# Flask config
IP = os.environ.get('API_IP', "0.0.0.0")
PORT = os.environ.get('API_PORT', 8080)

# Database
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', "")
