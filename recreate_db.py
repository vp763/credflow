#!/usr/bin/env python3
"""Drop and recreate database tables."""

import asyncio
import sys

sys.path.insert(0, '/Users/mac/Documents/CredVault/apps/backend')

from app.core.database import drop_db, init_db

async def main():
    print("Dropping database...")
    try:
        await drop_db()
        print("Database dropped successfully!")
    except Exception as e:
        print(f"Error dropping database: {e}")
        import traceback
        traceback.print_exc()
    
    print("Initializing database...")
    try:
        await init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())