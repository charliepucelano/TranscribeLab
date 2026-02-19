import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    import app
    print("Imported app")
except Exception as e:
    print(f"Failed to import app: {e}")

try:
    import app.core
    print("Imported app.core")
except Exception as e:
    print(f"Failed to import app.core: {e}")

try:
    import app.core.database
    print("Imported app.core.database")
except Exception as e:
    print(f"Failed to import app.core.database: {e}")
