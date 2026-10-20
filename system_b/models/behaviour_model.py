from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class WorkerBehaviourModel:

    worker_id: str = ""

    
    # Setup Behaviour
    

    mean_setup_time: float = 0.0

    setup_std: float = 0.0

    setup_distribution: Any = None

    setup_best_fit: str = ""

    setup_ks_statistic: float = 0.0

    setup_p_value: float = 0.0

   
    # Processing Behaviour
    

    processing_mean: float = 0.0

    processing_std: float = 0.0

    processing_distribution: Any = None

    processing_best_fit: str = ""

    processing_ks_statistic: float = 0.0

    processing_p_value: float = 0.0

    
    # Fault Response Behaviour
    

    mean_fault_response_time: float = 0.0

    fault_response_std: float = 0.0

    fault_response_distribution: Any = None

    fault_response_best_fit: str = ""

    fault_response_ks_statistic: float = 0.0

    fault_response_p_value: float = 0.0

   
    # Repair Behaviour
    

    mean_repair_time: float = 0.0

    repair_std: float = 0.0

    repair_distribution: Any = None

    repair_best_fit: str = ""

    repair_ks_statistic: float = 0.0

    repair_p_value: float = 0.0

   
    # Worker Observation Information
    

    observed_setups: int = 0

    observed_processing_cycles: int = 0

    observed_fault_responses: int = 0

    observed_repairs: int = 0


@dataclass
class BehaviourModel:

   
    # Job Arrival Behaviour
  

    mean_interarrival_time: float = 0.0

    interarrival_std: float = 0.0

    interarrival_distribution: Any = None

   
    # Setup Behaviour
   

    mean_setup_time: float = 0.0

    setup_std: float = 0.0

    setup_distribution: Any = None

    
    # Idle Behaviour
   

    mean_idle_time: float = 0.0

    idle_std: float = 0.0

    idle_distribution: Any = None

   
    # Processing Behaviour
   

    processing_mean: float = 0.0

    processing_std: float = 0.0

    processing_distribution: Any = None

    
    # Queue / Waiting Behaviour
    

    mean_waiting_time: float = 0.0

    waiting_std: float = 0.0

    waiting_distribution: Any = None

    
    # Faulted Behaviour
    

    mean_fault_response_time: float = 0.0

    fault_response_std: float = 0.0

    fault_response_distribution: Any = None

    # Repair Behaviour
    

    mean_repair_time: float = 0.0

    repair_std: float = 0.0

    repair_distribution: Any = None

    
    # Failure Behaviour
    

    failure_probability: float = 0.0

    mean_time_between_failures: float = 0.0

    
    # Worker-Dependent Behaviour
    

    worker_behaviours: Dict[str, WorkerBehaviourModel] = field(
        default_factory=dict
    )

   
    # Behaviour Drift
  

    processing_drift: float = 0.0

    
    # Learning / Observation Information
    

    observed_jobs: int = 0

    observed_arrivals: int = 0

    observed_setups: int = 0

    observed_failures: int = 0

    observed_repairs: int = 0

    
    # Best Statistical Models
    

    interarrival_best_fit: str = ""

    setup_best_fit: str = ""

    idle_best_fit: str = ""

    processing_best_fit: str = ""

    waiting_best_fit: str = ""

    fault_response_best_fit: str = ""

    repair_best_fit: str = ""

    
    # Goodness-of-Fit Statistics
    

    interarrival_ks_statistic: float = 0.0

    interarrival_p_value: float = 0.0

    setup_ks_statistic: float = 0.0

    setup_p_value: float = 0.0

    idle_ks_statistic: float = 0.0

    idle_p_value: float = 0.0

    processing_ks_statistic: float = 0.0

    processing_p_value: float = 0.0

    waiting_ks_statistic: float = 0.0

    waiting_p_value: float = 0.0

    fault_response_ks_statistic: float = 0.0

    fault_response_p_value: float = 0.0

    repair_ks_statistic: float = 0.0

    repair_p_value: float = 0.0