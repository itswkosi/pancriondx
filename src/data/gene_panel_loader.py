from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ValidationError

from ..models.gene import Gene


class GenePanel(BaseModel):
    genes: List[Gene]


class GenePanelLoader:
    def __init__(self, path: Path):
        self.path = path
        self.panel: Optional[GenePanel] = None
        self._load()

    def _load(self) -> None:
        """Load and validate the JSON file into a GenePanel object."""
        raw = Path(self.path).read_text()
        try:
            self.panel = GenePanel.model_validate_json(raw)
        except ValidationError as e:
            raise ValueError(f"Invalid gene panel format: {e}")

    def get_gene(self, symbol: str) -> Optional[Gene]:
        """Return the Gene object for the given symbol, or None if not present."""
        if not self.panel:
            return None
        for g in self.panel.genes:
            if g.gene_symbol.upper() == symbol.upper():
                return g
        return None

    def as_dict(self) -> Dict[str, Gene]:
        """Return panel entries keyed by uppercase gene_symbol."""
        if not self.panel:
            return {}
        return {g.gene_symbol.upper(): g for g in self.panel.genes}
