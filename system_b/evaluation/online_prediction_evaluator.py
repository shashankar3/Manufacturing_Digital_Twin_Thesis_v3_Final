import math


class OnlinePredictionEvaluator:
    

    def __init__(
        self,
    ):

        
        # Current one-step machine-state prediction
        

        self.active_prediction = None

        
        # Current inter-arrival prediction
        

        self.active_interarrival_prediction = None

        
        # Current setup prediction
      

        self.active_setup_prediction = None

        
        # Completed machine-state comparisons
      

        self.results = []

        
        # Completed inter-arrival comparisons
       

        self.interarrival_results = []

       
        # Completed setup comparisons
        

        self.setup_results = []

       
        # Prediction counter
        

        self.prediction_counter = 0

       
        # Inter-arrival prediction counter
       

        self.interarrival_prediction_counter = 0

       
        # Setup prediction counter
        

        self.setup_prediction_counter = 0

    
    # Store Active Prediction
    

    def set_prediction(
        self,
        prediction,
    ):
        

        
        # No Prediction
        

        if prediction is None:

            self.active_prediction = None

            return

        
        # Increment Prediction Counter
       

        self.prediction_counter += 1

        
        # Basic Prediction Information
        

        active_prediction = {
            "prediction_number":
                self.prediction_counter,

            "current_state":
                prediction["current_state"],

            "predicted_state":
                prediction["next_state"],

            "holding_time":
                float(
                    prediction["holding_time"]
                ),

            "predicted_time":
                float(
                    prediction["transition_time"]
                ),

            
            # Optional setup prediction
           

            "setup_time":
                (
                    None
                    if prediction.get(
                        "setup_time"
                    ) is None
                    else float(
                        prediction["setup_time"]
                    )
                ),
        }

        
        # Store Active Prediction
       

        self.active_prediction = (
            active_prediction
        )

    
    # Store Inter-Arrival Prediction
    

    def set_interarrival_prediction(
        self,
        prediction,
    ):

        if prediction is None:

            self.active_interarrival_prediction = None

            return

        self.interarrival_prediction_counter += 1

        self.active_interarrival_prediction = {
            "prediction_number":
                self.interarrival_prediction_counter,

            "interarrival_time":
                float(
                    prediction[
                        "interarrival_time"
                    ]
                ),

            "predicted_arrival_time":
                float(
                    prediction[
                        "arrival_time"
                    ]
                ),
        }

    
    # Store Setup Prediction
    

    def set_setup_prediction(
        self,
        prediction,
    ):
        

        if prediction is None:

            self.active_setup_prediction = None

            return

        self.setup_prediction_counter += 1

        self.active_setup_prediction = {
            "prediction_number":
                self.setup_prediction_counter,

            "setup_time":
                float(
                    prediction[
                        "setup_time"
                    ]
                ),
        }

   
    # Validate Inter-Arrival Prediction
   

    def validate_interarrival(
        self,
        actual_arrival_time,
    ):
       

        if (
            self.active_interarrival_prediction
            is None
        ):

            return None

        prediction = (
            self.active_interarrival_prediction
        )

        actual_arrival_time = float(
            actual_arrival_time
        )

        predicted_arrival_time = (
            prediction[
                "predicted_arrival_time"
            ]
        )

        arrival_time_error = (
            actual_arrival_time
            - predicted_arrival_time
        )

        absolute_arrival_time_error = abs(
            arrival_time_error
        )

        squared_arrival_time_error = (
            arrival_time_error ** 2
        )

        result = {
            "prediction_number":
                prediction[
                    "prediction_number"
                ],

            "predicted_interarrival_time":
                prediction[
                    "interarrival_time"
                ],

            "predicted_arrival_time":
                predicted_arrival_time,

            "actual_arrival_time":
                actual_arrival_time,

            "arrival_time_error":
                arrival_time_error,

            "absolute_arrival_time_error":
                absolute_arrival_time_error,

            "squared_arrival_time_error":
                squared_arrival_time_error,
        }

        self.interarrival_results.append(
            result
        )

       
        # Prediction Has Been Consumed
        

        self.active_interarrival_prediction = None

        return result

    
    # Validate Setup Prediction
    

    def validate_setup(
        self,
        setup_start_time,
        setup_completed_time,
        job_id=None,
    ):
       

        if (
            self.active_setup_prediction
            is None
        ):

            return None

        prediction = (
            self.active_setup_prediction
        )

        setup_start_time = float(
            setup_start_time
        )

        setup_completed_time = float(
            setup_completed_time
        )

        actual_setup_time = (
            setup_completed_time
            - setup_start_time
        )

        predicted_setup_time = (
            prediction[
                "setup_time"
            ]
        )

        setup_time_error = (
            actual_setup_time
            - predicted_setup_time
        )

        absolute_setup_time_error = abs(
            setup_time_error
        )

        squared_setup_time_error = (
            setup_time_error ** 2
        )

        result = {
            "prediction_number":
                prediction[
                    "prediction_number"
                ],

            "predicted_setup_time":
                predicted_setup_time,

            "actual_setup_time":
                actual_setup_time,

            "setup_time_error":
                setup_time_error,

            "absolute_setup_time_error":
                absolute_setup_time_error,

            "squared_setup_time_error":
                squared_setup_time_error,

            "job_id":
                job_id,
        }

        self.setup_results.append(
            result
        )

       
        # Prediction Has Been Consumed
       

        self.active_setup_prediction = None

        return result

   
    # Check Active Prediction
    

    def has_active_prediction(
        self,
    ):
       

        return (
            self.active_prediction
            is not None
        )

   
    # Validate Actual Transition
    

    def validate_transition(
        self,
        actual_state,
        actual_time,
        event_type=None,
        job_id=None,
    ):
        
        # No Active Prediction
       

        if self.active_prediction is None:

            return None

        prediction = (
            self.active_prediction
        )

        actual_time = float(
            actual_time
        )

     
        # State Correctness
       

        state_correct = (
            prediction[
                "predicted_state"
            ]
            == actual_state
        )

        
        # Timing Error
      

        predicted_time = (
            prediction[
                "predicted_time"
            ]
        )

        timing_error = (
            actual_time
            - predicted_time
        )

        absolute_timing_error = abs(
            timing_error
        )

        squared_timing_error = (
            timing_error ** 2
        )

      
        # Drift Eligibility
       

        drift_eligible = (
            state_correct
        )

        
        # Transition Identification
        

        transition = (
            prediction[
                "current_state"
            ],
            prediction[
                "predicted_state"
            ],
        )

        
        # Store Result
       

        result = {
           

            "prediction_number":
                prediction[
                    "prediction_number"
                ],

            

            "current_state":
                prediction[
                    "current_state"
                ],

            "predicted_state":
                prediction[
                    "predicted_state"
                ],

            "actual_state":
                actual_state,

            "transition":
                transition,

           

            "state_correct":
                state_correct,

           
            "holding_time":
                prediction[
                    "holding_time"
                ],

            "predicted_time":
                predicted_time,

            "actual_time":
                actual_time,

            

            "setup_time":
                prediction[
                    "setup_time"
                ],

            

            "timing_error":
                timing_error,

            "absolute_timing_error":
                absolute_timing_error,

            "squared_timing_error":
                squared_timing_error,

           

            "drift_eligible":
                drift_eligible,

          

            "event_type":
                event_type,

            "job_id":
                job_id,
        }

       
        # Store Result
        

        self.results.append(
            result
        )

        
        # Prediction Has Been Consumed
       

        self.active_prediction = None

        return result

    
    # Aggregate Metrics
    

    def get_metrics(
        self,
    ):

        total = len(
            self.results
        )


        if total == 0:

            return {
                "evaluated_predictions":
                    0,

                "correct_states":
                    0,

                "incorrect_states":
                    0,

                "state_accuracy":
                    0.0,

                "mae":
                    0.0,

                "rmse":
                    0.0,

                "mean_timing_error":
                    0.0,

                "drift_eligible_predictions":
                    0,

                "timing_evaluated_predictions":
                    0,

                "timing_within_1s":
                    0,

                "timing_within_2s":
                    0,

                "timing_within_5s":
                    0,

                "timing_accuracy_1s":
                    0.0,

                "timing_accuracy_2s":
                    0.0,

                "timing_accuracy_5s":
                    0.0,

                "median_absolute_timing_error":
                    0.0,

                "transition_metrics":
                    {},
            }

      
        # State Accuracy
        

        correct_states = sum(
            1
            for result in self.results
            if result[
                "state_correct"
            ]
        )

        incorrect_states = (
            total
            - correct_states
        )

        state_accuracy = (
            correct_states
            / total
        )

       
        # Timing Metrics
        

        mae = (
            sum(
                result[
                    "absolute_timing_error"
                ]
                for result in self.results
            )
            / total
        )

        mean_squared_error = (
            sum(
                result[
                    "squared_timing_error"
                ]
                for result in self.results
            )
            / total
        )

        rmse = math.sqrt(
            mean_squared_error
        )

        mean_timing_error = (
            sum(
                result[
                    "timing_error"
                ]
                for result in self.results
            )
            / total
        )

       
        # Drift-Eligible Predictions
        

        drift_eligible_predictions = sum(
            1
            for result in self.results
            if result[
                "drift_eligible"
            ]
        )


        timing_errors = [
            result["timing_error"]
            for result in self.results
        ]

        absolute_errors = [
            result["absolute_timing_error"]
            for result in self.results
        ]

        timing_evaluated_predictions = len(
            timing_errors
        )

        timing_within_1s = sum(
            1
            for error in absolute_errors
            if error <= 1.0
        )

        timing_within_2s = sum(
            1
            for error in absolute_errors
            if error <= 2.0
        )

        timing_within_5s = sum(
            1
            for error in absolute_errors
            if error <= 5.0
        )

        timing_accuracy_1s = (
            timing_within_1s
            / timing_evaluated_predictions
            if timing_evaluated_predictions
            else 0.0
        )

        timing_accuracy_2s = (
            timing_within_2s
            / timing_evaluated_predictions
            if timing_evaluated_predictions
            else 0.0
        )

        timing_accuracy_5s = (
            timing_within_5s
            / timing_evaluated_predictions
            if timing_evaluated_predictions
            else 0.0
        )

        sorted_absolute_errors = sorted(
            absolute_errors
        )

        middle = (
            len(sorted_absolute_errors) // 2
        )

        if len(sorted_absolute_errors) % 2:
            median_absolute_timing_error = (
                sorted_absolute_errors[middle]
            )
        else:
            median_absolute_timing_error = (
                (
                    sorted_absolute_errors[middle - 1]
                    + sorted_absolute_errors[middle]
                )
                / 2
            )

        
        transition_metrics = {}

        for result in self.results:
            transition = result["transition"]
            transition_entry = transition_metrics.setdefault(
                transition,
                {
                    "evaluated_predictions": 0,
                    "correct_states": 0,
                    "incorrect_states": 0,
                    "timing_absolute_errors": [],
                    "timing_errors": [],
                },
            )

            transition_entry["evaluated_predictions"] += 1
            if result["state_correct"]:
                transition_entry["correct_states"] += 1
            else:
                transition_entry["incorrect_states"] += 1

            transition_entry["timing_absolute_errors"].append(
                result["absolute_timing_error"]
            )
            transition_entry["timing_errors"].append(
                result["timing_error"]
            )

        for transition, entry in transition_metrics.items():
            count = entry["evaluated_predictions"]
            errors = entry["timing_errors"]
            abs_errors = entry["timing_absolute_errors"]
            entry["state_accuracy"] = (
                entry["correct_states"] / count
                if count else 0.0
            )
            entry["mae"] = (
                sum(abs_errors) / count
                if count else 0.0
            )
            entry["rmse"] = math.sqrt(
                sum(error ** 2 for error in errors) / count
            ) if count else 0.0
            entry["mean_timing_error"] = (
                sum(errors) / count
                if count else 0.0
            )
            entry["timing_accuracy_1s"] = (
                sum(error <= 1.0 for error in abs_errors) / count
                if count else 0.0
            )
            entry["timing_accuracy_2s"] = (
                sum(error <= 2.0 for error in abs_errors) / count
                if count else 0.0
            )
            entry["timing_accuracy_5s"] = (
                sum(error <= 5.0 for error in abs_errors) / count
                if count else 0.0
            )
            del entry["timing_absolute_errors"]
            del entry["timing_errors"]

    

        return {
            "evaluated_predictions":
                total,

            "correct_states":
                correct_states,

            "incorrect_states":
                incorrect_states,

            "state_accuracy":
                state_accuracy,

            "mae":
                mae,

            "rmse":
                rmse,

            "mean_timing_error":
                mean_timing_error,

            "drift_eligible_predictions":
                drift_eligible_predictions,

            "timing_evaluated_predictions":
                timing_evaluated_predictions,

            "timing_within_1s":
                timing_within_1s,

            "timing_within_2s":
                timing_within_2s,

            "timing_within_5s":
                timing_within_5s,

            "timing_accuracy_1s":
                timing_accuracy_1s,

            "timing_accuracy_2s":
                timing_accuracy_2s,

            "timing_accuracy_5s":
                timing_accuracy_5s,

            "median_absolute_timing_error":
                median_absolute_timing_error,

            "transition_metrics":
                transition_metrics,
        }

   
    # Behaviour Prediction Metrics
   

    def get_behaviour_metrics(
        self,
    ):
        """
        Calculate aggregate metrics for the additional
        behavioural prediction processes:

            - job inter-arrival time
            - setup time

        These metrics remain separate from machine-state
        transition metrics.
        """

        
        # Inter-arrival metrics
       

        interarrival_total = len(
            self.interarrival_results
        )

        if interarrival_total > 0:

            interarrival_mae = (
                sum(
                    result[
                        "absolute_arrival_time_error"
                    ]
                    for result
                    in self.interarrival_results
                )
                / interarrival_total
            )

            interarrival_mse = (
                sum(
                    result[
                        "squared_arrival_time_error"
                    ]
                    for result
                    in self.interarrival_results
                )
                / interarrival_total
            )

            interarrival_rmse = math.sqrt(
                interarrival_mse
            )

            mean_interarrival_error = (
                sum(
                    result[
                        "arrival_time_error"
                    ]
                    for result
                    in self.interarrival_results
                )
                / interarrival_total
            )

        else:

            interarrival_mae = 0.0
            interarrival_rmse = 0.0
            mean_interarrival_error = 0.0

      
        # Setup metrics
        

        setup_total = len(
            self.setup_results
        )

        if setup_total > 0:

            setup_mae = (
                sum(
                    result[
                        "absolute_setup_time_error"
                    ]
                    for result
                    in self.setup_results
                )
                / setup_total
            )

            setup_mse = (
                sum(
                    result[
                        "squared_setup_time_error"
                    ]
                    for result
                    in self.setup_results
                )
                / setup_total
            )

            setup_rmse = math.sqrt(
                setup_mse
            )

            mean_setup_error = (
                sum(
                    result[
                        "setup_time_error"
                    ]
                    for result
                    in self.setup_results
                )
                / setup_total
            )

        else:

            setup_mae = 0.0
            setup_rmse = 0.0
            mean_setup_error = 0.0

        return {
            "evaluated_interarrivals":
                interarrival_total,

            "interarrival_mae":
                interarrival_mae,

            "interarrival_rmse":
                interarrival_rmse,

            "mean_interarrival_error":
                mean_interarrival_error,

            "evaluated_setups":
                setup_total,

            "setup_mae":
                setup_mae,

            "setup_rmse":
                setup_rmse,

            "mean_setup_error":
                mean_setup_error,
        }

   
    # Access Results
  

    def get_results(
        self,
    ):
        """
        Return all rolling prediction comparisons.
        """

        return self.results


    def get_latest_result(
        self,
    ):
        """
        Return the most recent completed prediction
        comparison.

        Returns None if no prediction has yet been
        evaluated.
        """

        if len(
            self.results
        ) == 0:

            return None

        return self.results[-1]

    
    # Drift-Eligible Results
   

    def get_drift_eligible_results(
        self,
    ):

        return [
            result
            for result in self.results
            if result[
                "drift_eligible"
            ]
        ]


    def get_latest_drift_eligible_result(
        self,
    ):

        for result in reversed(
            self.results
        ):

            if result[
                "drift_eligible"
            ]:

                return result

        return None


    def reset(
        self,
    ):

        self.active_prediction = None

        self.results = []

        self.prediction_counter = 0

        self.active_interarrival_prediction = None

        self.interarrival_results = []

        self.interarrival_prediction_counter = 0

        self.active_setup_prediction = None

        self.setup_results = []

        self.setup_prediction_counter = 0

    # Print Summary
    

    def print_summary(
        self,
    ):

        metrics = (
            self.get_metrics()
        )

        print("\n")
        print("=" * 60)
        print(
            "Rolling One-Step Prediction Validation"
        )
        print("=" * 60)

        print(
            f"Evaluated Predictions       : "
            f"{metrics['evaluated_predictions']}"
        )

        print(
            f"Correct States              : "
            f"{metrics['correct_states']}"
        )

        print(
            f"Incorrect States            : "
            f"{metrics['incorrect_states']}"
        )

        print(
            f"State Accuracy              : "
            f"{metrics['state_accuracy'] * 100:.2f}%"
        )

        print(
            f"Timing MAE                  : "
            f"{metrics['mae']:.2f} s"
        )

        print(
            f"Timing RMSE                 : "
            f"{metrics['rmse']:.2f} s"
        )

        print(
            f"Mean Signed Timing Error    : "
            f"{metrics['mean_timing_error']:+.2f} s"
        )

        print(
            f"Timing Accuracy ±1s        : "
            f"{metrics['timing_accuracy_1s'] * 100:.2f}%"
        )

        print(
            f"Timing Accuracy ±2s        : "
            f"{metrics['timing_accuracy_2s'] * 100:.2f}%"
        )

        print(
            f"Timing Accuracy ±5s        : "
            f"{metrics['timing_accuracy_5s'] * 100:.2f}%"
        )

        print(
            f"Median Absolute Timing Err : "
            f"{metrics['median_absolute_timing_error']:.2f} s"
        )

        print(
            f"Drift-Eligible Predictions  : "
            f"{metrics['drift_eligible_predictions']}"
        )

       
        # Additional Behaviour Metrics
        

        behaviour_metrics = (
            self.get_behaviour_metrics()
        )

        print(
            f"Inter-arrival Predictions   : "
            f"{behaviour_metrics['evaluated_interarrivals']}"
        )

        print(
            f"Inter-arrival MAE           : "
            f"{behaviour_metrics['interarrival_mae']:.2f} s"
        )

        print(
            f"Inter-arrival RMSE          : "
            f"{behaviour_metrics['interarrival_rmse']:.2f} s"
        )

        print(
            f"Mean Inter-arrival Error    : "
            f"{behaviour_metrics['mean_interarrival_error']:+.2f} s"
        )

        print(
            f"Setup Predictions           : "
            f"{behaviour_metrics['evaluated_setups']}"
        )

        print(
            f"Setup MAE                   : "
            f"{behaviour_metrics['setup_mae']:.2f} s"
        )

        print(
            f"Setup RMSE                  : "
            f"{behaviour_metrics['setup_rmse']:.2f} s"
        )

        print(
            f"Mean Setup Error            : "
            f"{behaviour_metrics['mean_setup_error']:+.2f} s"
        )


        # Per-Transition Research Metrics
        

        print("\n")
        print("=" * 60)
        print("Per-Transition Prediction Performance")
        print("=" * 60)

        for transition, transition_result in metrics[
            "transition_metrics"
        ].items():
            print(
                f"{transition[0]} -> {transition[1]}"
            )
            print(
                f"  Predictions              : "
                f"{transition_result['evaluated_predictions']}"
            )
            print(
                f"  State Accuracy            : "
                f"{transition_result['state_accuracy'] * 100:.2f}%"
            )
            print(
                f"  Timing MAE                : "
                f"{transition_result['mae']:.2f} s"
            )
            print(
                f"  Timing RMSE               : "
                f"{transition_result['rmse']:.2f} s"
            )
            print(
                f"  Timing Bias               : "
                f"{transition_result['mean_timing_error']:+.2f} s"
            )
            print(
                f"  Timing Accuracy ±1s       : "
                f"{transition_result['timing_accuracy_1s'] * 100:.2f}%"
            )
            print(
                f"  Timing Accuracy ±2s       : "
                f"{transition_result['timing_accuracy_2s'] * 100:.2f}%"
            )
            print(
                f"  Timing Accuracy ±5s       : "
                f"{transition_result['timing_accuracy_5s'] * 100:.2f}%"
            )
            print()

        

        print("\n")
        print("=" * 60)
        print(
            "Rolling Prediction Details"
        )
        print("=" * 60)

        for result in self.results:

            print(
                f"\nPrediction "
                f"{result['prediction_number']}"
            )

            print("-" * 40)

            print(
                f"Previous State  : "
                f"{result['current_state']}"
            )

            print(
                f"Predicted State : "
                f"{result['predicted_state']}"
            )

            print(
                f"Actual State    : "
                f"{result['actual_state']}"
            )

            print(
                f"State Correct   : "
                f"{result['state_correct']}"
            )

            print(
                f"Predicted Time  : "
                f"{result['predicted_time']:.2f} s"
            )

            print(
                f"Actual Time     : "
                f"{result['actual_time']:.2f} s"
            )

            print(
                f"Timing Error    : "
                f"{result['timing_error']:+.2f} s"
            )

            print(
                f"Absolute Error  : "
                f"{result['absolute_timing_error']:.2f} s"
            )

            print(
                f"Drift Eligible  : "
                f"{result['drift_eligible']}"
            )

      
        # Inter-arrival Prediction Details
      

        if self.interarrival_results:

            print("\n")
            print("=" * 60)
            print(
                "Inter-arrival Prediction Details"
            )
            print("=" * 60)

            for result in (
                self.interarrival_results
            ):

                print(
                    f"\nInter-arrival Prediction "
                    f"{result['prediction_number']}"
                )

                print("-" * 40)

                print(
                    f"Predicted Inter-arrival : "
                    f"{result['predicted_interarrival_time']:.2f} s"
                )

                print(
                    f"Predicted Arrival Time  : "
                    f"{result['predicted_arrival_time']:.2f} s"
                )

                print(
                    f"Actual Arrival Time     : "
                    f"{result['actual_arrival_time']:.2f} s"
                )

                print(
                    f"Arrival Time Error      : "
                    f"{result['arrival_time_error']:+.2f} s"
                )

                print(
                    f"Absolute Error          : "
                    f"{result['absolute_arrival_time_error']:.2f} s"
                )

        
        # Setup Prediction Details
        

        if self.setup_results:

            print("\n")
            print("=" * 60)
            print(
                "Setup Prediction Details"
            )
            print("=" * 60)

            for result in (
                self.setup_results
            ):

                print(
                    f"\nSetup Prediction "
                    f"{result['prediction_number']}"
                )

                print("-" * 40)

                print(
                    f"Predicted Setup Time     : "
                    f"{result['predicted_setup_time']:.2f} s"
                )

                print(
                    f"Actual Setup Time        : "
                    f"{result['actual_setup_time']:.2f} s"
                )

                print(
                    f"Setup Time Error         : "
                    f"{result['setup_time_error']:+.2f} s"
                )

                print(
                    f"Absolute Error           : "
                    f"{result['absolute_setup_time_error']:.2f} s"
                )

                print(
                    f"Job ID                   : "
                    f"{result['job_id']}"
                )