import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app as fastapi_app
from mangum import Mangum

# Create the handler
_handler = Mangum(fastapi_app, lifespan="off")

# Vercel's detection looks for these names
# Use a function wrapper to avoid the issubclass check
def handler(event, context):
    return _handler(event, context)

# Also export app for ASGI compatibility
app = fastapi_app
