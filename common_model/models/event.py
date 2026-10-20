from dataclasses import asdict, dataclass, field
from typing import Any, Dict
import json

from common_model.models.event_type import EventType


@dataclass
class Event:

    timestamp: float
    event_id: int
    event_type: EventType
    workstation_id: str
    job_id: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    simulation_id: str = "default"

    @property
    def worker_id(self) -> str | None:
    
        worker_id = self.metadata.get("worker_id")

        if worker_id is None:
            return None

        return str(worker_id)

    def to_dict(self) -> Dict[str, Any]:
        
        data = asdict(self)
        data["event_type"] = self.event_type.value
        return data

    def to_json(self) -> str:
        
        return json.dumps(
            self.to_dict(),
            indent=4,
        )

    def __str__(self) -> str:
        
        worker_text = ""

        if self.worker_id is not None:
            worker_text = f" Worker={self.worker_id}"

        return (
            f"[{self.timestamp:8.2f}] "
            f"{self.event_type.value:<24} "
            f"Simulation={self.simulation_id:<10} "
            f"Machine={self.workstation_id:<6} "
            f"Job={self.job_id}"
            f"{worker_text}"
        )