from __future__ import annotations

import os
import tempfile
from importlib import reload
from pathlib import Path

from fastapi.testclient import TestClient


def test_ingest_and_chat_end_to_end():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        data_dir = tmp / "data" / "raw"
        models_dir = tmp / "models"
        data_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        (data_dir / "doc.txt").write_text(
            "Devoluciones: puedes solicitar devolución en 30 días.\n"
            "Facturación: si hay cargos duplicados, adjunta factura y capturas.\n",
            encoding="utf-8",
        )

        os.environ["DATA_DIR"] = str(data_dir)
        os.environ["MODELS_DIR"] = str(models_dir)
        os.environ["INDEX_PATH"] = str(models_dir / "rag_index.joblib")

        import app.main as main_mod

        reload(main_mod)

        with TestClient(main_mod.app) as client:
            r = client.post("/ingest")
            assert r.status_code == 200
            assert r.json()["n_chunks"] >= 1

            r2 = client.post(
                "/chat", json={"question": "¿Cuántos días tengo para devolver?"}
            )
            assert r2.status_code == 200
            out = r2.json()
            assert "Respuesta" in out["answer"]
            assert len(out["sources"]) >= 1
