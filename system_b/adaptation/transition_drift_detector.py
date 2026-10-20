from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple


class TransitionDriftDetector:

    def __init__(
        self,
        reference_value: float = 0.5,
        threshold: float = 5.0,
        epsilon: float = 1e-12,
    ) -> None:

        if reference_value < 0:
            raise ValueError(
                "reference_value must be >= 0."
            )

        if threshold <= 0:
            raise ValueError(
                "threshold must be > 0."
            )

        if epsilon <= 0 or epsilon >= 1:
            raise ValueError(
                "epsilon must be between 0 and 1."
            )

        self.reference_value = float(
            reference_value
        )

        self.threshold = float(
            threshold
        )

        self.epsilon = float(
            epsilon
        )

        # Current one-sided CUSUM statistic.
        self.cusum = 0.0

        # Number of transitions observed by this detector.
        self.observation_count = 0

        # Number of times the threshold has been crossed.
        self.alarm_count = 0

        # Information from the most recent observation.
        self.last_probability: Optional[float] = None
        self.last_surprise: Optional[float] = None

        self.last_transition: Optional[
            Tuple[Any, Any]
        ] = None

        self.last_alarm = False

    def observe_probability(
        self,
        probability: float,
        current_state: Any = None,
        next_state: Any = None,
    ) -> Dict[str, Any]:

        if not isinstance(
            probability,
            (int, float),
        ):
            raise TypeError(
                "probability must be numeric."
            )

        probability = float(
            probability
        )

        if not math.isfinite(
            probability
        ):
            raise ValueError(
                "probability must be finite."
            )

        if (
            probability < 0.0
            or probability > 1.0
        ):
            raise ValueError(
                "probability must be between 0 and 1."
            )

        # A zero-probability transition is maximally surprising.
        
        safe_probability = max(
            probability,
            self.epsilon,
        )

        
        # Transition surprise
       

        surprise = -math.log(
            safe_probability
        )

       
        # One-sided CUSUM
        

        self.cusum = max(
            0.0,
            self.cusum
            + surprise
            - self.reference_value,
        )

        self.observation_count += 1

        self.last_probability = (
            probability
        )

        self.last_surprise = (
            surprise
        )

        self.last_transition = (
            current_state,
            next_state,
        )

        
        # Drift decision
       

        self.last_alarm = (
            self.cusum >= self.threshold
        )

        if self.last_alarm:
            self.alarm_count += 1

        return self.get_status()

   
    # Transition-oriented interface
    

    def observe_transition(
        self,
        current_state: Any,
        next_state: Any,
        probability: float,
    ) -> Dict[str, Any]:

        return self.observe_probability(
            probability=probability,
            current_state=current_state,
            next_state=next_state,
        )

    
    # Reset
    

    def reset(self) -> None:
       

        self.cusum = 0.0

        self.last_probability = None

        self.last_surprise = None

        self.last_transition = None

        self.last_alarm = False

    
    # Status
    

    def is_drift_detected(
        self,
    ) -> bool:

        return self.last_alarm

    

    def get_cusum(
        self,
    ) -> float:

        return self.cusum

   

    def get_status(
        self,
    ) -> Dict[str, Any]:
       

        return {
            "cusum": self.cusum,
            "reference_value": (
                self.reference_value
            ),
            "threshold": (
                self.threshold
            ),
            "last_probability": (
                self.last_probability
            ),
            "last_surprise": (
                self.last_surprise
            ),
            "last_transition": (
                self.last_transition
            ),
            "drift_detected": (
                self.last_alarm
            ),
            "observation_count": (
                self.observation_count
            ),
            "alarm_count": (
                self.alarm_count
            ),
        }

   

    def get_parameters(
        self,
    ) -> Dict[str, float]:
        

        return {
            "reference_value": (
                self.reference_value
            ),
            "threshold": (
                self.threshold
            ),
            "epsilon": (
                self.epsilon
            ),
        }