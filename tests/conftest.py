import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """A throwaway repo root with a copy of the real catalog, so tests never touch data/."""
    (tmp_path / "catalog").mkdir()
    shutil.copy(REPO / "catalog" / "sources.csv", tmp_path / "catalog" / "sources.csv")
    monkeypatch.setenv("MSR_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def fixture_text():
    return lambda name: (FIXTURES / name).read_text()
