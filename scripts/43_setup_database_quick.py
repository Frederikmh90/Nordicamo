#!/usr/bin/env python3
"""
Quick database setup script - creates database and user if they don't exist.
Run this on the remote server.
"""
import psycopg2
import sys

def setup_database():
    """Create database and user for NAMO."""
    try:
        # Connect as postgres user
        print("Connecting to PostgreSQL as postgres user...")
        conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            database='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if namo_db exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'namo_db'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database namo_db...")
            cur.execute("CREATE DATABASE namo_db")
            print("✓ Database created")
        else:
            print("Database namo_db already exists")
        
        # Check if namo_user exists
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'namo_user'")
        user_exists = cur.fetchone()
        
        if not user_exists:
            print("Creating user namo_user...")
            cur.execute("CREATE USER namo_user WITH PASSWORD '<DB_PASSWORD>'")
            cur.execute("ALTER USER namo_user CREATEDB")
            print("✓ User created")
        else:
            print("User namo_user already exists")
        
        # Grant privileges
        cur.execute("GRANT ALL PRIVILEGES ON DATABASE namo_db TO namo_user")
        print("✓ Privileges granted")
        
        # Test connection as namo_user
        conn.close()
        
        print("\nTesting connection as namo_user...")
        test_conn = psycopg2.connect(
            host='localhost',
            user='namo_user',
            password='<DB_PASSWORD>',
            database='namo_db'
        )
        test_cur = test_conn.cursor()
        test_cur.execute("SELECT version();")
        version = test_cur.fetchone()[0]
        print(f"✓ Connection successful!")
        print(f"  PostgreSQL version: {version.split(',')[0]}")
        test_conn.close()
        
        print("\n✅ Database setup complete!")
        print("\nNext steps:")
        print("1. Create schema: python3 scripts/03_create_database_schema.py --create-db")
        print("2. Test NLP processing: python3 scripts/02_nlp_processing_from_db.py --dry-run")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()


