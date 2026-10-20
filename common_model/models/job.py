from dataclasses import dataclass


@dataclass
class Job:


    job_id: int
    arrival_time: float

    def __str__(self) -> str:
        return (
            f"Job("
            f"ID={self.job_id}, "
            f"Arrival={self.arrival_time:.2f}"
            f")"
        )