# ./Sentra-DiscordBot/Bot/DB/dbAccessLayer.py
# SQL Database Models for Sentra, using SQLAlchemy ORM, using postgresql, 
# This script creates the tables in the database, however it does not update them if they already exist.

from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    guild_id = Column(BigInteger, nullable=True)
    creator_id = Column(BigInteger, nullable=True)
    lobby_message_id = Column(BigInteger, nullable=True)

    textchanel_id = Column(BigInteger, unique=True)
    voicechanel_id = Column(BigInteger, unique=True)
    full_team = Column(Boolean, default=False)

    # Link back to the users (one team can have many members)
    members = relationship("User", back_populates="team")

class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('discord_id', 'guild_id', name='uq_user_per_guild'),
    )

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, nullable=False)
    guild_id = Column(BigInteger, nullable=False)
    email = Column(String(255))
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default='hacker')
    resume_data = Column(JSONB, nullable=True)

    # The Foreign Key link
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)

    # The relationship link
    team = relationship("Team", back_populates="members")
    

class GuildSettings(Base):
    __tablename__ = "guild_settings"

    # one row per server
    guild_id = Column(BigInteger, primary_key=True, index=True)

    # roles
    mentor_role_id = Column(BigInteger, nullable=True)
    ticket_support_role_id = Column(BigInteger, nullable=True)
    admin_role_id = Column(BigInteger, nullable=True)

    # channels (store as IDs)
    find_teammates_channel_id = Column(BigInteger, nullable=True)
    ticket_category_id = Column(BigInteger, nullable=True)
    ticket_panel_channel_id = Column(BigInteger, nullable=True)
    staff_channel_id = Column(BigInteger, nullable=True)
    team_category_id = Column(BigInteger, nullable=True)

    # team settings
    max_team_size = Column(Integer, default=4)

    # moderation settings
    mod_channel_id = Column(BigInteger, nullable=True)
    mod_toxicity_threshold = Column(Float, default=0.7)

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, index=True)
    user_id = Column(BigInteger, index=True)
    channel_id = Column(BigInteger, unique=True)
    status = Column(String(20), default='open') # 'open', 'closed'
    created_at = Column(BigInteger) # Store as timestamp
    claimed_by = Column(BigInteger, nullable=True)
    staff_message_id = Column(BigInteger, nullable=True)

class Infraction(Base):
    __tablename__ = "infractions"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, index=True)
    user_id = Column(BigInteger, index=True)
    message_content = Column(String(2000))
    toxicity_score = Column(Float)
    keywords = Column(JSONB, nullable=True)
    action_taken = Column(String(20))
    created_at = Column(BigInteger)
    reviewed = Column(Boolean, default=False)