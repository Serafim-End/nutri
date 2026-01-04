#!/usr/bin/env python3
"""
Smoke Test Script
Quick verification that all bot dependencies are properly configured.

Usage:
    python scripts/smoke.py

Exit codes:
    0 - All checks passed
    1 - One or more checks failed

Environment variables checked:
    - TELEGRAM_BOT_TOKEN
    - BACKEND_URL
    - BOT_SERVICE_TOKEN
    - DATABASE_URL
    - WEBAPP_URL
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from bot directory or project root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try project root
    root_env = Path(__file__).parent.parent.parent.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SmokeTest:
    """Smoke test runner with detailed reporting."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []
    
    def check(self, name: str, passed: bool, message: str = "", warning: bool = False):
        """Record a test result."""
        if passed:
            self.passed += 1
            status = "✅ PASS"
        elif warning:
            self.warnings += 1
            status = "⚠️ WARN"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        self.results.append((status, name, message))
        print(f"  {status}: {name}")
        if message:
            print(f"         {message}")
    
    def section(self, name: str):
        """Print section header."""
        print(f"\n{'='*50}")
        print(f"  {name}")
        print(f"{'='*50}")
    
    def summary(self):
        """Print summary and return exit code."""
        print(f"\n{'='*50}")
        print(f"  SUMMARY")
        print(f"{'='*50}")
        print(f"  ✅ Passed:   {self.passed}")
        print(f"  ⚠️ Warnings: {self.warnings}")
        print(f"  ❌ Failed:   {self.failed}")
        print(f"{'='*50}")
        
        if self.failed > 0:
            print("\n❌ SMOKE TEST FAILED")
            return 1
        elif self.warnings > 0:
            print("\n⚠️ SMOKE TEST PASSED WITH WARNINGS")
            return 0
        else:
            print("\n✅ SMOKE TEST PASSED")
            return 0


