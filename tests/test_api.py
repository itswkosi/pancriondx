import sys
import os

# ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_analyze_endpoint():
    payload = {
        "patient_id": "123",
        "variants": [
            {
                "gene": "BRCA1",
                "variant_id": "v1",
                "clinvar": "pathogenic",
                "impact": "missense",
                "allele_frequency": 0.0001,
            },
            {
                "gene": "FOO",
                "variant_id": "v2",
                "clinvar": "benign",
                "impact": "synonymous",
            },
        ],
    }
    res = client.post("/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == "123"
    assert "risk_score" in data
    # FOO should be filtered out
    assert all(v["gene"] == "BRCA1" for v in data["variants_analyzed"])
    assert data["risk_level"] in ["Low", "Moderate", "Elevated", "High"]
