"""
Shared library for the Claude memory system scripts.
"""
import json, os, urllib.request

MODEL = "gemini-embedding-001"

def _resolve_db():
    """Resolve the memory.db path. Priority: CLAUDE_MEMORY_DB env var > memory.db next to this file."""
    env = os.environ.get("CLAUDE_MEMORY_DB", "")
    if env:
        return os.path.expanduser(env)
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "memory.db")

DB = _resolve_db()

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    env_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".env")
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
