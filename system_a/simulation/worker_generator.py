import random
from dataclasses import dataclass
from typing import Dict, List

from common_model.models.worker import Worker


@dataclass(frozen=True)
class WorkerGenerationParameters:


    number_of_workers: int = 5

    
    # Setup behaviour
    

    setup_time_range: tuple[float, float] = (1.2, 3.5)
    setup_std_range: tuple[float, float] = (0.15, 0.45)

    
    # Worker contribution to processing
    

    processing_contribution_range: tuple[float, float] = (
        0.25,
        1.10,
    )

    processing_contribution_std_range: tuple[float, float] = (
        0.05,
        0.15,
    )

    # Repair response
    

    repair_response_range: tuple[float, float] = (
        1.0,
        3.0,
    )

    repair_response_std_range: tuple[float, float] = (
        0.15,
        0.40,
    )


    # Repair contribution
   

    repair_adjustment_range: tuple[float, float] = (
        -0.5,
        1.0,
    )

    repair_adjustment_std_range: tuple[float, float] = (
        0.10,
        0.30,
    )

   
    # Worker tenure
    

    min_jobs_per_worker: int = 15
    max_jobs_per_worker: int = 30


class WorkerGenerator:
    

    def __init__(
        self,
        parameters: WorkerGenerationParameters | None = None,
        seed: int | None = None,
    ):

        self.parameters = (
            parameters
            if parameters is not None
            else WorkerGenerationParameters()
        )

        self.random = random.Random(seed)

        self.workers: List[Worker] = []

        self.worker_profiles: Dict[str, dict] = {}

        self._generate_workforce()

   
    # Workforce generation
    

    def _generate_workforce(self):
       

        for index in range(
            1,
            self.parameters.number_of_workers + 1,
        ):

            worker_id = f"W{index}"

            worker = Worker(
                worker_id=worker_id,
                name=f"Worker {index}",
            )

            self.workers.append(worker)

            self.worker_profiles[worker_id] = (
                self._generate_worker_profile()
            )

   
    # Individual worker profile
    

    def _generate_worker_profile(self) -> dict:
        

        p = self.parameters
        rng = self.random

        setup_mean = rng.uniform(
            *p.setup_time_range
        )

        setup_std = rng.uniform(
            *p.setup_std_range
        )

        processing_mean = rng.uniform(
            *p.processing_contribution_range
        )

        processing_std = rng.uniform(
            *p.processing_contribution_std_range
        )

        repair_response_mean = rng.uniform(
            *p.repair_response_range
        )

        repair_response_std = rng.uniform(
            *p.repair_response_std_range
        )

        repair_adjustment_mean = rng.uniform(
            *p.repair_adjustment_range
        )

        repair_adjustment_std = rng.uniform(
            *p.repair_adjustment_std_range
        )

        return {
            "setup_mean": setup_mean,
            "setup_std": setup_std,

            "worker_processing_mean":
                processing_mean,

            "worker_processing_std":
                processing_std,

            "repair_response_mean":
                repair_response_mean,

            "repair_response_std":
                repair_response_std,

            "repair_adjustment_mean":
                repair_adjustment_mean,

            "repair_adjustment_std":
                repair_adjustment_std,
        }

    
    # Public interface
    

    def get_workers(self) -> List[Worker]:
        

        return list(self.workers)

    def get_worker_profiles(self) -> Dict[str, dict]:
       

        return {
            worker_id: profile.copy()
            for worker_id, profile
            in self.worker_profiles.items()
        }

    def get_worker_profile(
        self,
        worker_id: str,
    ) -> dict:
        

        if worker_id not in self.worker_profiles:
            raise KeyError(
                f"Unknown worker: {worker_id}"
            )

        return self.worker_profiles[
            worker_id
        ].copy()

    def sample_worker_job_limit(self) -> int:
        

        return self.random.randint(
            self.parameters.min_jobs_per_worker,
            self.parameters.max_jobs_per_worker,
        )