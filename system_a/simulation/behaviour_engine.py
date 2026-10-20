import math
import random


class BehaviourEngine:
    

    def __init__(
        self,
        processing_time_mean: float = 10.0,
        processing_time_std: float = 1.0,
        drift_per_job: float = 0.2,

       
        # Failure behaviour
        

        failure_probability: float = 0.25,

        response_time_mean: float = 2.0,
        response_time_std: float = 0.4,

        repair_time_mean: float = 3.0,
        repair_time_std: float = 0.5,

        
        # Generated worker behaviour
        

        worker_profiles: dict[str, dict] | None = None,
    ):

       
        # Machine behaviour
       

        self.processing_time_mean = (
            processing_time_mean
        )

        self.processing_time_std = (
            processing_time_std
        )

        self.drift_per_job = drift_per_job

        # Number of completed jobs
        self.completed_jobs = 0

      
        # Failure behaviour
       

        self.failure_probability = (
            failure_probability
        )

        self.response_time_mean = (
            response_time_mean
        )

        self.response_time_std = (
            response_time_std
        )

        self.repair_time_mean = (
            repair_time_mean
        )

        self.repair_time_std = (
            repair_time_std
        )

        
        # Worker behaviour
        
        self.worker_profiles = (
            worker_profiles
            if worker_profiles is not None
            else {}
        )

    
    # Machine Processing Behaviour
   

    def sample_processing_time(self) -> float:
        

        current_mean = (
            self.processing_time_mean
            + self.completed_jobs
            * self.drift_per_job
        )

        sampled_time = random.gauss(
            current_mean,
            self.processing_time_std,
        )

        return max(
            0.1,
            sampled_time,
        )

   
    # Worker Behaviour
    

    def _get_worker_profile(
        self,
        worker_id: str,
    ) -> dict:
        

        if worker_id not in self.worker_profiles:
            raise KeyError(
                f"No behavioural profile exists for worker "
                f"'{worker_id}'."
            )

        return self.worker_profiles[
            worker_id
        ]

   
    # Setup time
    

    def sample_setup_time(
        self,
        worker_id: str,
    ) -> float:
        

        profile = self._get_worker_profile(
            worker_id
        )

        sampled_time = random.gauss(
            profile["setup_mean"],
            profile["setup_std"],
        )

        return max(
            0.1,
            sampled_time,
        )

    
    # Worker processing contribution
    

    def sample_worker_processing_time(
        self,
        worker_id: str,
    ) -> float:
       

        profile = self._get_worker_profile(
            worker_id
        )

        sampled_time = random.gauss(
            profile[
                "worker_processing_mean"
            ],
            profile[
                "worker_processing_std"
            ],
        )

        return max(
            0.0,
            sampled_time,
        )

    
    # Worker repair response
   

    def sample_worker_repair_response_time(
        self,
        worker_id: str,
    ) -> float:
        

        profile = self._get_worker_profile(
            worker_id
        )

        sampled_time = random.gauss(
            profile[
                "repair_response_mean"
            ],
            profile[
                "repair_response_std"
            ],
        )

        return max(
            0.1,
            sampled_time,
        )

    
    # Failure Behaviour
    

    def should_fail(self) -> bool:
        

        return (
            random.random()
            < self.failure_probability
        )

    # -----------------------------------------------------

    def sample_idle_failure_wait_time(self) -> float:
        

        if self.failure_probability <= 0:
            return float("inf")

        if self.failure_probability >= 1:
            return 0.0

        reference_time = max(
            0.1,
            self.processing_time_mean,
        )

        # P(failure within reference_time) = p
        # => lambda = -ln(1-p) / reference_time
        hazard_rate = (
            -math.log(
                1.0 - self.failure_probability
            ) / reference_time
        )

        # Exponential time-to-failure.
        return random.expovariate(
            hazard_rate
        )

    # -----------------------------------------------------

    def sample_failure_time(
        self,
        processing_time: float,
    ) -> float:
        

        if processing_time <= 0:
            return 0.0

        if processing_time <= 0.2:
            return processing_time

        return random.uniform(
            0.1,
            processing_time - 0.1,
        )

    # -----------------------------------------------------

    def sample_response_time(self) -> float:
        

        sampled_time = random.gauss(
            self.response_time_mean,
            self.response_time_std,
        )

        return max(
            0.1,
            sampled_time,
        )

    # -----------------------------------------------------

    def sample_repair_time(
        self,
        worker_id: str,
    ) -> float:
       

        machine_repair_time = random.gauss(
            self.repair_time_mean,
            self.repair_time_std,
        )

        profile = self._get_worker_profile(
            worker_id
        )

        worker_repair_adjustment = random.gauss(
            profile[
                "repair_adjustment_mean"
            ],
            profile[
                "repair_adjustment_std"
            ],
        )

        sampled_time = (
            machine_repair_time
            + worker_repair_adjustment
        )

        return max(
            0.1,
            sampled_time,
        )

   
    # Job Completion
   

    def job_completed(self):
        

        self.completed_jobs += 1

   
    # Hidden State
    

    def get_hidden_state(self):
        

        return {
            "current_mean_processing_time": (
                self.processing_time_mean
                + self.completed_jobs
                * self.drift_per_job
            ),
            "completed_jobs": self.completed_jobs,
        }