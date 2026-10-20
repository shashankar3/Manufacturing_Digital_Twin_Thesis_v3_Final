from common_model.models.machine_state import MachineState
from common_model.models.state_transitions import StateTransitions
from system_b.models.operational_state import OperationalState


class StateSynchronizer:

    def __init__(self, operational_state: OperationalState):
        self.state = operational_state

        self.pre_failure_state = None

    def _transition_to(self, next_state: MachineState) -> None:
        
        current_state = self.state.machine_state

        if current_state == next_state:
            return

        StateTransitions.validate(current_state, next_state)
        self.state.machine_state = next_state

    def synchronize(self, event):

        event_type = event.event_type.name
        timestamp = event.timestamp

        
        # Update Simulation Clock
       

        self.state.simulation_time = timestamp

       
        # Job Arrival
       

        if event_type == "JOB_ARRIVAL":

            self.state.queue_length += 1

       
        # Job Start
        

        elif event_type == "JOB_START":

            if self.state.queue_length > 0:
                self.state.queue_length -= 1

            self._transition_to(MachineState.PROCESSING)

            self.state.current_job_id = event.job_id

        
        # Setup Started
        

        elif event_type == "SETUP_STARTED":

            self._transition_to(MachineState.SETUP)

            self.state.current_job_id = event.job_id

        
        # Setup Completed
        

        elif event_type == "SETUP_COMPLETED":

            if event.job_id is not None:
                self.state.current_job_id = event.job_id

       
        # Machine Cycle Started
        

        elif event_type == "MACHINE_CYCLE_STARTED":

            self._transition_to(MachineState.PROCESSING)

            if event.job_id is not None:
                self.state.current_job_id = event.job_id

       
        # Machine Cycle Completed
        
        

        elif event_type == "MACHINE_CYCLE_COMPLETED":

            if event.job_id is not None:
                self.state.current_job_id = event.job_id

        
        # Failure Detected
       

        elif event_type == "FAILURE_DETECTED":

            
            self.pre_failure_state = self.state.machine_state

            self._transition_to(MachineState.FAULTED)

            self.state.machine_failed = True

            if event.job_id is not None:
                self.state.current_job_id = event.job_id

       
        # Repair Started
      

        elif event_type == "REPAIR_STARTED":

            self._transition_to(MachineState.REPAIR)

            self.state.machine_failed = True

            if event.job_id is not None:
                self.state.current_job_id = event.job_id

        # Repair Completed
        

        elif event_type == "REPAIR_COMPLETED":

            self.state.machine_failed = False

            if self.pre_failure_state is not None:
                self._transition_to(self.pre_failure_state)
                self.pre_failure_state = None

            if event.job_id is not None:
                self.state.current_job_id = event.job_id

        # Job Completed
       

        elif event_type == "JOB_COMPLETED":

            self._transition_to(MachineState.IDLE)

            self.state.current_job_id = None


        # Worker Changed
        
      

        elif event_type == "WORKER_CHANGED":

            if getattr(event, "worker_id", None) is not None:
                self.state.current_worker_id = event.worker_id