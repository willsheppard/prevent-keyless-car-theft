"""Build the static site and serve dist/ over HTTP for the e2e session -- the same
artifact the deploy workflow ships. The browser fixtures come from pytest-playwright;
this only stands up the server and points base_url at it."""
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PORT = 4173
BASE_URL = f"http://localhost:{PORT}"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


def _wait_for_port(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError(f"server did not come up on port {port}")


@pytest.fixture(scope="session", autouse=True)
def site_server():
    subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, check=True)
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "-d", "dist"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port(PORT)
        yield
    finally:
        proc.terminate()
        proc.wait()
