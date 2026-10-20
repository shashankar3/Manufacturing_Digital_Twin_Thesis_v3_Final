from common_model.models.event_type import EventType


class FeatureExtractor:

    def __init__(self):

      
        # Temporary timestamps
       

        self.processing_start = {}

        self.waiting_start = {}

        self.setup_start = {}

        self.idle_start = None

        self.failure_detected = None

        self.repair_started = None

        self.last_job_arrival = None

    
        # Worker Context
       

        self.job_workers = {}

        self.failure_worker = None

        self.repair_worker = None
        

        # Time between consecutive JOB_ARRIVAL events.
        self.interarrival_times = []

        # Time between SETUP_STARTED and SETUP_COMPLETED.
        
        self.setup_times = []

        # Time between JOB_START and JOB_COMPLETED.
    
        self.processing_times = []

        # Time between JOB_ARRIVAL and JOB_START.
        self.waiting_times = []

        # Active IDLE residence time, excluding  FAULTED/REPAIR interruptions
    
        self.idle_times = []

        # Time between FAILURE_DETECTED and REPAIR_STARTED.
        
        self.fault_response_times = []

        # Time between REPAIR_STARTED and REPAIR_COMPLETED

        self.repair_times = []

        # Time between consecutive failures.
        self.time_between_failures = []

        # Actual failure timestamps.
        self.failure_timestamps = []

    
        # Worker-Conditioned Datasets
        

        self.worker_setup_times = {}

        self.worker_processing_times = {}

        self.worker_fault_response_times = {}

        self.worker_repair_times = {}

        
        # Worker Observation Counts
        

        self.worker_observation_counts = {}

        
        # State / event history
        

        self.state_transitions = []

        self.event_timestamps = []
        # Processing-clock bookkeeping. 
        self.processing_accumulated = {}
        self.processing_interval_start = {}
        self.processing_interrupted = set()

        # Setup-clock bookkeeping. 
        self.setup_accumulated = {}
        self.setup_interval_start = {}
        self.setup_interrupted = set()

        # Machine-level IDLE residence bookkeeping.
        self.idle_accumulated = 0.0
        self.idle_interval_start = None
        self.idle_interrupted = False


  
    # Worker Utility Methods
    

    @staticmethod
    def _get_worker_id(event):
        

        worker_id = getattr(
            event,
            "worker_id",
            None,
        )

        if worker_id is None:

            return None

        return str(worker_id)

    # =====================================================

    @staticmethod
    def _append_worker_observation(
        dataset,
        worker_id,
        value,
    ):
        

        if worker_id is None:

            return

        if value < 0.0:

            return

        if worker_id not in dataset:

            dataset[worker_id] = []

        dataset[worker_id].append(
            float(value)
        )

    # =====================================================

    def _record_worker_observation(
        self,
        dataset,
        worker_id,
        value,
        observation_type,
    ):
        

        if worker_id is None:

            return

        self._append_worker_observation(
            dataset,
            worker_id,
            value,
        )

        if worker_id not in self.worker_observation_counts:

            self.worker_observation_counts[
                worker_id
            ] = {}

        counts = self.worker_observation_counts[
            worker_id
        ]

        counts[observation_type] = (
            counts.get(
                observation_type,
                0,
            )
            + 1
        )

   
    # Observe Events
   

    def observe(self, event):
       

        event_type = event.event_type

        timestamp = float(
            event.timestamp
        )

        self.event_timestamps.append(
            timestamp
        )

        worker_id = self._get_worker_id(
            event
        )

      
        # Job Arrival
        

        if event_type == EventType.JOB_ARRIVAL:

           
            # Inter-arrival time
            

            if self.last_job_arrival is not None:

                interarrival_time = (
                    timestamp
                    - self.last_job_arrival
                )

                if interarrival_time >= 0.0:

                    self.interarrival_times.append(
                        interarrival_time
                    )

            self.last_job_arrival = timestamp

         
            # Waiting-time reference
          

            self.waiting_start[
                event.job_id
            ] = timestamp

        
        # Job Start
       

        elif event_type == EventType.JOB_START:

            # Processing residence starts 
        

            self.processing_accumulated[event.job_id] = 0.0
            self.processing_interval_start[event.job_id] = timestamp
            self.processing_interrupted.discard(event.job_id)

            
            # Store worker associated with this job
    

            if worker_id is not None:

                self.job_workers[
                    event.job_id
                ] = worker_id

            active_worker = (
                worker_id
                if worker_id is not None
                else self.job_workers.get(
                    event.job_id
                )
            )

            
            # Machine leaves IDLE
            

            if self.idle_interval_start is not None:

                self.idle_accumulated += (
                    timestamp
                    - self.idle_interval_start
                )

            idle_time = self.idle_accumulated

            if idle_time >= 0.0:

                self.idle_times.append(
                    idle_time
                )

            self.idle_start = None
            self.idle_accumulated = 0.0
            self.idle_interval_start = None
            self.idle_interrupted = False

            
            # Queue waiting ends
            

            if event.job_id in self.waiting_start:

                start = self.waiting_start.pop(
                    event.job_id
                )

                waiting_time = (
                    timestamp
                    - start
                )

                if waiting_time >= 0.0:

                    self.waiting_times.append(
                        waiting_time
                    )

           
            # Processing begins
           

            self.processing_start[
                event.job_id
            ] = timestamp

           
            # Preserve worker context
           

            if active_worker is not None:

                self.job_workers[
                    event.job_id
                ] = active_worker

        
        # Setup Started
       

        elif event_type == EventType.SETUP_STARTED:

            self.setup_start[
                event.job_id
            ] = timestamp

            self.setup_accumulated[
                event.job_id
            ] = 0.0

            self.setup_interval_start[
                event.job_id
            ] = timestamp

            self.setup_interrupted.discard(
                event.job_id
            )

           
            # Preserve worker context
            

            if worker_id is not None:

                self.job_workers[
                    event.job_id
                ] = worker_id

       
        # Setup Completed
       

        elif event_type == EventType.SETUP_COMPLETED:

            if event.job_id in self.setup_start:

                start = self.setup_start.pop(
                    event.job_id
                )

                if event.job_id in self.setup_interval_start:

                    setup_time = (
                        self.setup_accumulated.get(
                            event.job_id,
                            0.0,
                        )
                        + (
                            timestamp
                            - self.setup_interval_start[
                                event.job_id
                            ]
                        )
                    )

                else:

                    setup_time = self.setup_accumulated.get(
                        event.job_id,
                        0.0,
                    )

                self.setup_accumulated.pop(
                    event.job_id,
                    None,
                )

                self.setup_interval_start.pop(
                    event.job_id,
                    None,
                )

                self.setup_interrupted.discard(
                    event.job_id
                )

                if setup_time >= 0.0:

                    
                    # Existing global observation
                   

                    self.setup_times.append(
                        setup_time
                    )

                    
                    # Worker-conditioned observation
                   

                    active_worker = (
                        worker_id
                        if worker_id is not None
                        else self.job_workers.get(
                            event.job_id
                        )
                    )

                    self._record_worker_observation(
                        self.worker_setup_times,
                        active_worker,
                        setup_time,
                        "setup",
                    )

        # Job Completed
      

        elif event_type == EventType.JOB_COMPLETED:

           
            # Resolve worker before removing job context
          

            active_worker = (
                worker_id
                if worker_id is not None
                else self.job_workers.get(
                    event.job_id
                )
            )

            if event.job_id in self.processing_start:

                start = self.processing_start.pop(
                    event.job_id
                )

                if event.job_id in self.processing_interval_start:

                    processing_time = (
                        self.processing_accumulated.get(
                            event.job_id,
                            0.0,
                        )
                        + (
                            timestamp
                            - self.processing_interval_start[
                                event.job_id
                            ]
                        )
                    )

                else:

                    processing_time = self.processing_accumulated.get(
                        event.job_id,
                        0.0,
                    )

                self.processing_accumulated.pop(
                    event.job_id,
                    None,
                )

                self.processing_interval_start.pop(
                    event.job_id,
                    None,
                )

                self.processing_interrupted.discard(
                    event.job_id
                )

                if processing_time >= 0.0:

                    
                    # Existing global observation
                  

                    self.processing_times.append(
                        processing_time
                    )

        
                    # Worker-conditioned observation
                 

                    self._record_worker_observation(
                        self.worker_processing_times,
                        active_worker,
                        processing_time,
                        "processing",
                    )

            # Machine becomes idle
            

            self.idle_start = timestamp
            self.idle_accumulated = 0.0
            self.idle_interval_start = timestamp
            self.idle_interrupted = False

           
            # Job has completed, so its worker context is no longer required.        

            self.job_workers.pop(
                event.job_id,
                None,
            )

     
        # Failure Detected
           
            if event.job_id in self.processing_interval_start:
                _start = self.processing_interval_start.pop(event.job_id)
                self.processing_accumulated[event.job_id] = (
                    self.processing_accumulated.get(event.job_id, 0.0)
                    + (event.timestamp - _start)
                )
                self.processing_interrupted.add(event.job_id)
        elif event_type == EventType.FAILURE_DETECTED:

           
            # Pause state-residence clocks while faulted/repaired.
           

            if event.job_id in self.processing_interval_start:

                start = self.processing_interval_start.pop(
                    event.job_id
                )

                self.processing_accumulated[
                    event.job_id
                ] = (
                    self.processing_accumulated.get(
                        event.job_id,
                        0.0,
                    )
                    + (
                        timestamp
                        - start
                    )
                )

                self.processing_interrupted.add(
                    event.job_id
                )

            if event.job_id in self.setup_interval_start:

                start = self.setup_interval_start.pop(
                    event.job_id
                )

                self.setup_accumulated[
                    event.job_id
                ] = (
                    self.setup_accumulated.get(
                        event.job_id,
                        0.0,
                    )
                    + (
                        timestamp
                        - start
                    )
                )

                self.setup_interrupted.add(
                    event.job_id
                )

           
            if self.idle_interval_start is not None:

                self.idle_accumulated += (
                    timestamp
                    - self.idle_interval_start
                )

                self.idle_interval_start = None
                self.idle_interrupted = True

           
            # Time between failures
          

            if self.failure_timestamps:

                previous_failure = (
                    self.failure_timestamps[-1]
                )

                time_between_failures = (
                    timestamp
                    - previous_failure
                )

                if time_between_failures >= 0.0:

                    self.time_between_failures.append(
                        time_between_failures
                    )

            self.failure_timestamps.append(
                timestamp
            )

            self.failure_detected = timestamp

            # Preserving worker responsible for the active job
          

            active_worker = (
                worker_id
                if worker_id is not None
                else self.job_workers.get(
                    event.job_id
                )
            )

            self.failure_worker = (
                active_worker
            )

        # Repair Started
  

        elif event_type == EventType.REPAIR_STARTED:

            # Resolve worker context
         

            active_worker = (
                worker_id
                if worker_id is not None
                else self.failure_worker
            )

            # Fault-response time

            if self.failure_detected is not None:

                fault_response_time = (
                    timestamp
                    - self.failure_detected
                )

                if fault_response_time >= 0.0:

                    
                    # Existing global observation
                   

                    self.fault_response_times.append(
                        fault_response_time
                    )

                  
                    # Worker-conditioned observation
                   

                    self._record_worker_observation(
                        self.worker_fault_response_times,
                        active_worker,
                        fault_response_time,
                        "fault_response",
                    )

                self.failure_detected = None

            self.repair_started = timestamp

            self.repair_worker = (
                active_worker
            )

        # Repair Completed
       

        elif event_type == EventType.REPAIR_COMPLETED:

            # Resume the interrupted state-residence clock.
            

            if self.processing_interrupted:

                for job_id in list(
                    self.processing_interrupted
                ):

                    self.processing_interval_start[
                        job_id
                    ] = timestamp

                    self.processing_interrupted.discard(
                        job_id
                    )

            if self.setup_interrupted:

                for job_id in list(
                    self.setup_interrupted
                ):

                    self.setup_interval_start[
                        job_id
                    ] = timestamp

                    self.setup_interrupted.discard(
                        job_id
                    )

            if self.idle_interrupted:

                self.idle_interval_start = timestamp
                self.idle_interrupted = False

            
            # Resolve worker context
           

            active_worker = (
                worker_id
                if worker_id is not None
                else self.repair_worker
            )

           
            # Repair duration
            

            if self.repair_started is not None:

                repair_time = (
                    timestamp
                    - self.repair_started
                )

                if repair_time >= 0.0:

                    
                    # Existing global observation
                    

                    self.repair_times.append(
                        repair_time
                    )

                    
                    # Worker-conditioned observation
                    

                    self._record_worker_observation(
                        self.worker_repair_times,
                        active_worker,
                        repair_time,
                        "repair",
                    )

                self.repair_started = None

            self.repair_worker = None

   
    # State Transitions
    

    def add_state_transition(
        self,
        previous_state,
        current_state,
    ):
        

        self.state_transitions.append(
            (
                previous_state,
                current_state,
            )
        )

    # Worker Observation Accessors
   

    def get_worker_setup_times(
        self,
        worker_id=None,
    ):
        

        if worker_id is None:

            return self.worker_setup_times

        return self.worker_setup_times.get(
            str(worker_id),
            [],
        )

    # =====================================================

    def get_worker_processing_times(
        self,
        worker_id=None,
    ):
        

        if worker_id is None:

            return self.worker_processing_times

        return self.worker_processing_times.get(
            str(worker_id),
            [],
        )

    # =====================================================

    def get_worker_fault_response_times(
        self,
        worker_id=None,
    ):
        

        if worker_id is None:

            return self.worker_fault_response_times

        return self.worker_fault_response_times.get(
            str(worker_id),
            [],
        )

    # =====================================================

    def get_worker_repair_times(
        self,
        worker_id=None,
    ):
        

        if worker_id is None:

            return self.worker_repair_times

        return self.worker_repair_times.get(
            str(worker_id),
            [],
        )

    # =====================================================

    def get_worker_observation_counts(
        self,
        worker_id=None,
    ):
        

        if worker_id is None:

            return self.worker_observation_counts

        return self.worker_observation_counts.get(
            str(worker_id),
            {},
        )