from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    textchanel_id = Column(BigInteger, unique=True)
    voicechanel_id = Column(BigInteger, unique=True)
    full_team = Column(Boolean, default=True)

    # Link back to the users (one team can have many members)
    members = relationship("User", back_populates="team")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, unique=True, nullable=False)
    email = Column(String(255), unique=True)
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