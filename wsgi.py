"""
WSGI entry point for deployment
"""
from server import app

# This is the WSGI application for deployment
application = app

if __name__ == "__main__":
    app.run()
