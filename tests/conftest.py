from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_MD = """\
# FAQ

## Returns Policy
You can request a return within 30 days of purchase.
Contact our support team at support@example.com to initiate the process.

## Billing
If you see duplicate charges on your account, please attach your invoice and
screenshots when contacting billing@example.com.

## Pricing Plans
We offer three plans: Basic (free), Pro ($29/month), and Enterprise (custom pricing).
Annual subscribers get a 20% discount on Pro and Enterprise plans.
"""


@pytest.fixture()
def tmp_data(tmp_path: Path) -> dict:
    data_dir = tmp_path / "data" / "raw"
    models_dir = tmp_path / "models"
    data_dir.mkdir(parents=True)
    models_dir.mkdir(parents=True)
    (data_dir / "faq.md").write_text(SAMPLE_MD, encoding="utf-8")
    return {"data_dir": data_dir, "models_dir": models_dir, "tmp_path": tmp_path}


@pytest.fixture()
def index_obj(tmp_data: dict) -> dict:
    from src.index import build_index

    return build_index(tmp_data["data_dir"])
