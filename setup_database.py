#!/usr/bin/env python3
"""
Database setup script for Jim Discord Bot
Creates the jimbot database and tables if they don't exist
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the jimbot database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (default postgres database)
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='1136',
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='jimbot'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating jimbot database...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('jimbot')))
            print("Database 'jimbot' created successfully!")
        else:
            print("Database 'jimbot' already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Please ensure PostgreSQL is running and credentials are correct.")
        return False
    
    return True

def test_connection():
    """Test connection to the jimbot database"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:1136@localhost:5432/jimbot')
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Connected to PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

def create_tables():
    """Create the necessary tables using the models"""
    try:
        from models import create_app
        
        print("Creating database tables...")
        app = create_app()
        
        with app.app_context():
            from models import db
            db.create_all()
            print("Database tables created successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

if __name__ == "__main__":
    print("Jim Discord Bot Database Setup")
    print("=" * 35)
    
    # Step 1: Create database
    if not create_database():
        sys.exit(1)
    
    # Step 2: Test connection
    if not test_connection():
        sys.exit(1)
    
    # Step 3: Create tables
    if not create_tables():
        sys.exit(1)
    
    print("\nDatabase setup completed successfully!")
    print("You can now run the bot with: python main.py")