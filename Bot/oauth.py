from flask import Flask, request, redirect
import requests
from .config import Config
from .DB.dbLink import get_session
from .DB.dbAccessLayer import User

app = Flask(__name__)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    guild_id_str = request.args.get('state')
    if not code: return "Error: No code", 400
    if not guild_id_str: return "Error: No state (guild_id) provided", 400
    try:
        guild_id = int(guild_id_str)
    except ValueError:
        return "Error: Invalid state", 400

    # Token
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

    # Get User Email
    u_info = requests.get('https://discord.com/api/users/@me', 
                          headers={'Authorization': f'Bearer {access_token}'}).json()
    
    d_id = int(u_info['id'])
    d_email = u_info.get('email')

    #Save to Postgres
    session = get_session()
    try:
        user = session.query(User).filter_by(discord_id=d_id, guild_id=guild_id).first()
        if not user:
            user = User(discord_id=d_id, guild_id=guild_id, email=d_email, is_verified=True)
            session.add(user)
        else:
            user.email = d_email
            user.is_verified = True
        session.commit()
        html_response = """
        <html>
            <body style="background-color: #1e1e2e; color: #cdd6f4; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
                <div style="text-align: center; background-color: #313244; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h1 style="color: #a6e3a1;">Verification Successful!</h1>
                    <p style="font-size: 18px;">You have successfully linked your Discord account.</p>
                    <p style="color: #9399b2;">You can now close this tab and return to Discord.</p>
                </div>
            </body>
        </html>
        """
        return html_response
    finally:
        session.close()
