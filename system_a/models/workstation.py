import simpy

from common_model.models.event import Event
from common_model.models.event_type import EventType
from common_model.models.worker import Worker

from system_a.simulation.behaviour_engine import BehaviourEngine


class Workstation:


    def __init__(
        self,
        env: simpy.Environment,
        workstation_id: str,
        behaviour_engine: BehaviourEngine,
        workers: list[Worker],
        worker_job_limit_sampler,
        event_receiver=None,
    ):

        self.env = env

        self.workstation_id = (
            workstation_id
        )

        self.behaviour_engine = (
            behaviour_engine
        )

        # Optional connection to System B
        self.event_receiver = (
            event_receiver
        )

        # Function supplied by WorkerGenerator.
        
        self.worker_job_limit_sampler = (
            worker_job_limit_sampler
        )

        
        # Machine resource
        

        self.machine = simpy.Resource(
            env,
            capacity=1,
        )

        
        # Hidden machine operational state / idle-failure gate
        
        
        self.operational_gate = simpy.Resource(
            env,
            capacity=1,
        )

        self.machine_state = "IDLE"

        # Background hidden failure process. 
        self.idle_failure_process = env.process(
            self._idle_failure_process()
        )

       
        # Event management
        

        self.event_counter = 0

        self.event_log = []

       
        # Workers
        

        if not workers:
            raise ValueError(
                "Workstation requires at least "
                "one generated worker."
            )

        self.workers = list(workers)

        self.active_worker = None

        self.jobs_completed_by_worker = 0

        self.worker_job_limit = 0

        # Ground-truth diagnostic data.
       
        self.worker_change_log = []


        self.change_worker(
            initial=True
        )

   
    # Worker Management
    


    def _idle_failure_process(self):
       

        while True:
           
            wait_time = (
                self.behaviour_engine
                .sample_idle_failure_wait_time()
            )

            yield self.env.timeout(
                wait_time
            )

         
            if self.machine_state != "IDLE":
                continue

           
            with self.operational_gate.request() as gate_request:
                yield gate_request

                if self.machine_state != "IDLE":
                    continue

                self.machine_state = "FAULTED"

                
                worker_metadata = (
                    self.get_worker_metadata()
                )

                self.emit_event(
                    event_type=EventType.FAILURE_DETECTED,
                    job_id=None,
                    metadata=worker_metadata,
                )

               
                worker = self.active_worker

                if worker is not None:
                    response_time = (
                        self.behaviour_engine
                        .sample_worker_repair_response_time(
                            worker.worker_id
                        )
                    )
                else:
                    response_time = 0.0

                yield self.env.timeout(
                    response_time
                )

                self.emit_event(
                    event_type=EventType.REPAIR_STARTED,
                    job_id=None,
                    metadata=worker_metadata,
                )

                if worker is not None:
                    repair_time = (
                        self.behaviour_engine
                        .sample_repair_time(
                            worker.worker_id
                        )
                    )
                else:
                    repair_time = 0.0

                yield self.env.timeout(
                    repair_time
                )

                self.emit_event(
                    event_type=EventType.REPAIR_COMPLETED,
                    job_id=None,
                    metadata=worker_metadata,
                )

               
                self.machine_state = "IDLE"

    def change_worker(
        self,
        initial: bool = False,
    ):
        

        previous_worker = (
            self.active_worker
        )

        available_workers = [
            worker
            for worker in self.workers
            if (
                previous_worker is None
                or worker.worker_id
                != previous_worker.worker_id
            )
        ]

        if not available_workers:
            available_workers = self.workers

        
        import random

        self.active_worker = random.choice(
            available_workers
        )

        self.jobs_completed_by_worker = 0

        
        self.worker_job_limit = (
            self.worker_job_limit_sampler()
        )

        self.worker_change_log.append({
            "timestamp": self.env.now,
            "worker_id": (
                self.active_worker.worker_id
            ),
            "worker_name": (
                self.active_worker.name
            ),
            "worker_job_limit": (
                self.worker_job_limit
            ),
            "initial": initial,
        })

       
        # Emit worker change event
       

        self.emit_event(
            event_type=EventType.WORKER_CHANGED,
            job_id=-1,
            metadata={
                "worker_id":
                    self.active_worker.worker_id,

                "worker_name":
                    self.active_worker.name,

                "initial":
                    initial,
            },
        )

   
    # Event Emission
   

    def emit_event(
        self,
        event_type: EventType,
        job_id: int,
        metadata: dict = None,
    ):

        if metadata is None:
            metadata = {}

        self.event_counter += 1

        event = Event(
            timestamp=self.env.now,
            event_id=self.event_counter,
            event_type=event_type,
            workstation_id=self.workstation_id,
            job_id=job_id,
            metadata=metadata,
        )

        # Store locally
        self.event_log.append(event)

        # Send to Digital Twin
        if self.event_receiver is not None:
            self.event_receiver.receive(
                event
            )

        print(event)

    
    # Worker Metadata
    

    def get_worker_metadata(self):
       

        if self.active_worker is None:
            return {}

        return {
            "worker_id":
                self.active_worker.worker_id,

            "worker_name":
                self.active_worker.name,
        }

    
    # Job Processing
    

    def process_job(
        self,
        job,
    ):
        

        with self.machine.request() as request, \
             self.operational_gate.request() as operational_request:

        

            yield request
            yield operational_request

            
            self.machine_state = "SETUP"

          
            # Worker assigned to this job
          

            worker = self.active_worker

            worker_metadata = {
                "worker_id":
                    worker.worker_id,

                "worker_name":
                    worker.name,
            }

            
            # Setup
           

            self.emit_event(
                event_type=EventType.SETUP_STARTED,
                job_id=job.job_id,
                metadata=worker_metadata,
            )

            setup_time = (
                self.behaviour_engine
                .sample_setup_time(
                    worker.worker_id
                )
            )

           
            # Setup with possible machine failure
         
           
            if (
                self.behaviour_engine
                .should_fail()
            ):
                setup_failure_time = (
                    self.behaviour_engine
                    .sample_failure_time(
                        setup_time
                    )
                )

                remaining_setup = (
                    setup_time
                    - setup_failure_time
                )

                yield self.env.timeout(
                    setup_failure_time
                )

                self.machine_state = "FAULTED"

                self.emit_event(
                    event_type=EventType.FAILURE_DETECTED,
                    job_id=job.job_id,
                    metadata=worker_metadata,
                )

                response_time = (
                    self.behaviour_engine
                    .sample_worker_repair_response_time(
                        worker.worker_id
                    )
                )

                yield self.env.timeout(
                    response_time
                )

                self.emit_event(
                    event_type=EventType.REPAIR_STARTED,
                    job_id=job.job_id,
                    metadata=worker_metadata,
                )

                repair_time = (
                    self.behaviour_engine
                    .sample_repair_time(
                        worker.worker_id
                    )
                )

                yield self.env.timeout(
                    repair_time
                )

                self.emit_event(
                    event_type=EventType.REPAIR_COMPLETED,
                    job_id=job.job_id,
                    metadata=worker_metadata,
                )

                self.machine_state = "SETUP"

                # Resume the remaining setup work.
                yield self.env.timeout(
                    remaining_setup
                )

            else:
                yield self.env.timeout(
                    setup_time
                )

            self.emit_event(
                event_type=EventType.SETUP_COMPLETED,
                job_id=job.job_id,
                metadata=worker_metadata,
            )

            
            # Job Start
            

            self.machine_state = "PROCESSING"

            self.emit_event(
                event_type=EventType.JOB_START,
                job_id=job.job_id,
                metadata=worker_metadata,
            )

            # Machine cycle
            

            self.emit_event(
                event_type=(
                    EventType.MACHINE_CYCLE_STARTED
                ),
                job_id=job.job_id,
                metadata=worker_metadata,
            )

           
            # Machine processing time
         

            machine_processing_time = (
                self.behaviour_engine
                .sample_processing_time()
            )

          
            # Worker-dependent contribution
         

            worker_processing_time = (
                self.behaviour_engine
                .sample_worker_processing_time(
                    worker.worker_id
                )
            )

         
            # Total processing time
            

            total_processing_time = (
                machine_processing_time
                + worker_processing_time
            )

            
            # Hidden diagnostic state
           

            hidden_state = (
                self.behaviour_engine
                .get_hidden_state()
            )

            print(
                "Worker = "
                f"{worker.worker_id}"
            )

            print(
                "Hidden Machine Mean = "
                f"{hidden_state['current_mean_processing_time']:.2f} s"
            )

            print(
                "Machine Processing Time = "
                f"{machine_processing_time:.2f} s"
            )

            print(
                "Worker Contribution = "
                f"{worker_processing_time:.2f} s"
            )

            print(
                "Total Processing Time = "
                f"{total_processing_time:.2f} s"
            )

            
            # Failure Behaviour
          

            if (
                self.behaviour_engine
                .should_fail()
            ):

               
                # Determine failure time
               

                failure_time = (
                    self.behaviour_engine
                    .sample_failure_time(
                        total_processing_time
                    )
                )

                remaining_processing = (
                    total_processing_time
                    - failure_time
                )

               

                yield self.env.timeout(
                    failure_time
                )

            
                # Failure detected
               

                self.machine_state = "FAULTED"

                self.emit_event(
                    event_type=(
                        EventType.FAILURE_DETECTED
                    ),
                    job_id=job.job_id,
                    metadata=worker_metadata,
                )

                
                # Worker fault response
                

                response_time = (
                    self.behaviour_engine
                    .sample_worker_repair_response_time(
                        worker.worker_id
                    )
                )

                yield self.env.timeout(
                    response_time
                )

                
                # Repair starts
               

                self.emit_event(
                    event_type=(
                        EventType.REPAIR_STARTED
                    ),
                    job_id=job.job_id,
                    metadata=worker_metadata,
                )

              
                # Actual repair
               

                repair_time = (
                    self.behaviour_engine
                    .sample_repair_time(
                        worker.worker_id
                    )
                )

                yield self.env.timeout(
                    repair_time
                )

               
                # Repair completed
               

                self.emit_event(
                    event_type=(
                        EventType.REPAIR_COMPLETED
                    ),
                    job_id=job.job_id,
                    metadata=worker_metadata,
                )

                self.machine_state = "PROCESSING"

                
                # Resume remaining processing
              

                yield self.env.timeout(
                    remaining_processing
                )

            else:

               
                # Normal processing
                

                yield self.env.timeout(
                    total_processing_time
                )

            
            # Machine cycle completed
            

            self.emit_event(
                event_type=(
                    EventType.MACHINE_CYCLE_COMPLETED
                ),
                job_id=job.job_id,
                metadata=worker_metadata,
            )

            
            # Job completed
           

            self.emit_event(
                event_type=(
                    EventType.JOB_COMPLETED
                ),
                job_id=job.job_id,
                metadata=worker_metadata,
            )

        
            self.machine_state = "IDLE"

           
            # Update hidden machine behaviour
            

            self.behaviour_engine.job_completed()

         
            # Update worker job counter
            

            self.jobs_completed_by_worker += 1

            
            # Change worker when limit is reached
            

            if (
                self.jobs_completed_by_worker
                >= self.worker_job_limit
            ):
                self.change_worker()