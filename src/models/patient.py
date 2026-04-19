from pydantic import BaseModel
from typing import List, Optional

from .variant import Variant


class Patient(BaseModel):
    patient_id: str
    variants: List[Variant] = []
    metadata: Optional[dict] = None
