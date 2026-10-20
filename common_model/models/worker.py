from dataclasses import dataclass


@dataclass(frozen=True)
class Worker:
    

    worker_id: str
    name: str

    def __str__(self) -> str:
        return (
            f"Worker("
            f"ID={self.worker_id}, "
            f"Name={self.name}"
            f")"
        )