from typing import Any, Dict
from system_b.models.behaviour_model import (
    BehaviourModel,
    WorkerBehaviourModel,
)

from system_b.prediction.markov_chain import MarkovChain

from system_b.estimation.feature_extractor import FeatureExtractor
from system_b.estimation.parameter_estimator import ParameterEstimator
from system_b.estimation.distribution_fitter import DistributionFitter
from system_b.estimation.goodness_of_fit import GoodnessOfFit

from system_b.adaptation.sliding_window import SlidingWindow


class BehaviourEstimator:

    

    MIN_SAMPLES_FOR_FIT = 20
   

    def __init__(
        self,
        window_size=20,
    ):

      
        # Behaviour Model
     

        self.model = BehaviourModel()

      
        # Statistical Learning Modules
       

        self.feature_extractor = FeatureExtractor()

        self.parameter_estimator = ParameterEstimator()

        self.distribution_fitter = DistributionFitter()

        self.goodness_of_fit = GoodnessOfFit()

       
        # Sliding Window
        

        self.sliding_window = SlidingWindow(
            window_size=window_size,
        )

       
        # Markov Chain
        

        self.markov_chain = MarkovChain()

        self.previous_state = None

        # Adaptation Statistics
        

        self.adaptation_count = 0

        # Stores the most recent adaptation request.

        self.last_adaptation = None

      
        # Worker-conditioned observations
       

        self.worker_setup_times = {}
        self.worker_processing_times = {}
        self.worker_fault_response_times = {}
        self.worker_repair_times = {}

        self.worker_setup_start = {}
        self.worker_processing_start = {}
        self.worker_processing_worker = {}

        self.worker_failure_detected = None
        self.worker_failure_worker = None

        self.worker_repair_start = None
        self.worker_repair_worker = None

        self.current_worker_id = None


    # Sliding Window Control
    

    def enable_sliding_window(
        self,
        window_size=None,
    ):

        self.sliding_window.enable(
            window_size=window_size,
        )

   

    def disable_sliding_window(
        self,
    ):
        

        self.sliding_window.disable()

    
    # Sample Selection
    

    def __get_learning_samples(
        self,
        samples,
    ):

        return self.sliding_window.select(
            samples
        )

  
    # Worker Observation Helpers
    

    @staticmethod
    def __event_worker_id(
        event,
    ):

        metadata = getattr(
            event,
            "metadata",
            None,
        )

        if isinstance(metadata, dict):

            worker_id = metadata.get(
                "worker_id"
            )

            if worker_id is not None:

                return str(worker_id)

        worker_id = getattr(
            event,
            "worker_id",
            None,
        )

        if worker_id is not None:

            return str(worker_id)

        return None

  

    def __get_worker_model(
        self,
        worker_id,
    ):
       

        if worker_id is None:

            return None

        worker_id = str(worker_id)

        if worker_id not in self.model.worker_behaviours:

            self.model.worker_behaviours[
                worker_id
            ] = WorkerBehaviourModel(
                worker_id=worker_id
            )

        return self.model.worker_behaviours[
            worker_id
        ]

    

    @staticmethod
    def __append_worker_sample(
        collection,
        worker_id,
        value,
    ):

        if worker_id is None:

            return

        try:

            value = float(value)

        except (
            TypeError,
            ValueError,
        ):

            return

        if value < 0.0:

            return

        worker_id = str(worker_id)

        if worker_id not in collection:

            collection[worker_id] = []

        collection[worker_id].append(value)

    

    @staticmethod
    def __calculate_std(
        samples,
    ):

        if len(samples) <= 1:

            return 0.0

        mean = (
            sum(samples)
            / len(samples)
        )

        variance = (
            sum(
                (sample - mean) ** 2
                for sample in samples
            )
            / (len(samples) - 1)
        )

        return variance ** 0.5

    

    def __observe_worker_context(
        self,
        event,
    ):

        event_type = getattr(
            event,
            "event_type",
            None,
        )

        event_type_name = getattr(
            event_type,
            "value",
            str(event_type),
        )

        timestamp = float(
            event.timestamp
        )

        worker_id = self.__event_worker_id(
            event
        )

       
        # Worker change
        

        if event_type_name == "WORKER_CHANGED":

            if worker_id is not None:

                self.current_worker_id = worker_id

            return


        if worker_id is None:

            worker_id = self.current_worker_id

        else:

            self.current_worker_id = worker_id

        
        # Setup
        

        if event_type_name in (
            "SETUP_STARTED",
            "SETUP_START",
        ):

            if worker_id is not None:

                self.worker_setup_start[
                    event.job_id
                ] = (
                    timestamp,
                    worker_id,
                )

            return

        if event_type_name in (
            "SETUP_COMPLETED",
            "SETUP_END",
        ):

            record = self.worker_setup_start.pop(
                event.job_id,
                None,
            )

            if record is not None:

                start, start_worker = record

                duration = timestamp - start

                self.__append_worker_sample(
                    self.worker_setup_times,
                    start_worker,
                    duration,
                )

            return

       
        # Processing
       

        if event_type_name == "JOB_START":

            if worker_id is not None:

                self.worker_processing_start[
                    event.job_id
                ] = timestamp

                self.worker_processing_worker[
                    event.job_id
                ] = worker_id

            return

        if event_type_name == "JOB_COMPLETED":

            start = self.worker_processing_start.pop(
                event.job_id,
                None,
            )

            start_worker = self.worker_processing_worker.pop(
                event.job_id,
                None,
            )

            if (
                start is not None
                and start_worker is not None
            ):

                duration = timestamp - start

                self.__append_worker_sample(
                    self.worker_processing_times,
                    start_worker,
                    duration,
                )

            return

     
        # Failure response
        

        if event_type_name in (
            "FAILURE_DETECTED",
            "FAILURE",
        ):

            self.worker_failure_detected = timestamp
            self.worker_failure_worker = worker_id

            return

        if event_type_name in (
            "REPAIR_STARTED",
            "RECOVERY",
        ):

            if self.worker_failure_detected is not None:

                duration = (
                    timestamp
                    - self.worker_failure_detected
                )

                response_worker = (
                    self.worker_failure_worker
                    if self.worker_failure_worker is not None
                    else worker_id
                )

                self.__append_worker_sample(
                    self.worker_fault_response_times,
                    response_worker,
                    duration,
                )

            self.worker_repair_start = timestamp

            self.worker_repair_worker = (
                worker_id
                if worker_id is not None
                else self.worker_failure_worker
            )

            self.worker_failure_detected = None
            self.worker_failure_worker = None

            return

        
        # Repair
        

        if event_type_name == "REPAIR_COMPLETED":

            if self.worker_repair_start is not None:

                duration = (
                    timestamp
                    - self.worker_repair_start
                )

                self.__append_worker_sample(
                    self.worker_repair_times,
                    self.worker_repair_worker,
                    duration,
                )

            self.worker_repair_start = None
            self.worker_repair_worker = None

    
    # Worker Behaviour Estimation
   

    def __learn_worker_behaviour(
        self,
    ):

        worker_ids = set()

        worker_ids.update(
            self.worker_setup_times.keys()
        )

        worker_ids.update(
            self.worker_processing_times.keys()
        )

        worker_ids.update(
            self.worker_fault_response_times.keys()
        )

        worker_ids.update(
            self.worker_repair_times.keys()
        )

        for worker_id in worker_ids:

            worker_model = self.__get_worker_model(
                worker_id
            )

           
            # Setup
            

            all_samples = self.worker_setup_times.get(
                worker_id,
                [],
            )

            samples = self.__get_learning_samples(
                all_samples
            )

            if len(samples) > 0:

                worker_model.mean_setup_time = (
                    sum(samples)
                    / len(samples)
                )

                worker_model.setup_std = (
                    self.__calculate_std(samples)
                )

                worker_model.observed_setups = (
                    len(all_samples)
                )

                best_fit = self.__fit_distribution(
                    samples
                )

                if best_fit is not None:

                    worker_model.setup_distribution = (
                        best_fit["distribution_object"]
                    )

                    worker_model.setup_best_fit = (
                        best_fit["distribution"]
                    )

                    worker_model.setup_ks_statistic = (
                        best_fit["ks_statistic"]
                    )

                    worker_model.setup_p_value = (
                        best_fit["p_value"]
                    )

          
            # Processing
            

            all_samples = self.worker_processing_times.get(
                worker_id,
                [],
            )

            samples = self.__get_learning_samples(
                all_samples
            )

            if len(samples) > 0:

                worker_model.processing_mean = (
                    sum(samples)
                    / len(samples)
                )

                worker_model.processing_std = (
                    self.__calculate_std(samples)
                )

                worker_model.observed_processing_cycles = (
                    len(all_samples)
                )

                best_fit = self.__fit_distribution(
                    samples
                )

                if best_fit is not None:

                    worker_model.processing_distribution = (
                        best_fit["distribution_object"]
                    )

                    worker_model.processing_best_fit = (
                        best_fit["distribution"]
                    )

                    worker_model.processing_ks_statistic = (
                        best_fit["ks_statistic"]
                    )

                    worker_model.processing_p_value = (
                        best_fit["p_value"]
                    )

           
            # Fault response
           

            all_samples = self.worker_fault_response_times.get(
                worker_id,
                [],
            )

            samples = self.__get_learning_samples(
                all_samples
            )

            if len(samples) > 0:

                worker_model.mean_fault_response_time = (
                    sum(samples)
                    / len(samples)
                )

                worker_model.fault_response_std = (
                    self.__calculate_std(samples)
                )

                worker_model.observed_fault_responses = (
                    len(all_samples)
                )

                best_fit = self.__fit_distribution(
                    samples
                )

                if best_fit is not None:

                    worker_model.fault_response_distribution = (
                        best_fit["distribution_object"]
                    )

                    worker_model.fault_response_best_fit = (
                        best_fit["distribution"]
                    )

                    worker_model.fault_response_ks_statistic = (
                        best_fit["ks_statistic"]
                    )

                    worker_model.fault_response_p_value = (
                        best_fit["p_value"]
                    )

            
            # Repair
           

            all_samples = self.worker_repair_times.get(
                worker_id,
                [],
            )

            samples = self.__get_learning_samples(
                all_samples
            )

            if len(samples) > 0:

                worker_model.mean_repair_time = (
                    sum(samples)
                    / len(samples)
                )

                worker_model.repair_std = (
                    self.__calculate_std(samples)
                )

                worker_model.observed_repairs = (
                    len(all_samples)
                )

                best_fit = self.__fit_distribution(
                    samples
                )

                if best_fit is not None:

                    worker_model.repair_distribution = (
                        best_fit["distribution_object"]
                    )

                    worker_model.repair_best_fit = (
                        best_fit["distribution"]
                    )

                    worker_model.repair_ks_statistic = (
                        best_fit["ks_statistic"]
                    )

                    worker_model.repair_p_value = (
                        best_fit["p_value"]
                    )

  
    # Observe Event Stream
   

    def observe(
        self,
        event,
    ):
       

        self.__observe_worker_context(
            event
        )

        self.feature_extractor.observe(
            event
        )

      
        # Incoming job behaviour
      

        self.__learn_interarrival()

        
        # Setup behaviour
      

        self.__learn_setup()

       
        # Existing behavioural components
       

        self.__learn_idle()

        self.__learn_processing()

        self.__learn_waiting()

        self.__learn_fault_response()

        self.__learn_repair()

        self.__learn_worker_behaviour()

    
    # Generic Distribution Learning
   

    def __fit_distribution(
        self,
        samples,
    ):
        

        if len(samples) < self.MIN_SAMPLES_FOR_FIT:

            return None

        estimates = (
            self.parameter_estimator.estimate(
                samples
            )
        )

        fitted = (
            self.distribution_fitter.fit(
                estimates
            )
        )

        return (
            self.goodness_of_fit.evaluate(
                samples,
                fitted,
            )
        )

  
    # Incoming Job / Inter-Arrival Behaviour
   

    def __learn_interarrival(
        self,
    ):

        all_samples = (
            self.feature_extractor.interarrival_times
        )

        if len(all_samples) == 0:

            return

        samples = (
            self.__get_learning_samples(
                all_samples
            )
        )

        if len(samples) == 0:

            return

      
        # Mean inter-arrival time
       

        self.model.mean_interarrival_time = (
            sum(samples) / len(samples)
        )

     
        # Standard deviation
        

        if len(samples) > 1:

            mean = (
                self.model.mean_interarrival_time
            )

            variance = (
                sum(
                    (sample - mean) ** 2
                    for sample in samples
                )
                / (len(samples) - 1)
            )

            self.model.interarrival_std = (
                variance ** 0.5
            )

        else:

            self.model.interarrival_std = 0.0

        
        # Total observed arrivals

        self.model.observed_arrivals = (
            len(all_samples) + 1
        )

       
        # Distribution fitting
        

        best_fit = (
            self.__fit_distribution(
                samples
            )
        )

        if best_fit is not None:

            self.model.interarrival_distribution = (
                best_fit
            )

   
    # Setup Behaviour
  

    def __learn_setup(
        self,
    ):

        all_samples = (
            self.feature_extractor.setup_times
        )

        if len(all_samples) == 0:

            return

        samples = (
            self.__get_learning_samples(
                all_samples
            )
        )

        if len(samples) == 0:

            return

       
        # Mean setup time
      

        self.model.mean_setup_time = (
            sum(samples) / len(samples)
        )

        
        # Standard deviation
        

        if len(samples) > 1:

            mean = (
                self.model.mean_setup_time
            )

            variance = (
                sum(
                    (sample - mean) ** 2
                    for sample in samples
                )
                / (len(samples) - 1)
            )

            self.model.setup_std = (
                variance ** 0.5
            )

        else:

            self.model.setup_std = 0.0

      
        # Total observed setup operations
       

        self.model.observed_setups = (
            len(all_samples)
        )

      
        # Distribution fitting
      

        best_fit = (
            self.__fit_distribution(
                samples
            )
        )

        if best_fit is not None:

            self.model.setup_distribution = (
                best_fit
            )

    
    # Idle Behaviour
    

    def __learn_idle(
        self,
    ):

        all_samples = (
            self.feature_extractor.idle_times
        )

        if len(all_samples) == 0:

            return

        samples = (
            self.__get_learning_samples(
                all_samples
            )
        )

        if len(samples) == 0:

            return

        self.model.mean_idle_time = (
            sum(samples) / len(samples)
        )

        
        # Standard deviation
       

        if len(samples) > 1:

            mean = (
                self.model.mean_idle_time
            )

            variance = (
                sum(
                    (sample - mean) ** 2
                    for sample in samples
                )
                / (len(samples) - 1)
            )

            self.model.idle_std = (
                variance ** 0.5
            )

        else:

            self.model.idle_std = 0.0

        best_fit = (
            self.__fit_distribution(
                samples
            )
        )

        if best_fit is not None:

            self.model.idle_distribution = (
                best_fit
            )

   
    # Processing Behaviour
    

    def __learn_processing(
        self,
    ):

        all_samples = (
            self.feature_extractor.processing_times
        )

        if len(all_samples) == 0:

            return

        samples = (
            self.__get_learning_samples(
                all_samples
            )
        )

        if len(samples) == 0:

            return

        self.model.processing_mean = (
            sum(samples) / len(samples)
        )

       
        # Standard deviation
     

        if len(samples) > 1:

            mean = (
                self.model.processing_mean
            )

            variance = (
                sum(
                    (sample - mean) ** 2
                    for sample in samples
                )
                / (len(samples) - 1)
            )

            self.model.processing_std = (
                variance ** 0.5
            )

        else:

            self.model.processing_std = 0.0


        self.model.observed_jobs = len(
            all_samples
        )

        best_fit = (
            self.__fit_distribution(
                samples
            )
        )

        if best_fit is not None:

            self.model.processing_distribution = (
                best_fit
            )

   
    # Queue Waiting Behaviour
   

    def __learn_waiting(
        self,
    ):

        all_samples = (
            self.feature_extractor.waiting_times
        )

        if len(all_samples) == 0:

            return

        samples = (
            self.__get_learning_samples(
                all_samples
            )
        )

        if len(samples) == 0:

            return

        self.model.mean_waiting_time = (
            sum(samples) / len(samples)
        )

        
        # Standard deviation
        

        if len(samples) > 1:

            mean = (
                self.model.mean_waiting_time
            )

            variance = (
                sum(
                    (sample - mean) ** 2
                    for sample in samples
                )
                / (len(samples) - 1)
            )

            self.model.waiting_std = (
                variance ** 0.5
            )

        else:

            self.model.waiting_std = 0.0

        best_fit = (
            self.__fit_distribution(
                samples
            )
        )

        if best_fit is not None:

            self.model.waiting_distribution = (
                best_fit
            )

  
    # Fault Response Behaviour
   

    def __learn_fault_response(
        self,
    ):

        all_samples = (
            self.feature_extractor.fault_response_times
        )

        if len(all_samples) == 0:

            return

        samples = (
            self.__get_learning_samples(
                all_samples
            )
        )

        if len(samples) == 0:

            return

        self.model.mean_fault_response_time = (
            sum(samples) / len(samples)
        )

        
        # Standard deviation
       

        if len(samples) > 1:

            mean = (
                self.model.mean_fault_response_time
            )

            variance = (
                sum(
                    (sample - mean) ** 2
                    for sample in samples
                )
                / (len(samples) - 1)
            )

            self.model.fault_response_std = (
                variance ** 0.5
            )

        else:

            self.model.fault_response_std = 0.0

        best_fit = (
            self.__fit_distribution(
                samples
            )
        )

        if best_fit is not None:

            self.model.fault_response_distribution = (
                best_fit
            )

   
    # Repair Behaviour
   

    def __learn_repair(
        self,
    ):

        all_samples = (
            self.feature_extractor.repair_times
        )

        if len(all_samples) == 0:

            return

        samples = (
            self.__get_learning_samples(
                all_samples
            )
        )

        if len(samples) == 0:

            return

        self.model.mean_repair_time = (
            sum(samples) / len(samples)
        )

        
        # Standard deviation
       

        if len(samples) > 1:

            mean = (
                self.model.mean_repair_time
            )

            variance = (
                sum(
                    (sample - mean) ** 2
                    for sample in samples
                )
                / (len(samples) - 1)
            )

            self.model.repair_std = (
                variance ** 0.5
            )

        else:

            self.model.repair_std = 0.0

        best_fit = (
            self.__fit_distribution(
                samples
            )
        )

        if best_fit is not None:

            self.model.repair_distribution = (
                best_fit
            )

   
    # CUSUM-Triggered Behavioural Adaptation
   

    def adapt_to_drift(
        self,
        current_state,
        next_state,
        evidence=None,
    ):

      
        # Normalize State Names
        

        if hasattr(
            current_state,
            "name",
        ):

            current_state = (
                current_state.name
            )

        if hasattr(
            next_state,
            "name",
        ):

            next_state = (
                next_state.name
            )

        current_state = str(
            current_state
        )

        next_state = str(
            next_state
        )

        transition = (
            current_state,
            next_state,
        )

       
        # Preserve Evidence for Diagnostics
        

        if evidence is None:

            evidence_copy = []

        else:

            evidence_copy = [
                float(error)
                for error in evidence
            ]

       
        # Record Adaptation Request
       

        self.last_adaptation = {
            "transition": transition,
            "evidence": list(
                evidence_copy
            ),
            "evidence_count": len(
                evidence_copy
            ),
            "window_size": (
                self.sliding_window
                .get_window_size()
            ),
            "sliding_window_enabled": (
                self.sliding_window
                .is_enabled()
            ),
        }

        # Transition-Specific Re-estimation
       

        adapted = False

       
        # JOB_ARRIVAL to JOB_START
       

        if transition == (
            "JOB_ARRIVAL",
            "JOB_START",
        ):

            before = (
                self.model.mean_waiting_time
            )

            self.__learn_waiting()

            after = (
                self.model.mean_waiting_time
            )

            adapted = (
                after != before
            )

     
        # PROCESSING to IDLE
       

        elif transition == (
            "PROCESSING",
            "IDLE",
        ):

            before = (
                self.model.processing_mean
            )

            self.__learn_processing()

            after = (
                self.model.processing_mean
            )

            adapted = (
                after != before
            )

        
        # PROCESSING to FAULTED
        

        elif transition == (
            "PROCESSING",
            "FAULTED",
        ):

            return False

       
        # FAULTED to REPAIR
     

        elif transition == (
            "FAULTED",
            "REPAIR",
        ):

            before = (
                self.model.mean_fault_response_time
            )

            self.__learn_fault_response()

            after = (
                self.model.mean_fault_response_time
            )

            adapted = (
                after != before
            )

        
        # REPAIR to PROCESSING
      

        elif transition == (
            "REPAIR",
            "PROCESSING",
        ):

            before = (
                self.model.mean_repair_time
            )

            self.__learn_repair()

            after = (
                self.model.mean_repair_time
            )

            adapted = (
                after != before
            )

       
        # SETUP_STARTED to SETUP_COMPLETED
        

        elif transition == (
            "SETUP_STARTED",
            "SETUP_COMPLETED",
        ):

            before = (
                self.model.mean_setup_time
            )

            self.__learn_setup()

            after = (
                self.model.mean_setup_time
            )

            adapted = (
                after != before
            )

        
        # Unsupported Transition
       

        else:

            return False

       
        # Count Successful Adaptation

        self.adaptation_count += 1

        self.last_adaptation[
            "successful"
        ] = True

        self.last_adaptation[
            "parameter_changed"
        ] = adapted

        return True

    # Learning Markov State Transitions
    

    def observe_state_transition(
        self,
        current_state,
    ):


        if self.previous_state is None:

            self.previous_state = (
                current_state
            )

            return

        if (
            current_state
            == self.previous_state
        ):

            return

        self.markov_chain.observe_transition(
            self.previous_state,
            current_state,
        )

        self.previous_state = (
            current_state
        )

   
    # Public Accessors
    

    def get_worker_behaviour_report(
        self,
    ) -> Dict[Any, Dict[str, Any]]:
        
        report: Dict[Any, Dict[str, Any]] = {}

        worker_ids = set(
            self.worker_setup_times.keys()
        )
        worker_ids.update(
            self.worker_processing_times.keys()
        )
        worker_ids.update(
            self.worker_fault_response_times.keys()
        )
        worker_ids.update(
            self.worker_repair_times.keys()
        )
        worker_ids.update(
            self.model.worker_behaviours.keys()
        )

        for worker_id in sorted(
            worker_ids,
            key=lambda value: str(value),
        ):
            worker_model = (
                self.model.worker_behaviours.get(
                    worker_id
                )
            )

            setup_samples = self.worker_setup_times.get(
                worker_id,
                [],
            )
            processing_samples = (
                self.worker_processing_times.get(
                    worker_id,
                    [],
                )
            )
            fault_samples = (
                self.worker_fault_response_times.get(
                    worker_id,
                    [],
                )
            )
            repair_samples = (
                self.worker_repair_times.get(
                    worker_id,
                    [],
                )
            )

            if worker_model is None:
                continue

            report[worker_id] = {
                "worker_id": worker_id,
                "setup_observations": len(
                    setup_samples
                ),
                "processing_observations": len(
                    processing_samples
                ),
                "fault_response_observations": len(
                    fault_samples
                ),
                "repair_observations": len(
                    repair_samples
                ),
                "learned_setup_mean": (
                    worker_model.mean_setup_time
                ),
                "learned_processing_mean": (
                    worker_model.processing_mean
                ),
                "learned_fault_response_mean": (
                    worker_model.mean_fault_response_time
                ),
                "learned_repair_mean": (
                    worker_model.mean_repair_time
                ),
            }

        return report

    def get_worker_characteristic_summary(
        self,
    ) -> Dict[Any, Dict[str, Any]]:
       
        report = self.get_worker_behaviour_report()

        return {
            worker_id: {
                "setup_mean": values[
                    "learned_setup_mean"
                ],
                "processing_mean": values[
                    "learned_processing_mean"
                ],
                "fault_response_mean": values[
                    "learned_fault_response_mean"
                ],
                "repair_mean": values[
                    "learned_repair_mean"
                ],
                "setup_observations": values[
                    "setup_observations"
                ],
                "processing_observations": values[
                    "processing_observations"
                ],
                "fault_response_observations": values[
                    "fault_response_observations"
                ],
                "repair_observations": values[
                    "repair_observations"
                ],
            }
            for worker_id, values in report.items()
        }

    def get_behaviour_model(
        self,
    ):

        return self.model

    # =====================================================

    def get_worker_behaviour(
        self,
        worker_id=None,
    ):

        if worker_id is None:

            return dict(
                self.model.worker_behaviours
            )

        return self.model.worker_behaviours.get(
            str(worker_id)
        )


    def get_markov_chain(
        self,
    ):

        return self.markov_chain

    # =====================================================

    def get_window_size(
        self,
    ):

        return (
            self.sliding_window
            .get_window_size()
        )

    # =====================================================

    def is_sliding_window_enabled(
        self,
    ):

        return (
            self.sliding_window
            .is_enabled()
        )

   
    # Adaptation Statistics
   

    def get_adaptation_count(
        self,
    ):
        

        return self.adaptation_count

    # =====================================================

    def get_last_adaptation(
        self,
    ):

        if self.last_adaptation is None:

            return None

        return dict(
            self.last_adaptation
        )