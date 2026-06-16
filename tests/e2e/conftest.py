"""E2E fixtures: spin up the real app on a SQLite DB with mocked AI, then
drive it with Playwright. All tests here are marked ``e2e``.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER = PROJECT_ROOT / "tests" / "e2e" / "_server.py"


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_until_up(url: str, proc: subprocess.Popen, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited early (code {proc.returncode})")
        try:
            with urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("server did not become ready in time")


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("e2e") / "e2e.db"
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = dict(os.environ)
    # The app reads BASE_URL for QR/share links; keep it consistent.
    env["BASE_URL"] = base_url
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    proc = subprocess.Popen(
        [sys.executable, str(SERVER), str(db_path), str(port)],
        cwd=str(PROJECT_ROOT), env=env,
    )
    try:
        _wait_until_up(f"{base_url}/api/vendors", proc)
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def page(live_server, page):
    """Override pytest-playwright's page to point at the live server."""
    page.set_default_timeout(10_000)
    return page
