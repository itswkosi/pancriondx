from typing import List

from ..models.variant import Variant


def filter_panel_variants(variants: List[Variant], panel_genes: List[str]) -> List[Variant]:
    """Return only variants whose gene is in the provided panel list."""
    return [v for v in variants if v.gene in panel_genes]


def filter_by_af(variants: List[Variant], max_af: float) -> List[Variant]:
    """Remove variants with allele frequency above threshold."""
    return [v for v in variants if (v.allele_frequency is None or v.allele_frequency <= max_af)]
