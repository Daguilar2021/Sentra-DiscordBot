# ./Sentra-DiscordBot/Bot/config.py
# This file handles the configuration of Sentra's environment variables.

import os
from dotenv import load_dotenv

# This looks for the .env file in the parent directory
load_dotenv()

class Config:
    TOKEN = os.getenv('BOT_TOKEN')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    API_URL = os.getenv('API_URL')
    DATABASE_URL = os.getenv('DATABASE_URL')
    CONNECTION_STRINGS = os.getenv('CONNECTION_STRINGS')

    
    # Ensure all required variables are present
    @classmethod
    def validate(cls):
        required = ['TOKEN', 'CLIENT_ID', 'CLIENT_SECRET', 'DATABASE_URL']
        for var in required:
            if not getattr(cls, var):
                raise ValueError(f"Missing environment variable: {var}")