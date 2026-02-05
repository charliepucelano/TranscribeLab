
import asyncio
from httpx import AsyncClient
from app.core.auth import create_access_token
from app.main import app

async def test_endpoint():
    token = create_access_token({"sub": "cleyurzaiz@gmail.com"})
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        print("Requesting /jobs/...")
        response = await ac.get("/jobs/", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_endpoint())
