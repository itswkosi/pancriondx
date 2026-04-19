import sys
import os

# ensure src importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from math import log
from src.models.variant import Variant
from src.scoring.risk_engine import RiskEngine


def make_panel():
    return {
        "BRCA1": {
            "baseline_weight": 2.0,
            "pathogenicity_multiplier": {"pathogenic": 5.0, "benign": 0},
        },
        "TP53": {
            "baseline_weight": 1.5,
            "pathogenicity_multiplier": {"pathogenic": 4.0},
        },
    }


def test_no_variants():
    engine = RiskEngine(make_panel())
    result = engine.calculate("patient1", [])
    assert result["score"] == 0
    assert result["normalized"] == log(1)
    assert result["risk_level"] == "Low"
    assert result["variant_contributions"] == []


def test_single_variant_low():
    engine = RiskEngine(make_panel())
    var = Variant(gene="BRCA1", variant_id="v1", consequence="synonymous", clinvar_classification="pathogenic")
    result = engine.calculate("p2", [var])
    # compute expected
    expected_score = 2.0 * 5.0 * 0.5
    assert result["score"] == expected_score
    assert result["normalized"] == log(1 + expected_score)
    # normalized log(1+5) ~1.79 → Moderate category
    assert result["risk_level"] == "Moderate"


def test_thresholds():
    # create panels where a single variant can achieve a specific total
    for total, expected_level in [
        (0.5, "Low"),  # normalized ~0.405
        (1.8, "Moderate"),  # normalized ~1.029 >1
        (6.4, "Elevated"),  # normalized ~1.93 (still moderate) - adjust >2
        (7.4, "Elevated"),
        (19.1, "High"),  # normalized ~3.0+ → High
    ]:
        panel = {"TEST": {"baseline_weight": total, "pathogenicity_multiplier": {"pathogenic": 1}}}
        engine = RiskEngine(panel)
        var = Variant(gene="TEST", variant_id="x", consequence=None, clinvar_classification="pathogenic")
        res = engine.calculate("pid", [var])
        assert res["score"] == total
        assert res["risk_level"] == expected_level
