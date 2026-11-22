"""Lightweight health check endpoint and server for GameTracker.

Provides:
- Standalone HTTP health server for container/server deployments.
- Starlette ASGI route patcher for Streamlit's web engine.
- Streamlit query parameter handler (?health=1) for Streamlit Community Cloud.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional

logger = logging.getLogger(__name__)

SERVICE_NAME = "GameTracker"
VERSION = "1.0.0"


def get_health_status() -> dict[str, str]:
    """Generate the standardized health check payload.

    Expected response:
    {
        "status": "healthy",
        "service": "GameTracker",
        "timestamp": "...",
        "version": "..."
    }
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": VERSION,
    }


class HealthHandler(BaseHTTPRequestHandler):
    """Minimal, fast HTTP request handler for health checks and WhatsApp webhooks."""

    def do_GET(self) -> None:
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        if path in ("", "/health", "/healthz", "/status", "/_stcore/healthz"):
            self._send_health(200)
        elif path in ("/whatsapp/webhook", "/webhook/whatsapp"):
            from whatsapp_bot import verify_webhook_subscription
            status_code, body = verify_webhook_subscription(query)
            payload = body.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self._send_json(404, {"error": "not_found", "message": "Endpoint not recognized"})

    def do_POST(self) -> None:
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("/whatsapp/webhook", "/webhook/whatsapp"):
            from whatsapp_bot import process_webhook_payload
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            sig_header = self.headers.get("X-Hub-Signature-256", "")

            status_code, resp_data = process_webhook_payload(body_bytes, sig_header)
            self._send_json(status_code, resp_data)
        else:
            self._send_json(404, {"error": "not_found", "message": "Endpoint not recognized"})

    def do_HEAD(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        if path in ("", "/health", "/healthz", "/status", "/_stcore/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def _send_health(self, status_code: int = 200) -> None:
        data = get_health_status()
        self._send_json(status_code, data)

    def _send_json(self, status_code: int, data: dict[str, Any]) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard HTTP access logs
        pass


_server_instance: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None


def start_health_server(port: int = 8080, host: str = "0.0.0.0") -> bool:
    """Start the lightweight background health server in a daemon thread."""
    global _server_instance, _server_thread

    if _server_instance is not None:
        logger.debug("Health server already running")
        return True

    try:
        server = HTTPServer((host, port), HealthHandler)
        _server_instance = server

        thread = threading.Thread(target=server.serve_forever, daemon=True, name="health-check-server")
        _server_thread = thread
        thread.start()
        logger.info("Health check server running on http://%s:%d/health", host, port)
        return True
    except OSError as e:
        logger.warning("Could not bind health check server on %s:%d: %s", host, port, e)
        return False
    except Exception as e:
        logger.warning("Failed to start health server: %s", e)
        return False


def stop_health_server() -> None:
    """Stop the background health server if running."""
    global _server_instance, _server_thread
    if _server_instance:
        try:
            _server_instance.shutdown()
            _server_instance.server_close()
        except Exception:
            pass
        _server_instance = None
        _server_thread = None


def patch_starlette_health_routes() -> bool:
    """Attempt to register /health directly onto Streamlit's internal Starlette ASGI server."""
    try:
        import streamlit.web.server.starlette.starlette_routes as sr
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        orig_create_health = getattr(sr, "create_health_routes", None)
        if not orig_create_health or getattr(sr, "_health_patched", False):
            return True

        def patched_create_health(runtime: Any, base_url: str | None) -> list[Any]:
            routes = orig_create_health(runtime, base_url)

            async def _custom_health(request: Any) -> JSONResponse:
                resp = JSONResponse(get_health_status())
                resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                resp.headers["Access-Control-Allow-Origin"] = "*"
                return resp

            async def _whatsapp_webhook_endpoint(request: Any) -> Any:
                from starlette.responses import PlainTextResponse, JSONResponse
                from whatsapp_bot import verify_webhook_subscription, process_webhook_payload

                if request.method == "GET":
                    status_code, body = verify_webhook_subscription(dict(request.query_params))
                    return PlainTextResponse(body, status_code=status_code)
                elif request.method == "POST":
                    body_bytes = await request.body()
                    sig_header = request.headers.get("x-hub-signature-256", "")
                    status_code, resp_data = process_webhook_payload(body_bytes, sig_header)
                    return JSONResponse(resp_data, status_code=status_code)
                return PlainTextResponse("Method Not Allowed", status_code=405)

            routes.append(Route("/health", _custom_health, methods=["GET", "HEAD"]))
            routes.append(Route("/_stcore/healthz", _custom_health, methods=["GET", "HEAD"]))
            routes.append(Route("/whatsapp/webhook", _whatsapp_webhook_endpoint, methods=["GET", "POST", "HEAD"]))
            routes.append(Route("/webhook/whatsapp", _whatsapp_webhook_endpoint, methods=["GET", "POST", "HEAD"]))
            return routes

        sr.create_health_routes = patched_create_health
        sr._health_patched = True
        logger.info("Patched Streamlit Starlette routes with /health JSON endpoint")
        return True
    except Exception as e:
        logger.debug("Could not patch Starlette routes (not available or non-Starlette environment): %s", e)
        return False


def handle_streamlit_query_health() -> bool:
    """Handle ?health=true or ?endpoint=health directly inside Streamlit without loading games.

    Returns True if health check was handled and script should stop.
    """
    try:
        import streamlit as st
        params = st.query_params
        if params.get("health") in ("1", "true", "yes", "") or params.get("endpoint") == "health" or params.get("check") == "health":
            st.json(get_health_status())
            st.stop()
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GameTracker Health Check")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the health server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind")
    args = parser.parse_args()

    print(json.dumps(get_health_status(), indent=2))
    print(f"\nStarting HTTP health server on http://{args.host}:{args.port}/health ...")
    server = HTTPServer((args.host, args.port), HealthHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping health server.")
        server.server_close()
