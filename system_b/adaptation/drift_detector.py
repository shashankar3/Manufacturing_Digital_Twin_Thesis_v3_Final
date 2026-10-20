class DriftDetector:

    def __init__(
        self,
        reference_value=0.5,
        threshold=5.0,
    ):
        

        if reference_value < 0:
            raise ValueError(
                "reference_value must be non-negative."
            )

        if threshold <= 0:
            raise ValueError(
                "threshold must be greater than zero."
            )

        
        # CUSUM Configuration
        

        self.reference_value = float(
            reference_value
        )

        self.threshold = float(
            threshold
        )

        
        # CUSUM State
        

        self.positive_cusum = 0.0

        self.negative_cusum = 0.0

        
        # Detection Statistics
        

        self.observed_errors = 0

        self.detected_drifts = 0

        self.last_drift_direction = None

      
        # Most Recent Error
       

        self.last_error = None

   
    # Observe Prediction Error
    

    def observe(
        self,
        error,
    ):

        error = float(error)

        self.last_error = error

        self.observed_errors += 1

       
        # Positive CUSUM
        

        self.positive_cusum = max(
            0.0,
            self.positive_cusum
            + error
            - self.reference_value,
        )

        
        # Negative CUSUM
       

        self.negative_cusum = min(
            0.0,
            self.negative_cusum
            + error
            + self.reference_value,
        )

        
        # Positive Drift Detection
      

        if (
            self.positive_cusum
            >= self.threshold
        ):

            self.detected_drifts += 1

            self.last_drift_direction = (
                "POSITIVE"
            )

            self.__reset_cusum()

            return True

       
        # Negative Drift Detection
        

        if (
            self.negative_cusum
            <= -self.threshold
        ):

            self.detected_drifts += 1

            self.last_drift_direction = (
                "NEGATIVE"
            )

            self.__reset_cusum()

            return True

        return False

    
    # Internal CUSUM Reset
    

    def __reset_cusum(
        self,
    ):
        

        self.positive_cusum = 0.0

        self.negative_cusum = 0.0

    
    # Full Reset
   

    def reset(
        self,
    ):
       

        self.positive_cusum = 0.0

        self.negative_cusum = 0.0

        self.observed_errors = 0

        self.detected_drifts = 0

        self.last_drift_direction = None

        self.last_error = None

    

    def get_positive_cusum(
        self,
    ):
        

        return self.positive_cusum

    

    def get_negative_cusum(
        self,
    ):
        

        return self.negative_cusum

    

    def get_observed_errors(
        self,
    ):
        

        return self.observed_errors

    

    def get_detected_drifts(
        self,
    ):
        

        return self.detected_drifts

    

    def get_last_drift_direction(
        self,
    ):

        return self.last_drift_direction

 

    def get_last_error(
        self,
    ):
        

        return self.last_error

    

    def get_state(
        self,
    ):

        return {
            "reference_value": (
                self.reference_value
            ),
            "threshold": (
                self.threshold
            ),
            "positive_cusum": (
                self.positive_cusum
            ),
            "negative_cusum": (
                self.negative_cusum
            ),
            "observed_errors": (
                self.observed_errors
            ),
            "detected_drifts": (
                self.detected_drifts
            ),
            "last_drift_direction": (
                self.last_drift_direction
            ),
            "last_error": (
                self.last_error
            ),
        }


    def __repr__(
        self,
    ):
        

        return (
            "DriftDetector("
            f"reference_value="
            f"{self.reference_value}, "
            f"threshold="
            f"{self.threshold}, "
            f"positive_cusum="
            f"{self.positive_cusum:.4f}, "
            f"negative_cusum="
            f"{self.negative_cusum:.4f}, "
            f"observed_errors="
            f"{self.observed_errors}, "
            f"detected_drifts="
            f"{self.detected_drifts}"
            ")"
        )