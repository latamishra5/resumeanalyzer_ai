#!/usr/bin/env python3
"""
Create Default Admin Account for Resume Analyzer AI
This script will create a default admin account with simple credentials.
"""

import sqlite3
from config.database import get_database_connection

def create_default_admin():
    """Create default admin account"""
    
    # Connect to database
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Delete existing admin records
        cursor.execute("DELETE FROM admin")
        
        # Create default admin credentials
        default_email = "admin@resumeanalyzer.ai"
        default_password = "admin123"
        
        # Insert new admin
        cursor.execute("INSERT INTO admin (email, password) VALUES (?, ?)", 
                      (default_email, default_password))
        conn.commit()
        
        print("="*50)
        print("DEFAULT ADMIN ACCOUNT CREATED!")
        print("="*50)
        print(f"Email: {default_email}")
        print(f"Password: {default_password}")
        print("="*50)
        print("\nUse these credentials to login in the sidebar.")
        
    except Exception as e:
        print(f"Error creating admin: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_default_admin()
