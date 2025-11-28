"""
Vercel serverless function entry point for FastAPI application.
This file is required for deploying FastAPI to Vercel.
"""
import sys
import os

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app first to ensure all modules are loaded
from app.main import app

# Import Mangum after app is loaded
from mangum import Mangum

# Mangum handler for AWS Lambda/Vercel
# lifespan="off" disables startup/shutdown events which aren't supported in serverless
# api_gateway_base_path="/" ensures proper routing
handler = Mangum(app, lifespan="off", api_gateway_base_path="/")
