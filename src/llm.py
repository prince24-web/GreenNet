import requests
import json

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:1.5b"
EMBED_MODEL = "nomic-embed-text"

# Tuned for CPU-only Pentium Silver hardware
_LLM_OPTIONS = {
    "temperature": 0.3,
    "num_ctx": 1024,       # Reduced from 2048 — smaller context = faster load
    "num_predict": 300,    # Reduced from 512 — enough for most farming answers
}


def chat(prompt: str, system: str = None) -> str:
    """Send a prompt to Qwen2.5 and return the response text."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "keep_alive": -1,   # Keep model loaded in RAM indefinitely — eliminates cold-start
        "options": _LLM_OPTIONS,
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        return "Error: Ollama is not running. Please start it with: ollama serve"
    except Exception as e:
        return f"Error: {str(e)}"


def embed(text: str) -> list[float]:
    """Get an embedding vector for a piece of text."""
    payload = {
        "model": EMBED_MODEL,
        "prompt": text,
        "keep_alive": -1,   # Keep embed model loaded too — eliminates its cold-start
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json=payload,
            timeout=60      # Embedding is fast — fail quickly if unavailable
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return []


def warmup() -> bool:
    """
    Pre-load both models into RAM on app startup.
    Called once in a background thread so the UI doesn't block.
    Returns True if both models warmed up successfully.
    """
    print("[warmup] Loading LLM into RAM...")
    try:
        requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
                "keep_alive": -1,
                "options": {"num_predict": 1, "num_ctx": 64},
            },
            timeout=120,
        )
        print("[warmup] LLM ready.")
    except Exception as e:
        print(f"[warmup] LLM warm-up failed: {e}")
        return False

    print("[warmup] Loading embed model into RAM...")
    try:
        requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": "warmup", "keep_alive": -1},
            timeout=60,
        )
        print("[warmup] Embed model ready.")
    except Exception as e:
        print(f"[warmup] Embed warm-up failed: {e}")
        # Non-fatal — RAG will fall back to empty results
    return True


def is_ollama_running() -> bool:
    """Quick health check before the app starts."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False