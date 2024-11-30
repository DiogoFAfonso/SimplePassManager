import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key

load_dotenv()
ENV_FILE = '.env'

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Please configure it in the .env file or environment variables.")

def load_or_generate_key():
    encryption_key = os.getenv('ENCRYPTION_KEY')
    
    if encryption_key:
        return encryption_key.encode()
    else:
        encryption_key = Fernet.generate_key().decode()
        if os.path.exists(ENV_FILE):
            set_key(ENV_FILE, 'ENCRYPTION_KEY', encryption_key)
        else:
            with open(ENV_FILE, 'w') as env_file:
                env_file.write(f"ENCRYPTION_KEY={encryption_key}\n")
        return encryption_key.encode()

ENCRYPTION_KEY = load_or_generate_key()