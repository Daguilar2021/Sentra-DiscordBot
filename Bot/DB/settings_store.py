from Bot.DB.dbLink import get_session
from Bot.DB.dbAccessLayer import GuildSettings

def get_or_create_settings(guild_id: int) -> GuildSettings:
    db = get_session()
    try:
        row = db.query(GuildSettings).filter(GuildSettings.guild_id == guild_id).first()
        if not row:
            row = GuildSettings(guild_id=guild_id, team_chat_channel_ids=[])
            db.add(row)
            db.commit()
            db.refresh(row)
        return row
    finally:
        db.close()

def update_settings(guild_id: int, **fields) -> GuildSettings:
    db = get_session()
    try:
        row = db.query(GuildSettings).filter(GuildSettings.guild_id == guild_id).first()
        if not row:
            row = GuildSettings(guild_id=guild_id, team_chat_channel_ids=[])
            db.add(row)

        for key, value in fields.items():
            setattr(row, key, value)

        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()
