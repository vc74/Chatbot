#!/usr/bin/env python3
"""
Production ChatBot Server Runner
Simple script to start the production server with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        'flask', 'groq', 'flask-cors', 'flask-limiter', 
        'werkzeug', 'python-dotenv', 'gunicorn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("Install them with: pip install " + " ".join(missing))
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Create a .env file with your Groq API key:")
        print("GROQ_API_KEY=your_api_key_here")
        return False
    
    # Read .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    if 'GROQ_API_KEY' not in content:
        print("❌ GROQ_API_KEY not found in .env file!")
        print("Add your Groq API key to .env file:")
        print("GROQ_API_KEY=your_api_key_here")
        return False
    
    return True

def run_development_server():
    """Run the development server"""
    print("🚀 Starting ChatBot Development Server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run the server module directly
        os.environ['FLASK_ENV'] = 'development'
        subprocess.run([sys.executable, 'server.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def run_production_server():
    """Run the production server with Gunicorn"""
    print("🚀 Starting ChatBot Production Server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Use gunicorn for production
        cmd = [
            'gunicorn',
            '--bind', '0.0.0.0:5000',
            '--workers', '4',
            '--timeout', '120',
            '--keep-alive', '2',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--worker-class', 'sync',
            '--access-logfile', 'access.log',
            '--error-logfile', 'error.log',
            '--log-level', 'info',
            'server:app'
        ]
        
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except FileNotFoundError:
        print("❌ Gunicorn not found. Running development server instead...")
        run_development_server()
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("🤖 ChatBot Production Server")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check .env file
    if not check_env_file():
        sys.exit(1)
    
    # Get server mode from command line or ask user
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("\nSelect server mode:")
        print("1. Development (Flask dev server)")
        print("2. Production (Gunicorn)")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        mode = 'dev' if choice == '1' else 'prod'
    
    print(f"\n✅ All checks passed!")
    print(f"🎯 Starting in {'development' if mode == 'dev' else 'production'} mode...\n")
    
    if mode == 'dev' or mode == 'development':
        run_development_server()
    else:
        run_production_server()

if __name__ == "__main__":
    main()