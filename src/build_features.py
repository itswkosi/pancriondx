import json
from pathlib import Path

import pandas as pd

_PANEL_PATH = Path(__file__).parent / "data" / "gene_panel.json"


def _load_gene_panel() -> list:
    """Load gene symbols from gene_panel.json, preserving JSON order."""
    data = json.loads(_PANEL_PATH.read_text())
    return [g["gene_symbol"] for g in data["genes"]]


GENE_PANEL = _load_gene_panel()


def build_feature_matrix(patients):
    """
    Build a binary mutation feature matrix for PDAC patients.

    Args:
        patients (list[dict]): Each item must include:
            - "id" (str): patient identifier
            - "mutations" (list[str]): mutated gene symbols
            - "label" (int): binary class label (0 or 1)

    Returns:
        tuple[pd.DataFrame, pd.Series]:
            - X: DataFrame with rows=patients, columns=GENE_PANEL, values in {0,1}
            - y: Series of labels aligned to X rows

    Raises:
        ValueError: If input is empty or required keys are missing.
        TypeError: If patients is not a list.
    """
    if not isinstance(patients, list):
        raise TypeError("patients must be a list of dictionaries")
    if len(patients) == 0:
        raise ValueError("patients is empty")

    required_keys = {"id", "mutations", "label"}
    rows = []
    labels = []
    index_ids = []

    for i, patient in enumerate(patients):
        if not isinstance(patient, dict):
            raise ValueError(f"Patient at index {i} is not a dictionary")

        missing = required_keys - set(patient.keys())
        if missing:
            raise ValueError(
                f"Patient at index {i} is missing required keys: {sorted(missing)}"
            )

        pid = patient["id"]
        muts = patient["mutations"] or []
        label = patient["label"]

        if not isinstance(muts, list):
            raise ValueError(f"'mutations' for patient '{pid}' must be a list")

        mut_set = set(muts)

        row = {gene: int(gene in mut_set) for gene in GENE_PANEL}
        rows.append(row)
        labels.append(label)
        index_ids.append(pid)

    X = pd.DataFrame(rows, columns=GENE_PANEL, index=index_ids)
    X.index.name = "id"

    y = pd.Series(labels, index=index_ids, name="label")
    y.index.name = "id"

    return X, y


if __name__ == "__main__":
    sample_patients = [
        {"id": "P1", "mutations": ["KRAS", "TP53"], "label": 1},
        {"id": "P2", "mutations": ["KRAS"], "label": 0},
        {"id": "P3", "mutations": ["SMAD4", "ATM", "NOT_IN_PANEL"], "label": 1},
    ]

    X, y = build_feature_matrix(sample_patients)

    print("Feature matrix (X):")
    print(X)
    print("\nLabels (y):")
    print(y)