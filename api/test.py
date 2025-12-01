"""Test if imports work"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    print("Importing app.main...")
    from app.main import app
    print(f"Success! App: {app}")
    print(f"App type: {type(app)}")
    
    print("\nImporting Mangum...")
    from mangum import Mangum
    print(f"Success! Mangum: {Mangum}")
    
    print("\nCreating handler...")
    handler = Mangum(app, lifespan="off")
    print(f"Success! Handler: {handler}")
    print(f"Handler type: {type(handler)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
