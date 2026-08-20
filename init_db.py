#!/usr/bin/env python3
"""Initialize database tables."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/mac/Documents/CredVault/apps/backend')

from app.core.database import init_db

async def main():
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