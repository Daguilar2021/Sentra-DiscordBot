import os
from dotenv import load_dotenv

# This looks for the .env file in the parent directory
load_dotenv()

class Config:
    TOKEN = os.getenv('BOT_TOKEN')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Ensure all required variables are present
    @classmethod
    def validate(cls):
        required = ['TOKEN', 'CLIENT_ID', 'CLIENT_SECRET', 'DATABASE_URL']
        for var in required:
            if not getattr(cls, var):
                raise ValueError(f"Missing environment variable: {var}")