import os
import sys

# Manually load .env from parent of backend or current dir
def load_env_manual():
    env_path = os.path.join(os.path.dirname(os.getcwd()), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.getcwd(), '.env')
        if not os.path.exists(env_path):
            return
            
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

load_env_manual()

try:
    import huggingface_hub
    from huggingface_hub import HfApi
except ImportError:
    print("CRITICAL: huggingface_hub not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
    from huggingface_hub import HfApi

token = os.getenv("HF_TOKEN")
print(f"Token found: {token[:4]}...{token[-4:] if token else 'None'}")

if not token:
    print("FATAL: No HF_TOKEN in environment.")
    exit(1)

try:
    print("Verifying token with Hugging Face API...")
    api = HfApi(token=token)
    user = api.whoami()
    print(f"Authenticated as: {user['name']} (Type: {user['type']})")
    
    models_to_check = [
        "pyannote/speaker-diarization-3.1",
        "pyannote/segmentation-3.0"
    ]
    
    for model in models_to_check:
        print(f"Checking access to '{model}'...")
        try:
            model_info = api.model_info(model)
            print(f"Success! Access to '{model}' confirmed.")
            
            if model_info.gated:
                print(f"Model '{model}' is GATED. (Access confirmed).")
                
        except Exception as e:
            print(f"FAILED to access model info for '{model}': {e}")
            print("Likely cause: Terms not accepted or invalid token.")

except Exception as e:
    print(f"Authentication Failed: {e}")
