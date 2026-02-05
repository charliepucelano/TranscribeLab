
import asyncio
from httpx import AsyncClient
from app.core.auth import create_access_token
from app.main import app
from app.core.database import db

async def debug_requests():
    # Force connection manually just in case lifespan didn't Trigger in this script context
    db.connect()
    
    token = create_access_token({"sub": "cleyurzaiz@gmail.com"})
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        print("\n--- TEST 1: GET /jobs/ (With Slash) ---")
        try:
            response = await ac.get("/jobs/", headers=headers, follow_redirects=False)
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response: {response.text}")
                if response.status_code == 307:
                    print(f"Location: {response.headers.get('location')}")
        except Exception as e:
            print(f"Error: {e}")

        print("\n--- TEST 2: GET /jobs (No Slash) ---")
        try:
            response = await ac.get("/jobs", headers=headers, follow_redirects=False)
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response: {response.text}")
                if response.status_code == 307:
                    print(f"Location: {response.headers.get('location')}")
        except Exception as e:
             print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_requests())