async def run_smoke_tests():
    """Run all smoke tests."""
    test = SmokeTest()
    
    print("\n🔥 NutriMatch Bot Smoke Test")
    print(f"   Time: {datetime.now().isoformat()}")
    
    # =========================================
    # Environment Variables
    # =========================================
    test.section("Environment Variables")
    
    # Required variables
    required_vars = [
        ("TELEGRAM_BOT_TOKEN", "Telegram bot token"),
        ("BACKEND_URL", "Backend API URL"),
        ("BOT_SERVICE_TOKEN", "Service authentication token"),
        ("DATABASE_URL", "PostgreSQL connection string"),
    ]
    
    for var, desc in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if "TOKEN" in var or "PASSWORD" in var:
                display = value[:8] + "..." if len(value) > 8 else "***"
            elif "URL" in var:
                display = value[:50] + "..." if len(value) > 50 else value
            else:
                display = value[:30] + "..." if len(value) > 30 else value
            test.check(f"{var}", True, f"= {display}")
        else:
            test.check(f"{var}", False, f"MISSING - {desc}")
    
    # Optional variables
    optional_vars = [
        ("WEBAPP_URL", "Mini App URL"),
        ("BOT_DEBUG", "Debug mode"),
        ("LOG_LEVEL", "Log level"),
    ]
    
    for var, desc in optional_vars:
        value = os.environ.get(var)
        if value:
            test.check(f"{var} (optional)", True, f"= {value}")
        else:
            test.check(f"{var} (optional)", True, f"Not set - using default", warning=True)
    
    # =========================================
    # Backend Connectivity
    # =========================================
    test.section("Backend Connectivity")
    
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:5000")
    
    try:
        import aiohttp
        
        # Health check
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            try:
                async with session.get(f"{backend_url}/health/db") as response:
                    if response.status == 200:
                        data = await response.json()
                        test.check("Backend health (/health/db)", True, f"status={response.status}")
                    else:
                        test.check("Backend health (/health/db)", False, f"status={response.status}")
            except aiohttp.ClientError as e:
                test.check("Backend health (/health/db)", False, f"Connection error: {e}")
            
            # Service token auth
            service_token = os.environ.get("BOT_SERVICE_TOKEN", "")
            if service_token:
                try:
                    headers = {"X-Service-Token": service_token}
                    async with session.get(
                        f"{backend_url}/api/bot/resolve-telegram-user",
                        params={"telegram_user_id": 1},
                        headers=headers
                    ) as response:
                        if response.status in (200, 404):
                            test.check("Service token auth", True, f"status={response.status}")
                        elif response.status == 401:
                            test.check("Service token auth", False, "Invalid token")
                        else:
                            test.check("Service token auth", False, f"status={response.status}")
                except aiohttp.ClientError as e:
                    test.check("Service token auth", False, f"Connection error: {e}")
            else:
                test.check("Service token auth", False, "No token configured")
                
    except ImportError:
        test.check("aiohttp import", False, "aiohttp not installed")
    
    # =========================================
    # Database Connectivity
    # =========================================
    test.section("Database Connectivity")
    
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        try:
            import asyncpg
            
            # Parse URL
            db_url = database_url
            if "+psycopg2" in db_url:
                db_url = db_url.replace("+psycopg2", "")
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            
            try:
                conn = await asyncpg.connect(db_url, timeout=5)
                
                # Check bot_states table
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'bot_states'"
                )
                if result > 0:
                    test.check("bot_states table", True, "exists")
                else:
                    test.check("bot_states table", True, "will be created on first run", warning=True)
                
                # Check profiles table
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'profiles'"
                )
                if result > 0:
                    test.check("profiles table", True, "exists")
                else:
                    test.check("profiles table", False, "missing - run migrations")
                
                await conn.close()
                test.check("Database connection", True)
                
            except asyncpg.PostgresError as e:
                test.check("Database connection", False, str(e))
            except Exception as e:
                test.check("Database connection", False, str(e))
                
        except ImportError:
            test.check("asyncpg import", False, "asyncpg not installed")
    else:
        test.check("Database connection", False, "DATABASE_URL not set")
    
    # =========================================
    # Bot Token Validation
    # =========================================
    test.section("Telegram Bot Token")
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if bot_token:
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                try:
                    async with session.get(f"https://api.telegram.org/bot{bot_token}/getMe") as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("ok"):
                                bot_info = data.get("result", {})
                                test.check(
                                    "Bot token valid", 
                                    True, 
                                    f"@{bot_info.get('username')} (id={bot_info.get('id')})"
                                )
                            else:
                                test.check("Bot token valid", False, data.get("description", "Unknown error"))
                        elif response.status == 401:
                            test.check("Bot token valid", False, "Invalid token")
                        else:
                            test.check("Bot token valid", False, f"status={response.status}")
                except aiohttp.ClientError as e:
                    test.check("Bot token valid", False, f"Network error: {e}")
                    
        except ImportError:
            test.check("aiohttp import", False, "Cannot verify token")
    else:
        test.check("Bot token valid", False, "No token configured")
    
    # =========================================
    # Python Imports
    # =========================================
    test.section("Python Dependencies")
    
    required_imports = [
        ("aiogram", "Telegram bot framework"),
        ("aiohttp", "HTTP client"),
        ("asyncpg", "PostgreSQL driver"),
    ]
    
    for module, desc in required_imports:
        try:
            __import__(module)
            test.check(f"import {module}", True)
        except ImportError as e:
            test.check(f"import {module}", False, str(e))
    
    # Check aiogram version
    try:
        import aiogram
        version = aiogram.__version__
        if version.startswith("3."):
            test.check("aiogram version", True, f"v{version}")
        else:
            test.check("aiogram version", False, f"v{version} - requires v3.x")
    except Exception as e:
        test.check("aiogram version", False, str(e))
    
    # =========================================
    # Summary
    # =========================================
    return test.summary()


def main():
    """Entry point."""
    try:
        exit_code = asyncio.run(run_smoke_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Smoke test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Smoke test crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

