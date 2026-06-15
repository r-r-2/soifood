"""E2E conftest — boots uvicorn subprocess + provides a Playwright page fixture.

Each test module gets a fresh app instance (module-scoped) so DB state from one
test file doesn't leak into another. Within a module, tests share state.
"""

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_ready(url: str, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"server at {url} did not become ready in {timeout}s")


@pytest.fixture(scope="module")
def live_server():
    """Launch the app as a subprocess with a fresh SQLite tempfile."""
    port = _free_port()
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()

    env = os.environ.copy()
    env.update({
        "GEMINI_API_KEY": "test-key",
        "DATABASE_URL": f"sqlite:///{db_file.name}",
        "BASE_URL": f"http://127.0.0.1:{port}",
        "SOIFOOD_E2E_PORT": str(port),
        "PYTHONPATH": str(PROJECT_ROOT),
    })

    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).parent / "_app_for_e2e.py")],
        env=env,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_ready(f"{base_url}/", timeout=20.0)
    except Exception:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=5)
        raise RuntimeError(
            f"subprocess failed to start.\nstdout:\n{stdout.decode(errors='replace')}\n"
            f"stderr:\n{stderr.decode(errors='replace')}"
        )

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    try:
        os.unlink(db_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def page_mobile(live_server, browser):
    """Playwright page on a mobile viewport — soifood is mobile-first."""
    context = browser.new_context(
        viewport={"width": 390, "height": 844},  # iPhone 14
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
    )
    page = context.new_page()
    yield page
    context.close()
