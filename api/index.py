"""
Vercel serverless function entry point for FastAPI application.
This file is required for deploying FastAPI to Vercel.
"""
from mangum import Mangum
from app.main import app

# Mangum handler for AWS Lambda/Vercel
# lifespan="off" disables startup/shutdown events which aren't supported in serverless
handler = Mangum(app, lifespan="off")
