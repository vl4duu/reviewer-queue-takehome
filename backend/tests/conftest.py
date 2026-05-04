import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import SEED_PATH, app  # noqa: E402
from app.store import store  # noqa: E402


@pytest.fixture
def client():
    store.load_seed(SEED_PATH)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fresh_store():
    store.load_seed(SEED_PATH)
    return store
