import requests

job_id = "6983c61354698ebd5320af00"
url = f"http://localhost:8000/jobs/{job_id}/transcript"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjbGV5dXJ6YWl6QGdtYWlsLmNvbSIsImV4cCI6MTc3MDc2NzA4OH0.Y8Ec-iRX2DUbVOMqBV-eWfw-FfI5lvwEFSHb_bkN_sc"

headers = {
    "Authorization": f"Bearer {token}"
}

try:
    print(f"Requesting {url}...")
    res = requests.get(url, headers=headers)
    
    with open("response_dump.txt", "w", encoding="utf-8") as f:
        f.write(f"Status: {res.status_code}\n")
        f.write(f"Headers: {res.headers}\n")
        f.write(f"Body: {res.text[:1000]}\n")
        
        try:
            data = res.json()
            f.write(f"Parsed JSON Keys: {list(data.keys())}\n")
            if 'segments' in data:
                f.write(f"Segment count: {len(data['segments'])}\n")
        except Exception as e:
            f.write(f"JSON Parse Error: {e}\n")

except Exception as e:
    print(f"Request failed: {e}")
