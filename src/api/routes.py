from fastapi import APIRouter, HTTPException
from typing import List, Any
from pathlib import Path

from ..models.patient import Patient
from ..data.gene_panel_loader import GenePanelLoader
from ..scoring.mutation_weight import MutationWeightCalculator
from ..variant_processing.variant_processor import VariantProcessor
from ..scoring.risk_engine import RiskEngine
from ..interpretation.report_generator import generate_interpretation

router = APIRouter()


@router.post("/analyze")
def analyze(patient: Patient):
    if not patient.variants:
        raise HTTPException(status_code=400, detail="No variants provided")

    # load gene panel
    panel_path = Path(__file__).parent.parent / "data" / "gene_panel.json"
    loader = GenePanelLoader(panel_path)
    panel_map = loader.as_dict()
    # convert Gene objects to dicts for easier downstream use
    panel_map = {k: v.model_dump() for k, v in panel_map.items()}

    # set up processors
    weight_calc = MutationWeightCalculator(panel_map)
    variant_proc = VariantProcessor(loader, weight_calc)

    # parse & annotate input variants (they may already be Variant models)
    raw_input = [v.model_dump() if hasattr(v, 'model_dump') else v for v in patient.variants]
    annotated = variant_proc.process(raw_input)

    # compute risk
    engine = RiskEngine(panel_map)
    result = engine.calculate(patient.patient_id, annotated)

    # prepare disease mapping
    gene_diseases = {g: panel_map[g].get("disease_association") for g in panel_map}

    report_json, narrative = generate_interpretation(
        result["normalized"], result["variant_contributions"], gene_diseases, result["risk_level"]
    )

    return {
        "patient_id": patient.patient_id,
        "risk_score": result["score"],
        "risk_level": result["risk_level"],
        "report": report_json,
        "report_text": narrative,
        "variants_analyzed": [v.model_dump() for v in annotated],
    }
