#!/usr/bin/env python3
"""
Script to create an admin user
"""
import sys
sys.path.append('.')

from api.database import SessionLocal, engine
from api.models import Base
from api.auth import create_user

def main():
    # Create tables first
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    db = SessionLocal()
    try:
        # Create admin user
        admin = create_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="admin"
        )
        
        if admin:
            print(f"✅ Admin user created successfully!")
            print(f"   Username: admin")
            print(f"   Email: admin@example.com")
            print(f"   Password: admin123")
        else:
            print("❌ Admin user already exists or failed to create")
        
        # Create demo user
        user = create_user(
            db=db,
            username="user",
            email="user@example.com",
            password="user123",
            role="user"
        )
        
        if user:
            print(f"✅ Demo user created successfully!")
            print(f"   Username: user")
            print(f"   Email: user@example.com")
            print(f"   Password: user123")
        else:
            print("❌ Demo user already exists or failed to create")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()

