"""
Shared library for the Claude memory system scripts.
"""
import json, os, urllib.request

MODEL = "gemini-embedding-001"
DB = os.path.expanduser("~/.claude/projects/-Volumes-Crucial-X10-assistant/memory/memory.db")

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def embed(text):
    api_key = get_api_key()
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:embedContent?key={api_key}"
    payload = json.dumps({
        "content": {"parts": [{"text": text}]}
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["embedding"]["values"]
    except Exception:
        return None
