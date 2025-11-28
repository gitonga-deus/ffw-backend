"""
Vercel serverless function entry point for FastAPI application.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.main import app
    from mangum import Mangum
    
    # Create handler
    handler = Mangum(app, lifespan="off")
    
except Exception as e:
    print(f"Error initializing handler: {e}")
    import traceback
    traceback.print_exc()
    raise
