"""
AgriSense — desktop app entry point.

Runs a native webview window (no browser, no Chrome overhead) and exposes
a JS-callable API that streams tokens from Ollama directly into the UI
as they're generated.

Memory footprint: ~80-150MB for the WebKitGTK window, vs 800MB-1.5GB
for a Chrome-based Gradio setup.
"""

import json
import threading
import webview
import requests

from src.orchestrator import build_prompt_context, SYSTEM_PROMPT
from src.llm import OLLAMA_BASE_URL, LLM_MODEL, is_ollama_running, warmup
from src.vision import classify_leaf_image_from_base64


class Api:
    """
    Exposed to JS as window.pywebview.api.*
    Every public method here is callable directly from app.js.
    """

    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    # ---------- Status check ----------

    def check_ollama_status(self):
        running = is_ollama_running()
        return {"running": running, "model": LLM_MODEL if running else None}

    # ---------- Main streaming entry point ----------

    def handle_query_stream(self, user_text: str, image_data_url: str | None):
        """
        Called from app.js. Runs orchestration (vision + RAG + DB lookups),
        then streams the LLM response token-by-token back into the UI via
        JS events. Runs in a background thread so the webview UI thread
        never blocks.
        """
        thread = threading.Thread(
            target=self._run_stream,
            args=(user_text, image_data_url),
            daemon=True,
        )
        thread.start()
        return {"started": True}

    def _run_stream(self, user_text: str, image_data_url: str | None):
        try:
            vision_tag = None
            vision_result = None

            # Run vision classification first if an image was attached
            if image_data_url:
                vision_result = classify_leaf_image_from_base64(image_data_url)
                if vision_result and vision_result.get("confidence", 0) > 0.3:
                    vision_tag = (
                        f"Detected: {vision_result['label']} "
                        f"({vision_result['confidence']:.0%} confidence)"
                    )

            # Build the full prompt using Phase 2-4 context (DB + RAG + vision)
            full_prompt = build_prompt_context(user_text, vision_result)

            # Signal the UI to swap skeleton -> live bubble
            self._emit("agrisense:stream_start", {"visionTag": vision_tag})

            # Stream directly from Ollama's /api/chat with stream=True
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt},
                ],
                "stream": True,
                "keep_alive": -1,       # Keep model in RAM — prevents cold-start
                "options": {
                    "temperature": 0.3,
                    "num_ctx": 1024,    # Reduced: faster context load on CPU
                    "num_predict": 300, # Reduced: enough for farming answers
                },
            }

            with requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                stream=True,
                timeout=180,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        self._emit("agrisense:stream_token", {"token": token})
                    if chunk.get("done"):
                        break

            self._emit("agrisense:stream_end", {})

        except requests.exceptions.ConnectionError:
            self._emit(
                "agrisense:stream_error",
                {"message": "Can't reach Ollama. Run 'ollama serve' in a terminal and try again."},
            )
        except Exception as e:
            self._emit("agrisense:stream_error", {"message": f"Error: {str(e)}"})

    def _emit(self, event_name: str, detail: dict):
        """Dispatch a CustomEvent in the webview's JS context."""
        if not self._window:
            return
        detail_json = json.dumps(detail)
        js = f"window.dispatchEvent(new CustomEvent('{event_name}', {{ detail: {detail_json} }}));"
        self._window.evaluate_js(js)


def main():
    # Pre-load both Ollama models in the background so they are warm
    # before the first user message arrives. This eliminates the 30-60s
    # cold-start delay on the very first query.
    warmup_thread = threading.Thread(target=warmup, daemon=True)
    warmup_thread.start()

    api = Api()
    window = webview.create_window(
        "GreenNet",
        "ui/Index.HTML",
        js_api=api,
        width=1180,
        height=760,
        min_size=(860, 560),
        background_color="#FAFAF7",
    )
    api.set_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()   