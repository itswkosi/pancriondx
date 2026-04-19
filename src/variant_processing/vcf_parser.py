from pathlib import Path
from typing import Dict, List, Optional

from ..models.variant import Variant


INFO_KEYS = {
    "gene": ("GENE",),
    "clinvar_classification": ("CLINVAR",),
    "predicted_impact": ("IMPACT",),
    "consequence": ("CSQ", "CONSEQUENCE"),
    "allele_frequency": ("AF",),
}


def _parse_info_field(info_field: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for part in info_field.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        values[key.upper()] = value
    return values


def _pick(info_map: Dict[str, str], *keys: str) -> Optional[str]:
    for key in keys:
        value = info_map.get(key)
        if value not in (None, ""):
            return value
    return None


def parse_vcf(file_path: str) -> List[Variant]:
    """Convert a VCF file path or VCF text into Variant objects.

    Supports a lightweight VCF representation where useful annotations are
    provided in the INFO column, e.g. `GENE`, `CLINVAR`, `IMPACT`, `AF`, and
    optionally `CSQ` or `CONSEQUENCE`.
    """
    path = Path(file_path)
    vcf_content = path.read_text() if path.exists() else file_path
    variants: List[Variant] = []

    for line in vcf_content.strip().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        columns = stripped.split("\t")
        if len(columns) < 6:
            continue

        chrom, pos, variant_id, ref, alt = columns[:5]
        info_field = columns[7] if len(columns) >= 8 else columns[5]
        info_map = _parse_info_field(info_field)

        allele_frequency_raw = _pick(info_map, *INFO_KEYS["allele_frequency"])
        try:
            allele_frequency = float(allele_frequency_raw) if allele_frequency_raw is not None else None
        except ValueError:
            allele_frequency = None

        gene = _pick(info_map, *INFO_KEYS["gene"])
        if not gene:
            continue

        normalized_variant_id = variant_id if variant_id not in ("", ".") else f"{chrom}:{pos}:{ref}:{alt}"

        variants.append(
            Variant(
                gene=gene,
                variant_id=normalized_variant_id,
                consequence=_pick(info_map, *INFO_KEYS["consequence"]),
                clinvar_classification=_pick(info_map, *INFO_KEYS["clinvar_classification"]),
                predicted_impact=_pick(info_map, *INFO_KEYS["predicted_impact"]),
                allele_frequency=allele_frequency,
            )
        )

    return variants
