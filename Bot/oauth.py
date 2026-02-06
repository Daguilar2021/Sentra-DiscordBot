from flask import Flask, request
import requests
from .config import Config
from .dbLink import get_session
from .dbAccessLayer import User

app = Flask(__name__)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return "Error: No code", 400

    # 1. Exchange code for Token
    data = {
        'client_id': Config.CLIENT_ID,
        'client_secret': Config.CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': Config.REDIRECT_URI
    }
    r = requests.post('https://discord.com/api/oauth2/token', data=data, 
                      headers={'Content-Type': 'application/x-www-form-urlencoded'})
    access_token = r.json().get('access_token')

    # 2. Get User Email
    u_info = requests.get('https://discord.com/api/users/@me', 
                          headers={'Authorization': f'Bearer {access_token}'}).json()
    
    d_id = int(u_info['id'])
    d_email = u_info.get('email')

    # 3. Save to Postgres
    session = get_session()
    try:
        user = session.query(User).filter_by(discord_id=d_id).first()
        if not user:
            user = User(discord_id=d_id, email=d_email, is_verified=True)
            session.add(user)
        else:
            user.email = d_email
            user.is_verified = True
        session.commit()
        return "<h1>Success!</h1><p>You are now verified in the Sentra database.</p>"
    finally:
        session.close()