from common_model.models.machine_state import MachineState
from system_b.models.operational_state import OperationalState

from system_b.synchronizer.state_synchronizer import (
    StateSynchronizer,
)

from system_b.estimation.behaviour_estimator import (
    BehaviourEstimator,
)

from system_b.receiver.event_receiver import (
    EventReceiver,
)

from system_b.prediction.prediction_engine import (
    PredictionEngine,
)

from system_b.evaluation.prediction_validator import (
    PredictionValidator,
)

from system_b.evaluation.online_prediction_evaluator import (
    OnlinePredictionEvaluator,
)

from system_b.adaptation.drift_detector import (
    DriftDetector,
)

from system_b.adaptation.transition_drift_detector import (
    TransitionDriftDetector,
)

from system_b.adaptation.transition_adaptation import (
    TransitionAdaptation,
)

from system_b.adaptation.adaptation_manager import (
    AdaptationManager,
)


class DigitalTwin:

    

    def __init__(
        self,
    ):

    
        # Operational State
        

        self.operational_state = (
            OperationalState()
        )

        
        # Synchronization
        

        self.state_synchronizer = (
            StateSynchronizer(
                self.operational_state
            )
        )

       
        # Behaviour Learning
       

        self.behaviour_estimator = (
            BehaviourEstimator()
        )

        
        # Open-Loop Prediction Validation
        

        self.prediction_validator = (
            PredictionValidator()
        )

        
        # Rolling One-Step Prediction Validation
        

        self.online_prediction_evaluator = (
            OnlinePredictionEvaluator()
        )

        
        # Drift Detection
        

        self.drift_detector = (
            DriftDetector()
        )

        
        # Point 3: Categorical Transition Drift Detection

        self.transition_drift_detector = (
            TransitionDriftDetector()
        )

        # Point 4: Parallel Transition Adaptation


        self.transition_adaptation = (
            TransitionAdaptation(
                states=list(
                    MachineState
                ),
            )
        )

        # Adaptation Manager
        

        self.adaptation_manager = (
            AdaptationManager(
                drift_detector=(
                    self.drift_detector
                ),
                adaptation_callback=(
                    self._adapt_behaviour_model
                ),
                transition_drift_detector=(
                    self.transition_drift_detector
                ),
                transition_adaptation=(
                    self.transition_adaptation
                ),
            )
        )

        
        # Event Receiver

        self.event_receiver = (
            EventReceiver(
                self.state_synchronizer,
                self.behaviour_estimator,
                self.prediction_validator,
                self.online_prediction_evaluator,
                self.adaptation_manager,
                self.behaviour_estimator.get_markov_chain(),
            )
        )

        # Prediction Engine
        

        self.prediction_engine = (
            PredictionEngine(
                self.behaviour_estimator
                .get_markov_chain()
            )
        )

     
        # Rolling Prediction Callback
       

        self.event_receiver.set_prediction_callback(
            self.predict_next_transition
        )

    
        # Current Operating Mode
       

        self.mode = "TRAINING"

        # Adaptation Initially Disabled
       

        self.event_receiver.disable_adaptation()

   
    # Behavioural Adaptation Callback
    

    def _adapt_behaviour_model(
        self,
        transition,
        evidence,
    ):

        # Validate Transition
        

        if (
            transition is None
            or len(transition) != 2
        ):

            return False

        current_state = (
            transition[0]
        )

        next_state = (
            transition[1]
        )

        # Delegate Adaptation
        

        return (
            self.behaviour_estimator
            .adapt_to_drift(
                current_state=current_state,
                next_state=next_state,
                evidence=evidence,
            )
        )

    
    # Event Interface
   

    def receive(
        self,
        event,
    ):

        return self.event_receiver.receive(
            event
        )

    # General / Open-Loop Prediction
    

    def predict(
        self,
        prediction_steps=10,
        store_predictions=True,
    ):

        trajectory = (
            self.prediction_engine.predict(
                operational_state=(
                    self.operational_state
                ),
                behaviour_model=(
                    self.behaviour_estimator
                    .get_behaviour_model()
                ),
                prediction_steps=(
                    prediction_steps
                ),
            )
        )

        if store_predictions:

            self.prediction_validator.store_predictions(
                trajectory
            )

        return trajectory

    # Rolling One-Step Prediction
    

    def predict_next_transition(
        self,
    ):

        trajectory = (
            self.prediction_engine.predict(
                operational_state=(
                    self.operational_state
                ),
                behaviour_model=(
                    self.behaviour_estimator
                    .get_behaviour_model()
                ),
                prediction_steps=1,
            )
        )

        if len(trajectory) == 0:

            self.online_prediction_evaluator.set_prediction(
                None
            )

            return None

        prediction = (
            trajectory[0]
        )

        self.online_prediction_evaluator.set_prediction(
            prediction
        )

        return prediction

   
    # Rolling Prediction Control
    

    def start_rolling_prediction(
        self,
    ):

        self.event_receiver.enable_rolling_prediction()

        return (
            self.predict_next_transition()
        )

    # =====================================================

    def stop_rolling_prediction(
        self,
    ):

        self.event_receiver.disable_rolling_prediction()

  
    # Training Mode
    

    def start_training(
        self,
    ):

        self.stop_rolling_prediction()

        
        # Cumulative Behavioural Learning
       

        self.behaviour_estimator.disable_sliding_window()

       
        # Enable Learning
       

        self.event_receiver.enable_learning()

        
        # Disable Validation
        

        self.event_receiver.disable_validation()

      
        # Disable Adaptation
        

        self.event_receiver.disable_adaptation()

        self.mode = "TRAINING"

   
    # Frozen Validation
    

    def start_frozen_validation(
        self,
    ):

        self.stop_rolling_prediction()

       
        # No Sliding-Window Learning
        

        self.behaviour_estimator.disable_sliding_window()

        
        # Freeze Learning
       

        self.event_receiver.disable_learning()

        
        # Enable Validation
        

        self.event_receiver.enable_validation()

        
        # Disable Adaptation
       

        self.event_receiver.disable_adaptation()

       
        # Reset Evaluation State
        

        self.online_prediction_evaluator.reset()

        self.mode = "FROZEN_VALIDATION"

   
    # Adaptive Validation
   

    def start_adaptive_validation(
        self,
    ):

        self.stop_rolling_prediction()

        
        # Cumulative Behavioural Learning
        

        self.behaviour_estimator.disable_sliding_window()

        
        # Enable Learning
        

        self.event_receiver.enable_learning()

       
        # Enable Validation
        

        self.event_receiver.enable_validation()

        
        # Enable Adaptation
        

        self.event_receiver.enable_adaptation()

        
        # Reset Evaluation State
       

        self.online_prediction_evaluator.reset()

        
        # Reset CUSUM / Adaptation Statistics
        

        self.adaptation_manager.reset()

        self.mode = "ADAPTIVE_VALIDATION"

    
    # Sliding-Window Adaptive Validation
    

    def start_sliding_window_adaptive_validation(
        self,
        window_size=20,
    ):

        self.stop_rolling_prediction()

        
        # Enable Sliding Window
        

        self.behaviour_estimator.enable_sliding_window(
            window_size=window_size
        )

        
        # Enable Learning
       

        self.event_receiver.enable_learning()

        
        # Enable Validation
       

        self.event_receiver.enable_validation()

      
        # Enable Adaptation
        

        self.event_receiver.enable_adaptation()

        
        # Reset Evaluation State
        

        self.online_prediction_evaluator.reset()

        
        # Reset Adaptation State
        

        self.adaptation_manager.reset()

        self.mode = (
            "SLIDING_WINDOW_ADAPTIVE_VALIDATION"
        )

    
    # Learning Control
    

    def freeze_learning(
        self,
    ):

        self.event_receiver.disable_learning()

    # =====================================================

    def resume_learning(
        self,
    ):

        self.event_receiver.enable_learning()

    
    # Accessors
    

    def get_operational_state(
        self,
    ):

        return self.operational_state

    # =====================================================

    def get_behaviour_model(
        self,
    ):

        return (
            self.behaviour_estimator
            .get_behaviour_model()
        )

    # =====================================================

    def get_prediction_validator(
        self,
    ):

        return self.prediction_validator

    # =====================================================

    def get_online_prediction_evaluator(
        self,
    ):

        return (
            self.online_prediction_evaluator
        )

    # =====================================================

    def get_adaptation_manager(
        self,
    ):

        return self.adaptation_manager

    # =====================================================

    def get_drift_detector(
        self,
    ):

        return self.drift_detector

    
    # Adaptation Diagnostics
    

    def get_adaptation_summary(
        self,
    ):

        return (
            self.adaptation_manager
            .get_transition_summary()
        )

    # =====================================================

    def get_transition_drift_summary(
        self,
    ):

        return (
            self.adaptation_manager
            .get_transition_drift_summary()
        )

    def get_transition_adaptation_summary(
        self,
    ):

        return (
            self.adaptation_manager
            .get_transition_adaptation_summary()
        )

    def get_prediction_results(
        self,
    ):

        return self.online_prediction_evaluator.get_metrics()

    # =====================================================

    def get_validation_results(
        self,
    ):

        return self.prediction_validator.evaluate()

    # =====================================================

    def get_transition_monitoring_history(
        self,
    ):

        return (
            self.adaptation_manager
            .get_transition_monitoring_history()
        )

    # =====================================================

    def get_transition_adaptation_history(
        self,
    ):

        return (
            self.adaptation_manager
            .get_transition_adaptation_history()
        )

    def get_mode(
        self,
    ):

        return self.mode

    # =====================================================

    def get_sliding_window_size(
        self,
    ):

        return (
            self.behaviour_estimator
            .get_window_size()
        )

    # =====================================================

    def is_sliding_window_enabled(
        self,
    ):

        return (
            self.behaviour_estimator
            .is_sliding_window_enabled()
        )

    # =====================================================

    def is_adaptation_enabled(
        self,
    ):

        return (
            self.adaptation_manager
            .is_enabled()
        )