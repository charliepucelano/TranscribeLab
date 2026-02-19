
import requests
import random
import string

BASE_URL = "http://localhost:8010"

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def run_test():
    email = f"test_{random_string()}@example.com"
    password = "password123"
    
    print(f"Testing with {email} / {password}")
    
    # 1. Register
    print("1. Registering...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password
        })
        print(f"Register Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Register Response: {resp.text}")
            return
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        return

    # 2. Login
    print("\n2. Logging in...")
    try:
        # FastAPI OAuth2PasswordRequestForm expects form data
        resp = requests.post(f"{BASE_URL}/auth/token", data={
            "username": email,
            "password": password
        })
        print(f"Login Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Login Response: {resp.text}")
            return
        
        token = resp.json()["access_token"]
        print("Login successful, token received.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # 3. Get User (Dashboard load)
    print("\n3. Getting User Profile (/auth/me)...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Get User Status: {resp.status_code}")
        print(f"Get User Response: {resp.text}")

        # 4. Get Jobs (Dashboard content)
        print("\n4. Getting Jobs (/jobs)...")
        resp = requests.get(f"{BASE_URL}/jobs", headers=headers)
        print(f"Get Jobs Status: {resp.status_code}")
        print(f"Get Jobs Response: {resp.text}")
        
    except Exception as e:
        print(f"Get User/Jobs failed: {e}")

if __name__ == "__main__":
    run_test()
