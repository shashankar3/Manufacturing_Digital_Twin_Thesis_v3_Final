from dataclasses import dataclass, field
from typing import Optional

from common_model.models.machine_state import MachineState


@dataclass
class OperationalState:

    
    # Current Machine State
    

    machine_state: MachineState = field(
        default=MachineState.IDLE
    )

    
    # Current Active Job
    

    current_job_id: Optional[int] = None

   
    # Current Worker
    

    current_worker_id: Optional[str] = None

    
    # Queue
    

    queue_length: int = 0

   
    # Digital Twin Simulation Time
    

    simulation_time: float = 0.0

    
    # Machine Health
   

    machine_failed: bool = False

    
    # Reset
    

    def reset(self):
        

        self.machine_state = MachineState.IDLE

        self.current_job_id = None

        self.current_worker_id = None

        self.queue_length = 0

        self.simulation_time = 0.0

        self.machine_failed = False

    
    # Worker Update
   

    def set_worker(
        self,
        worker_id: Optional[str],
    ):
        

        if worker_id is None:
            self.current_worker_id = None
            return

        self.current_worker_id = str(worker_id)

    # =====================================================

    def get_worker(
        self,
    ) -> Optional[str]:
        

        return self.current_worker_id

    
    # String Representation
    

    def __str__(self):
        

        return (
            "\n========== Operational State ==========\n"
            f"Machine State  : {self.machine_state.value}\n"
            f"Current Job    : {self.current_job_id}\n"
            f"Current Worker : {self.current_worker_id}\n"
            f"Queue Length   : {self.queue_length}\n"
            f"Machine Failed : {self.machine_failed}\n"
            f"Simulation Time: {self.simulation_time:.2f}\n"
            "=======================================\n"
        )