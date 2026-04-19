import sys
import os

# ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.interpretation.report_generator import generate_interpretation


def test_generate_interpretation():
    normalized = 2.3
    risk_level = "Elevated"
    contributions = [
        {"variant_id": "v1", "gene": "BRCA1", "score": 5.0},
        {"variant_id": "v2", "gene": "TP53", "score": 0.2},
    ]
    gene_diseases = {"BRCA1": "Hereditary breast and ovarian cancer", "TP53": "Li-Fraumeni"}
    json_report, narrative = generate_interpretation(normalized, contributions, gene_diseases, risk_level)
    assert json_report["risk_level"] == risk_level
    assert "Hereditary breast" in json_report["associated_diseases"][0]
    assert "Elevated genomic risk detected" in narrative
    assert "pathogenic BRCA1 variant" in narrative
