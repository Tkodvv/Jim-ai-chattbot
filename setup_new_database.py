#!/usr/bin/env python3
"""
Setup script for Jim Bot's new database under new ownership.
Transfers ownership from oxy5535 to iivxfn (Izaiah).
"""

import os
import sys
from flask import Flask
from models import db, UserProfile, UserMemory, ConversationContext, ChatHistory, UserFact, create_app
from datetime import datetime

import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from models import db, UserProfile, UserMemory, UserFact, create_app


def setup_new_database():
    """Create fresh database tables and initialize with new owner"""
    print("🔄 Setting up new database for Jim Bot...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all existing tables (fresh start)
            print("🗑️  Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("📊 Creating new database tables...")
            db.create_all()
            
            # Create new owner profile (iivxfn - Izaiah)
            print("👑 Setting up new owner profile...")
            new_owner = UserProfile(
                user_id="556006898298650662",  # iivxfn's Discord ID
                username="yoda",               # Display name
                display_name="Izaiah",         # Real name
                is_creator=True,               # Mark as creator/owner
                interaction_count=0,
                last_interaction=datetime.utcnow(),
                preferred_name="Izaiah",       # Jim will call him Izaiah
                personality_notes="Main owner and creator of Jim Bot",
                relationship_status="owner"
            )
            db.session.add(new_owner)
            
            # Add memory about the new owner
            owner_memory = UserMemory(
                user_id="556006898298650662",
                memory_type="relationship",
                title="Owner Recognition", 
                content="iivxfn (real name: Izaiah, Discord username: yoda) is my owner and creator. He has full authority over my settings and operation.",
                importance=10,  # Highest importance
                source_message="Database setup",
                tags=["owner", "creator", "authority", "Izaiah"],
                created_at=datetime.utcnow(),
                last_referenced=datetime.utcnow(),
                reference_count=1
            )
            db.session.add(owner_memory)
            
            # Add fact about preferred name
            name_fact = UserFact(
                user_id="556006898298650662",
                key="preferred_name",
                value="Izaiah",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(name_fact)
            
            # Add fact about role
            role_fact = UserFact(
                user_id="556006898298650662", 
                key="role",
                value="owner_creator",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(role_fact)
            
            # Commit all changes
            db.session.commit()
            
            print("✅ Database setup complete!")
            print(f"👑 New owner: iivxfn (Izaiah) - ID: 556006898298650662")
            print(f"📝 Display name: yoda")
            print(f"🎯 Jim will address the owner as: Izaiah")
            print(f"🗃️ Fresh database created with new ownership structure")
            
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            db.session.rollback()
            return False
            
    return True

def verify_database():
    """Verify the database was set up correctly"""
    print("\n🔍 Verifying database setup...")
    
    app = create_app()
    with app.app_context():
        try:
            # Check if owner profile exists
            owner = UserProfile.query.filter_by(user_id="556006898298650662").first()
            if owner:
                print(f"✅ Owner profile found: {owner.display_name} ({owner.username})")
                print(f"✅ Creator status: {owner.is_creator}")
            else:
                print("❌ Owner profile not found!")
                return False
                
            # Check owner memories
            memories = UserMemory.query.filter_by(user_id="556006898298650662").count()
            print(f"✅ Owner memories: {memories}")
            
            # Check owner facts
            facts = UserFact.query.filter_by(user_id="556006898298650662").count()
            print(f"✅ Owner facts: {facts}")
            
            print("✅ Database verification successful!")
            return True
            
        except Exception as e:
            print(f"❌ Database verification failed: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Jim Bot Database Migration Script")
    print("📋 Transferring ownership from oxy5535 to iivxfn (Izaiah)")
    print("⚠️  This will create a fresh database!")
    
    response = input("\nContinue? (y/N): ").lower().strip()
    if response != 'y':
        print("❌ Migration cancelled.")
        sys.exit(0)
    
    # Setup new database
    if setup_new_database():
        # Verify setup
        if verify_database():
            print("\n🎉 Migration completed successfully!")
            print("🔄 Restart Jim Bot to use the new database.")
        else:
            print("\n⚠️  Migration completed but verification failed.")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
