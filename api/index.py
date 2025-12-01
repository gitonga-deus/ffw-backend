import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mangum import Mangum
from app.main import app

# Mangum handler for Vercel serverless
handler = Mangum(app, lifespan="off")
