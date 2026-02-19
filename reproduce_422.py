
import requests

BASE_URL = "http://localhost:8010"

def test_login_payloads():
    email = "test_user@example.com" # Doesn't matter if user exists for 422 check, 422 happens before auth logic often
    password = "password"

    print("--- Test 1: Sending JSON (Expect 422) ---")
    try:
        resp = requests.post(f"{BASE_URL}/auth/token", json={
            "username": email,
            "password": password
        })
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(e)

    print("\n--- Test 2: Sending FormData with correct headers (Expect 200 or 401) ---")
    try:
        resp = requests.post(f"{BASE_URL}/auth/token", data={
            "username": email,
            "password": password
        })
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(e)

    print("\n--- Test 3: Sending FormData BUT Content-Type=application/json (Expect 422) ---")
    try:
        # requests.post override headers
        resp = requests.post(
            f"{BASE_URL}/auth/token", 
            data={ "username": email, "password": password },
            headers={"Content-Type": "application/json"} 
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(e)
        
    print("\n--- Test 4: Sending FormData with manual multipart/form-data (Missing boundary) (Expect 422) ---")
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/token", 
            data={ "username": email, "password": password },
            headers={"Content-Type": "multipart/form-data"} 
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_login_payloads()
