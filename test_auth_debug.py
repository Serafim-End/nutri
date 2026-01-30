#!/usr/bin/env python3
"""
Run this inside the backend container to test auth with actual initData
"""
import sys
import os
sys.path.insert(0, '/app')

# Set up Flask app context
os.environ.setdefault('FLASK_APP', 'app')

from app import create_app
from app.services.telegram_auth import TelegramAuthService
import time

app = create_app()

with app.app_context():
    print("=" * 60)
    print("Telegram Auth Debug Tool")
    print("=" * 60)
    print(f"\nBot Token: {app.config.get('TELEGRAM_BOT_TOKEN', '')[:20]}...")
    print(f"Current time: {int(time.time())}")
    print("\nPaste initData to test:")
    
    init_data = input().strip()
    
    if not init_data:
        print("No initData provided")
        sys.exit(1)
    
    print(f"\nTesting initData (length: {len(init_data)})...")
    is_valid, user_data = TelegramAuthService.verify_init_data(init_data)
    
    print(f"\nResult: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if user_data:
        print(f"User data: {user_data}")
    else:
        print("No user data returned")
