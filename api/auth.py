# api/auth.py
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from .models import User

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use SHA-256 with salt
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    password_hash = hash_obj.hex()
    
    return password_hash, salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password against hash"""
    new_hash, _ = hash_password(password, salt)
    return new_hash == password_hash

def create_user(db: Session, username: str, email: str, password: str, role: str = "user") -> Optional[User]:
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        return None
    
    # Hash password
    password_hash, salt = hash_password(password)
    
    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        salt=salt,
        role=role,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not user.is_active:
        return None
    
    if not verify_password(password, user.password_hash, user.salt):
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)



