"""
Shared library for the agent-memory system.
"""
import json, os, urllib.request

MODEL = "gemini-embedding-2-preview"
EMBED_DIMENSIONS = 768
DATA_DIR = os.path.expanduser(os.environ.get("AGENT_MEMORY_DIR", "~/.agent-memory"))

def _resolve_db():
    """Resolve the memory.db path. Priority: AGENT_MEMORY_DIR env var > ~/.agent-memory/"""
    return os.path.join(DATA_DIR, "memory.db")

DB = _resolve_db()

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    # Check .env in the data directory (~/.agent-memory/.env)
    env_file = os.path.join(DATA_DIR, ".env")
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
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": EMBED_DIMENSIONS,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["embedding"]["values"]
    except Exception:
        return None
