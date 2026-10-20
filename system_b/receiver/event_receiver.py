from common_model.models.event_type import EventType
from common_model.models.machine_state import MachineState

from system_b.synchronizer.state_synchronizer import StateSynchronizer
from system_b.estimation.behaviour_estimator import BehaviourEstimator
from system_b.evaluation.prediction_validator import PredictionValidator
from system_b.evaluation.online_prediction_evaluator import (
    OnlinePredictionEvaluator,
)
from system_b.adaptation.adaptation_manager import AdaptationManager
from system_b.prediction.markov_chain import MarkovChain


class EventReceiver:
   

    # EVENTS THAT CAN PRODUCE OPERATIONAL STATE TRANSITIONS
   

    STATE_TRANSITION_EVENTS = {
        EventType.JOB_START,
        EventType.SETUP_STARTED,
        EventType.JOB_COMPLETED,
        EventType.FAILURE_DETECTED,
        EventType.REPAIR_STARTED,
        EventType.REPAIR_COMPLETED,
    }


    def __init__(
        self,
        synchronizer: StateSynchronizer,
        behaviour_estimator: BehaviourEstimator,
        prediction_validator: PredictionValidator,
        online_prediction_evaluator: OnlinePredictionEvaluator,
        adaptation_manager: AdaptationManager,
        markov_chain: MarkovChain = None,
    ):

        self.synchronizer = synchronizer
        self.behaviour_estimator = behaviour_estimator
        self.prediction_validator = prediction_validator
        self.online_prediction_evaluator = (
            online_prediction_evaluator
        )
        self.adaptation_manager = adaptation_manager

       
        self.markov_chain = markov_chain

       
        # Learning
       

        self.learning_enabled = True

       
        # Validation
       

        self.validation_enabled = False

        
        # Rolling prediction
        

        self.prediction_callback = None
        self.rolling_prediction_enabled = False

   
    # LEARNING CONTROL
   

    def enable_learning(self):
        """Enable behavioural learning."""
        self.learning_enabled = True

    # =====================================================

    def disable_learning(self):
        """Disable behavioural learning."""
        self.learning_enabled = False

    
    # VALIDATION CONTROL
    

    def enable_validation(self):
        """Enable prediction validation."""
        self.validation_enabled = True

    # =====================================================

    def disable_validation(self):
        """Disable prediction validation."""
        self.validation_enabled = False

    
    # ADAPTATION CONTROL
   

    def enable_adaptation(self):
        
        self.adaptation_manager.enable()

    # =====================================================

    def disable_adaptation(self):
        
        self.adaptation_manager.disable()

   
    # ROLLING PREDICTION CONTROL
   

    def set_prediction_callback(self, callback):
        
        self.prediction_callback = callback

    # =====================================================

    def enable_rolling_prediction(self):
        
        self.rolling_prediction_enabled = True

    # =====================================================

    def disable_rolling_prediction(self):
       
        self.rolling_prediction_enabled = False

   
    # STATE TRANSITION EVENT DETECTION
  

    def is_state_transition_event(self, event):
       

        return event.event_type in self.STATE_TRANSITION_EVENTS

   
    # EVENT to MACHINE STATE MAPPING
    

    def state_from_event(self, event):
        

        event_type = event.event_type

        
        # Job starts.
       

        if event_type == EventType.JOB_START:
            return MachineState.PROCESSING

       
        # SETUP starts.
        

        if event_type == EventType.SETUP_STARTED:
            return MachineState.SETUP

        # SETUP completes and processing begins.
       

        if event_type == EventType.SETUP_COMPLETED:
            return self.synchronizer.state.machine_state

        # Job completes and machine becomes idle.
       

        if event_type == EventType.JOB_COMPLETED:
            return MachineState.IDLE

        # Machine failure.
       

        if event_type == EventType.FAILURE_DETECTED:
            return MachineState.FAULTED

        # Repair begins.
        

        if event_type == EventType.REPAIR_STARTED:
            return MachineState.REPAIR

        # Repair completes.
       

        if event_type == EventType.REPAIR_COMPLETED:
            
            if self.synchronizer.pre_failure_state is not None:
                return self.synchronizer.pre_failure_state
            return self.synchronizer.state.machine_state


        if event_type in {
            EventType.MACHINE_CYCLE_STARTED,
            EventType.MACHINE_CYCLE_COMPLETED,
        }:
            return None


        return None

    
    # ACTUAL STATE TRANSITION DETECTION
    

    def is_actual_state_transition(
        self,
        previous_state,
        new_state,
    ):
        

        if new_state is None:
            return False

        if previous_state is None:
            return True

        return previous_state != new_state

   
    # RECEIVE EVENT
    

    def receive(self, event):
       

        
        # 1. DETERMINE CANDIDATE STATE
       

        candidate_state = self.state_from_event(event)

        # State before processing this event.
        previous_state = self.synchronizer.state.machine_state

        # 2. DETERMINE GENUINE STATE TRANSITION
      

        is_transition_event = self.is_state_transition_event(
            event
        )

        actual_state_transition = (
            is_transition_event
            and self.is_actual_state_transition(
                previous_state,
                candidate_state,
            )
        )

        # POINT 3: PRE-UPDATE TRANSITION PROBABILITY
    

        transition_probability = None

        if (
            actual_state_transition
            and previous_state is not None
            and candidate_state is not None
            and self.markov_chain is not None
        ):
            transition_probability = (
                self.markov_chain.get_transition_probability(
                    previous_state,
                    candidate_state,
                )
            )

       
        # VALIDATION RESULT
        

        validation_result = None

       
        # 3. VALIDATE ACTIVE PREDICTION
       

        if (
            self.validation_enabled
            and actual_state_transition
            and self.online_prediction_evaluator.has_active_prediction()
        ):

            validation_result = (
                self.online_prediction_evaluator.validate_transition(
                    actual_state=candidate_state.name,
                    actual_time=event.timestamp,
                    event_type=event.event_type.name,
                    job_id=event.job_id,
                )
            )


        transition_adaptation_result = None

        if (
            actual_state_transition
            and transition_probability is not None
            and self.adaptation_manager.is_enabled()
        ):
            transition_adaptation_result = (
                self.adaptation_manager.observe_transition(
                    current_state=previous_state,
                    next_state=candidate_state,
                    probability=transition_probability,
                )
            )

        
        # 4. SYNCHRONIZE SYSTEM B
        

        self.synchronizer.synchronize(event)

       
        # 5. RECORD EVENT
        

        if self.validation_enabled:
            self.prediction_validator.record_event(event)

        
        # 6. BEHAVIOURAL LEARNING
        

        if self.learning_enabled:

            
            self.behaviour_estimator.observe(event)

            
            self.behaviour_estimator.observe_state_transition(
                self.synchronizer.state.machine_state
            )

        
        # 7. ADAPTIVE DRIFT MONITORING
        

        adaptation_result = None

        if (
            validation_result is not None
            and validation_result["drift_eligible"]
            and self.adaptation_manager.is_enabled()
        ):

            current_state = validation_result[
                "current_state"
            ]

            next_state = validation_result[
                "actual_state"
            ]

            timing_error = validation_result[
                "timing_error"
            ]

            adaptation_result = (
                self.adaptation_manager.observe_error(
                    current_state=current_state,
                    next_state=next_state,
                    error=timing_error,
                )
            )

       
        # 8. GENERATE NEXT ROLLING PREDICTION
        

        if (
            self.validation_enabled
            and self.rolling_prediction_enabled
            and actual_state_transition
            and self.prediction_callback is not None
        ):

            self.prediction_callback()

        
        # RETURN RESULTS
        

        return {
            "validation_result": validation_result,
            "adaptation_result": adaptation_result,
            "transition_adaptation_result": (
                transition_adaptation_result
            ),
            "transition_probability": transition_probability,
            "is_transition_event": is_transition_event,
            "actual_state_transition": actual_state_transition,
            "previous_state": (
                previous_state.name
                if previous_state is not None
                else None
            ),
            "new_state": (
                candidate_state.name
                if candidate_state is not None
                else None
            ),
        }