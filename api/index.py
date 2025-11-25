"""
Vercel serverless function entry point for FastAPI application.
This file is required for deploying FastAPI to Vercel.
"""
import sys
import os

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
from app.main import app

# Mangum handler for AWS Lambda/Vercel
# lifespan="off" disables startup/shutdown events which aren't supported in serverless
handler = Mangum(app, lifespan="off")
