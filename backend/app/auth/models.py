"""
User models and database schema for authentication.

Production: Uses PostgreSQL via DATABASE_URL environment variable.
Development: Falls back to SQLite for local convenience.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
import os
import logging

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

# ── Database Configuration ────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./f1_strategy.db"  # SQLite ONLY for local development
)

# Railway PostgreSQL URLs sometimes use "postgres://" scheme — SQLAlchemy requires
# "postgresql://" for psycopg2. Patch the URL transparently.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("[DB] Patched postgres:// → postgresql:// for SQLAlchemy compatibility")

# Build engine kwargs based on database type
_is_sqlite = "sqlite" in DATABASE_URL
_engine_kwargs = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pool settings optimised for Railway
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_pre_ping"] = True  # Detects stale connections
    _engine_kwargs["pool_recycle"] = 300    # Recycle connections every 5 min

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models ────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class User(Base):
    """User database model."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(String, default="true")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, role={self.role})>"

    def to_dict(self):
        """Convert user to dictionary (excludes password)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active == "true"
        }


class AuditLog(Base):
    """Audit log for tracking user activity."""
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    params = Column(String, nullable=True)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    response_status = Column(Integer, nullable=True)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "username": self.username,
            "endpoint": self.endpoint,
            "method": self.method,
            "params": self.params,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ip_address": self.ip_address,
            "response_status": self.response_status
        }


# ── Pydantic API Schemas ───────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """User creation schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.VIEWER


class UserLogin(BaseModel):
    """User login schema."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response schema (no password)."""
    user_id: int
    username: str
    email: str
    role: str
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    is_active: bool


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None


# ── Database Utilities ────────────────────────────────────────────────────────

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    db_type = "SQLite (dev)" if _is_sqlite else "PostgreSQL (production)"
    logger.info(f"[DB] Database initialized: {db_type}")
    print(f"[OK] Database initialized: {db_type}")


def create_default_admin():
    """
    Create the default admin account on first startup.

    Credentials are sourced exclusively from environment variables:
        ADMIN_USERNAME  — defaults to "admin"
        ADMIN_EMAIL     — defaults to "admin@f1strategy.com"
        ADMIN_PASSWORD  — REQUIRED in production (no hardcoded fallback)

    Credentials are NEVER logged. The function is idempotent (safe to call
    on every startup — it only creates the user if no admin exists).
    """
    from .password_utils import get_password_hash

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@f1strategy.com")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_password:
        if _is_sqlite:
            # Development convenience only — never for production
            admin_password = "admin123"
            print("[WARN] ADMIN_PASSWORD not set — using dev default (SQLite mode only).")
            print("[WARN] Set ADMIN_PASSWORD env var before production deployment!")
        else:
            logger.error(
                "[SECURITY] ADMIN_PASSWORD env var is required for production (PostgreSQL). "
                "No admin account will be created. Set ADMIN_PASSWORD in Railway env vars."
            )
            print("[ERROR] ADMIN_PASSWORD not set. Skipping admin creation. "
                  "Set ADMIN_PASSWORD in Railway env vars and restart.")
            return

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            hashed = get_password_hash(admin_password)
            admin_user = User(
                username=admin_username,
                email=admin_email,
                hashed_password=hashed,
                role=UserRole.ADMIN,
                is_active="true"
            )
            db.add(admin_user)
            db.commit()
            # Log creation without exposing credentials
            print(f"[OK] Admin account created: username={admin_username!r}")
        else:
            logger.debug(f"[DB] Admin account already exists: {admin.username!r}")
    except Exception as e:
        logger.error(f"[DB] Failed to create admin account: {e}")
        print(f"[WARN] Could not create admin account: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    create_default_admin()
    print("\n[OK] Auth database setup complete!")
