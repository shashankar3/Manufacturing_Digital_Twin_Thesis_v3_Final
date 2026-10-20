class PredictionValidator:

    def __init__(self):

       

        self.predictions = []

       

        self.actual_events = []

   
    # Prediction Recording
    

    def store_predictions(
        self,
        predictions,
    ):
       

        if predictions is None:

            self.predictions = []

            return

        self.predictions = list(
            predictions
        )

    
    # Actual Event Recording
    

    def record_event(
        self,
        event,
    ):
    

        self.actual_events.append(
            event
        )

   

    def _event_to_state(
        self,
        event,
    ):
        

        event_name = (
            event.event_type.name
        )

        

        if event_name == "SETUP_STARTED":

            return "SETUP"

        

        if event_name == "JOB_START":

            return "PROCESSING"

     

        if event_name == "JOB_COMPLETED":

            return "IDLE"

       

        if event_name == "FAILURE_DETECTED":

            return "FAULTED"

        

        if event_name == "REPAIR_STARTED":

            return "REPAIR"

        

        if event_name == "REPAIR_COMPLETED":

            return None

       

        return None


    def build_actual_trajectory(
        self,
    ):
        

        trajectory = []

        current_state = None
        pre_failure_state = None

        for event in self.actual_events:

            event_name = (
                event.event_type.name
            )


            if event_name == "SETUP_STARTED":

                state = "SETUP"
                current_state = state

            elif event_name == "JOB_START":

                state = "PROCESSING"
                current_state = state

            elif event_name == "JOB_COMPLETED":

                state = "IDLE"
                current_state = state

            elif event_name == "FAILURE_DETECTED":

                pre_failure_state = current_state
                state = "FAULTED"
                current_state = state

            elif event_name == "REPAIR_STARTED":

                state = "REPAIR"
                current_state = state

            elif event_name == "REPAIR_COMPLETED":

                if pre_failure_state is None:

                    continue

                state = pre_failure_state
                current_state = state
                pre_failure_state = None

            else:

                continue

            trajectory.append(
                {
                    "state":
                        state,

                    "transition_time":
                        float(
                            event.timestamp
                        ),

                    "event_type":
                        event.event_type.name,

                    "job_id":
                        event.job_id,
                }
            )

        return trajectory

   

    def build_actual_arrivals(
        self,
    ):
        

        arrivals = []

        for event in self.actual_events:

            event_name = (
                event.event_type.name
            )

            if event_name != "JOB_ARRIVAL":

                continue

            arrivals.append(
                {
                    "arrival_time":
                        float(
                            event.timestamp
                        ),

                    "job_id":
                        event.job_id,
                }
            )

        return arrivals



    def build_actual_interarrival_trajectory(
        self,
    ):


        arrivals = (
            self.build_actual_arrivals()
        )

        interarrivals = []

        if len(arrivals) < 2:

            return interarrivals

        for index in range(
            1,
            len(arrivals),
        ):

            previous_arrival = (
                arrivals[
                    index - 1
                ]
            )

            current_arrival = (
                arrivals[
                    index
                ]
            )

            interarrival_time = (
                current_arrival[
                    "arrival_time"
                ]
                -
                previous_arrival[
                    "arrival_time"
                ]
            )

            interarrivals.append(
                {
                    "interarrival_time":
                        interarrival_time,

                    "arrival_time":
                        current_arrival[
                            "arrival_time"
                        ],

                    "previous_arrival_time":
                        previous_arrival[
                            "arrival_time"
                        ],

                    "job_id":
                        current_arrival[
                            "job_id"
                        ],
                }
            )

        return interarrivals

  

    def build_actual_setup_trajectory(
        self,
    ):

        setup_starts = {}

        setup_trajectory = []

        for event in self.actual_events:

            event_name = (
                event.event_type.name
            )

            job_id = event.job_id

            if event_name == "SETUP_STARTED":

                setup_starts[job_id] = (
                    float(
                        event.timestamp
                    )
                )

            elif (
                event_name
                == "SETUP_COMPLETED"
            ):

                completed_time = float(
                    event.timestamp
                )

                if job_id not in setup_starts:

                    continue

                started_time = (
                    setup_starts[
                        job_id
                    ]
                )

                setup_time = (
                    completed_time
                    -
                    started_time
                )

                setup_trajectory.append(
                    {
                        "setup_time":
                            setup_time,

                        "setup_start_time":
                            started_time,

                        "setup_completed_time":
                            completed_time,

                        "job_id":
                            job_id,
                    }
                )

                del setup_starts[
                    job_id
                ]

        return setup_trajectory


    def _get_predicted_interarrival_time(
        self,
        prediction,
    ):


        if (
            prediction.get(
                "interarrival_time"
            )
            is not None
        ):

            return float(
                prediction[
                    "interarrival_time"
                ]
            )

        if (
            prediction.get(
                "predicted_interarrival_time"
            )
            is not None
        ):

            return float(
                prediction[
                    "predicted_interarrival_time"
                ]
            )

        return None


    def _get_predicted_setup_time(
        self,
        prediction,
    ):


        if (
            prediction.get(
                "setup_time"
            )
            is not None
        ):

            return float(
                prediction[
                    "setup_time"
                ]
            )

        if (
            prediction.get(
                "predicted_setup_time"
            )
            is not None
        ):

            return float(
                prediction[
                    "predicted_setup_time"
                ]
            )

        return None

   
    # Prediction Evaluation
    

    def evaluate(
        self,
    ):

        actual_trajectory = (
            self.build_actual_trajectory()
        )

        

        comparison_count = min(
            len(self.predictions),
            len(actual_trajectory),
        )

        comparisons = []

        correct_states = 0

        absolute_time_errors = []

       

        for index in range(
            comparison_count
        ):

            prediction = (
                self.predictions[index]
            )

            actual = (
                actual_trajectory[index]
            )

            predicted_state = (
                prediction[
                    "next_state"
                ]
            )

            actual_state = (
                actual[
                    "state"
                ]
            )

            predicted_time = float(
                prediction[
                    "transition_time"
                ]
            )

            actual_time = float(
                actual[
                    "transition_time"
                ]
            )

            

            state_correct = (
                predicted_state
                == actual_state
            )

            if state_correct:

                correct_states += 1

          

            time_error = (
                actual_time
                - predicted_time
            )

            absolute_time_error = abs(
                time_error
            )

            absolute_time_errors.append(
                absolute_time_error
            )


            drift_eligible = (
                state_correct
            )

          

            comparisons.append(
                {
                    "prediction_number":
                        index + 1,

                    "predicted_state":
                        predicted_state,

                    "actual_state":
                        actual_state,

                    "state_correct":
                        state_correct,

                    "predicted_time":
                        predicted_time,

                    "actual_time":
                        actual_time,

                    "time_error":
                        time_error,

                    "absolute_time_error":
                        absolute_time_error,

                    "drift_eligible":
                        drift_eligible,
                }
            )

        

        if comparison_count > 0:

            state_accuracy = (
                correct_states
                /
                comparison_count
            )

        else:

            state_accuracy = 0.0

       

        if absolute_time_errors:

            mean_absolute_time_error = (
                sum(
                    absolute_time_errors
                )
                /
                len(
                    absolute_time_errors
                )
            )

        else:

            mean_absolute_time_error = 0.0

       

        if comparison_count > 0:

            mean_timing_error = (
                sum(
                    comparison[
                        "time_error"
                    ]
                    for comparison
                    in comparisons
                )
                /
                comparison_count
            )

        else:

            mean_timing_error = 0.0

        

        drift_eligible_comparisons = [
            comparison
            for comparison in comparisons
            if comparison[
                "drift_eligible"
            ]
        ]

        

        interarrival_results = (
            self.evaluate_interarrival_predictions()
        )

        setup_results = (
            self.evaluate_setup_predictions()
        )

       

        timing_errors = [
            comparison["time_error"]
            for comparison in comparisons
        ]

        squared_time_errors = [
            error ** 2
            for error in timing_errors
        ]

        timing_evaluated = len(timing_errors)

        if timing_evaluated > 0:
            timing_rmse = math.sqrt(
                sum(squared_time_errors)
                / timing_evaluated
            )
            timing_within_1s = sum(
                error <= 1.0
                for error in (
                    abs(value)
                    for value in timing_errors
                )
            )
            timing_within_2s = sum(
                error <= 2.0
                for error in (
                    abs(value)
                    for value in timing_errors
                )
            )
            timing_within_5s = sum(
                error <= 5.0
                for error in (
                    abs(value)
                    for value in timing_errors
                )
            )
            timing_accuracy_1s = (
                timing_within_1s / timing_evaluated
            )
            timing_accuracy_2s = (
                timing_within_2s / timing_evaluated
            )
            timing_accuracy_5s = (
                timing_within_5s / timing_evaluated
            )
            sorted_errors = sorted(
                abs(value) for value in timing_errors
            )
            middle = len(sorted_errors) // 2
            if len(sorted_errors) % 2:
                median_absolute_time_error = (
                    sorted_errors[middle]
                )
            else:
                median_absolute_time_error = (
                    sorted_errors[middle - 1]
                    + sorted_errors[middle]
                ) / 2
        else:
            timing_rmse = 0.0
            timing_within_1s = 0
            timing_within_2s = 0
            timing_within_5s = 0
            timing_accuracy_1s = 0.0
            timing_accuracy_2s = 0.0
            timing_accuracy_5s = 0.0
            median_absolute_time_error = 0.0

      

        transition_metrics = {}

        for comparison in comparisons:
            transition = (
                comparison["predicted_state"],
                comparison["actual_state"],
            )
            entry = transition_metrics.setdefault(
                transition,
                {
                    "evaluated_predictions": 0,
                    "correct_states": 0,
                    "timing_errors": [],
                },
            )
            entry["evaluated_predictions"] += 1
            if comparison["state_correct"]:
                entry["correct_states"] += 1
            entry["timing_errors"].append(
                comparison["time_error"]
            )

        for entry in transition_metrics.values():
            count = entry["evaluated_predictions"]
            errors = entry["timing_errors"]
            entry["incorrect_states"] = (
                count - entry["correct_states"]
            )
            entry["state_accuracy"] = (
                entry["correct_states"] / count
                if count else 0.0
            )
            entry["mae"] = (
                sum(abs(error) for error in errors) / count
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
                sum(abs(error) <= 1.0 for error in errors) / count
                if count else 0.0
            )
            entry["timing_accuracy_2s"] = (
                sum(abs(error) <= 2.0 for error in errors) / count
                if count else 0.0
            )
            entry["timing_accuracy_5s"] = (
                sum(abs(error) <= 5.0 for error in errors) / count
                if count else 0.0
            )
            del entry["timing_errors"]

        

        return {
            "predicted_transitions":
                len(
                    self.predictions
                ),

            "actual_transitions":
                len(
                    actual_trajectory
                ),

            "compared_transitions":
                comparison_count,

            "correct_states":
                correct_states,

            "incorrect_states":
                (
                    comparison_count
                    - correct_states
                ),

            "state_accuracy":
                state_accuracy,

            "mean_absolute_time_error":
                mean_absolute_time_error,

            "mean_timing_error":
                mean_timing_error,

            "drift_eligible_transitions":
                len(
                    drift_eligible_comparisons
                ),

            "timing_evaluated_predictions":
                timing_evaluated,

            "timing_rmse":
                timing_rmse,

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

            "median_absolute_time_error":
                median_absolute_time_error,

            "transition_metrics":
                transition_metrics,

            "comparisons":
                comparisons,

            "actual_trajectory":
                actual_trajectory,

            "interarrival_evaluation":
                interarrival_results,

            "setup_evaluation":
                setup_results,
        }

    

    def evaluate_interarrival_predictions(
        self,
    ):


        actual_interarrivals = (
            self.build_actual_interarrival_trajectory()
        )

        comparisons = []

        absolute_errors = []

        squared_errors = []

        prediction_records = [
            prediction
            for prediction in self.predictions
            if (
                self._get_predicted_interarrival_time(
                    prediction
                )
                is not None
            )
        ]

        comparison_count = min(
            len(prediction_records),
            len(actual_interarrivals),
        )

        for index in range(
            comparison_count
        ):

            prediction = (
                prediction_records[index]
            )

            actual = (
                actual_interarrivals[index]
            )

            predicted_interarrival = (
                self._get_predicted_interarrival_time(
                    prediction
                )
            )

            actual_interarrival = (
                float(
                    actual[
                        "interarrival_time"
                    ]
                )
            )

            error = (
                actual_interarrival
                -
                predicted_interarrival
            )

            absolute_error = abs(
                error
            )

            squared_error = (
                error ** 2
            )

            absolute_errors.append(
                absolute_error
            )

            squared_errors.append(
                squared_error
            )

            comparisons.append(
                {
                    "prediction_number":
                        index + 1,

                    "predicted_interarrival_time":
                        predicted_interarrival,

                    "actual_interarrival_time":
                        actual_interarrival,

                    "error":
                        error,

                    "absolute_error":
                        absolute_error,

                    "squared_error":
                        squared_error,

                    "actual_arrival_time":
                        actual[
                            "arrival_time"
                        ],

                    "previous_arrival_time":
                        actual[
                            "previous_arrival_time"
                        ],

                    "job_id":
                        actual[
                            "job_id"
                        ],
                }
            )

        if comparison_count > 0:

            mae = (
                sum(
                    absolute_errors
                )
                / comparison_count
            )

            mse = (
                sum(
                    squared_errors
                )
                / comparison_count
            )

            rmse = (
                mse ** 0.5
            )

            mean_error = (
                sum(
                    comparison[
                        "error"
                    ]
                    for comparison
                    in comparisons
                )
                /
                comparison_count
            )

        else:

            mae = 0.0
            rmse = 0.0
            mean_error = 0.0

        return {
            "predicted_interarrivals":
                len(
                    prediction_records
                ),

            "actual_interarrivals":
                len(
                    actual_interarrivals
                ),

            "compared_interarrivals":
                comparison_count,

            "mae":
                mae,

            "rmse":
                rmse,

            "mean_error":
                mean_error,

            "comparisons":
                comparisons,

            "actual_trajectory":
                actual_interarrivals,
        }


    def evaluate_setup_predictions(
        self,
    ):

        actual_setups = (
            self.build_actual_setup_trajectory()
        )

        comparisons = []

        absolute_errors = []

        squared_errors = []

        prediction_records = [
            prediction
            for prediction in self.predictions
            if (
                self._get_predicted_setup_time(
                    prediction
                )
                is not None
            )
        ]

        comparison_count = min(
            len(prediction_records),
            len(actual_setups),
        )

        for index in range(
            comparison_count
        ):

            prediction = (
                prediction_records[index]
            )

            actual = (
                actual_setups[index]
            )

            predicted_setup_time = (
                self._get_predicted_setup_time(
                    prediction
                )
            )

            actual_setup_time = (
                float(
                    actual[
                        "setup_time"
                    ]
                )
            )

            error = (
                actual_setup_time
                -
                predicted_setup_time
            )

            absolute_error = abs(
                error
            )

            squared_error = (
                error ** 2
            )

            absolute_errors.append(
                absolute_error
            )

            squared_errors.append(
                squared_error
            )

            comparisons.append(
                {
                    "prediction_number":
                        index + 1,

                    "predicted_setup_time":
                        predicted_setup_time,

                    "actual_setup_time":
                        actual_setup_time,

                    "error":
                        error,

                    "absolute_error":
                        absolute_error,

                    "squared_error":
                        squared_error,

                    "setup_start_time":
                        actual[
                            "setup_start_time"
                        ],

                    "setup_completed_time":
                        actual[
                            "setup_completed_time"
                        ],

                    "job_id":
                        actual[
                            "job_id"
                        ],
                }
            )

        if comparison_count > 0:

            mae = (
                sum(
                    absolute_errors
                )
                /
                comparison_count
            )

            mse = (
                sum(
                    squared_errors
                )
                /
                comparison_count
            )

            rmse = (
                mse ** 0.5
            )

            mean_error = (
                sum(
                    comparison[
                        "error"
                    ]
                    for comparison
                    in comparisons
                )
                /
                comparison_count
            )

        else:

            mae = 0.0
            rmse = 0.0
            mean_error = 0.0

        return {
            "predicted_setups":
                len(
                    prediction_records
                ),

            "actual_setups":
                len(
                    actual_setups
                ),

            "compared_setups":
                comparison_count,

            "mae":
                mae,

            "rmse":
                rmse,

            "mean_error":
                mean_error,

            "comparisons":
                comparisons,

            "actual_trajectory":
                actual_setups,
        }


    def print_summary(
        self,
    ):
        

        results = (
            self.evaluate()
        )

        print("\n")

        print(
            "=" * 60
        )

        print(
            "Prediction Validation"
        )

        print(
            "=" * 60
        )

        print(
            f"Predicted Transitions : "
            f"{results['predicted_transitions']}"
        )

        print(
            f"Actual Transitions    : "
            f"{results['actual_transitions']}"
        )

        print(
            f"Compared Transitions  : "
            f"{results['compared_transitions']}"
        )

        print(
            f"Correct States        : "
            f"{results['correct_states']}"
        )

        print(
            f"Incorrect States      : "
            f"{results['incorrect_states']}"
        )

        print(
            f"State Accuracy        : "
            f"{results['state_accuracy'] * 100:.2f}%"
        )

        print(
            f"Mean Absolute "
            f"Timing Error          : "
            f"{results['mean_absolute_time_error']:.2f} s"
        )

        print(
            f"Mean Signed "
            f"Timing Error          : "
            f"{results['mean_timing_error']:+.2f} s"
        )

        print(
            f"Drift-Eligible "
            f"Transitions           : "
            f"{results['drift_eligible_transitions']}"
        )

       
        print(
            f"Timing RMSE           : "
            f"{results['timing_rmse']:.2f} s"
        )

        print(
            f"Timing Accuracy ±1s   : "
            f"{results['timing_accuracy_1s'] * 100:.2f}%"
        )

        print(
            f"Timing Accuracy ±2s   : "
            f"{results['timing_accuracy_2s'] * 100:.2f}%"
        )

        print(
            f"Timing Accuracy ±5s   : "
            f"{results['timing_accuracy_5s'] * 100:.2f}%"
        )

        print(
            f"Median Absolute Error  : "
            f"{results['median_absolute_time_error']:.2f} s"
        )


        interarrival = (
            results[
                "interarrival_evaluation"
            ]
        )

        print("\n")

        print(
            "=" * 60
        )

        print(
            "Inter-arrival Prediction Validation"
        )

        print(
            "=" * 60
        )

        print(
            f"Predicted Inter-arrivals : "
            f"{interarrival['predicted_interarrivals']}"
        )

        print(
            f"Actual Inter-arrivals    : "
            f"{interarrival['actual_interarrivals']}"
        )

        print(
            f"Compared Inter-arrivals  : "
            f"{interarrival['compared_interarrivals']}"
        )

        print(
            f"Inter-arrival MAE        : "
            f"{interarrival['mae']:.2f} s"
        )

        print(
            f"Inter-arrival RMSE       : "
            f"{interarrival['rmse']:.2f} s"
        )

        print(
            f"Mean Inter-arrival Error : "
            f"{interarrival['mean_error']:+.2f} s"
        )


        setup = (
            results[
                "setup_evaluation"
            ]
        )

        print("\n")

        print(
            "=" * 60
        )

        print(
            "Setup-Time Prediction Validation"
        )

        print(
            "=" * 60
        )

        print(
            f"Predicted Setups         : "
            f"{setup['predicted_setups']}"
        )

        print(
            f"Actual Setups            : "
            f"{setup['actual_setups']}"
        )

        print(
            f"Compared Setups          : "
            f"{setup['compared_setups']}"
        )

        print(
            f"Setup MAE                : "
            f"{setup['mae']:.2f} s"
        )

        print(
            f"Setup RMSE               : "
            f"{setup['rmse']:.2f} s"
        )

        print(
            f"Mean Setup Error         : "
            f"{setup['mean_error']:+.2f} s"
        )


        print("\n")
        print("=" * 60)
        print("Per-Transition Prediction Performance")
        print("=" * 60)

        for transition, metric in results[
            "transition_metrics"
        ].items():
            print(
                f"{transition[0]} -> {transition[1]}"
            )
            print(
                f"  Predictions        : "
                f"{metric['evaluated_predictions']}"
            )
            print(
                f"  State Accuracy     : "
                f"{metric['state_accuracy'] * 100:.2f}%"
            )
            print(
                f"  Timing MAE         : "
                f"{metric['mae']:.2f} s"
            )
            print(
                f"  Timing RMSE        : "
                f"{metric['rmse']:.2f} s"
            )
            print(
                f"  Timing Bias        : "
                f"{metric['mean_timing_error']:+.2f} s"
            )
            print(
                f"  Accuracy ±1s       : "
                f"{metric['timing_accuracy_1s'] * 100:.2f}%"
            )
            print(
                f"  Accuracy ±2s       : "
                f"{metric['timing_accuracy_2s'] * 100:.2f}%"
            )
            print(
                f"  Accuracy ±5s       : "
                f"{metric['timing_accuracy_5s'] * 100:.2f}%"
            )
            print()

      

        print("\n")

        print(
            "=" * 60
        )

        print(
            "Transition-by-Transition Comparison"
        )

        print(
            "=" * 60
        )

        for comparison in (
            results[
                "comparisons"
            ]
        ):

            print(
                f"\nTransition "
                f"{comparison['prediction_number']}"
            )

            print(
                "-" * 40
            )

            print(
                f"Predicted State : "
                f"{comparison['predicted_state']}"
            )

            print(
                f"Actual State    : "
                f"{comparison['actual_state']}"
            )

            print(
                f"State Correct   : "
                f"{comparison['state_correct']}"
            )

            print(
                f"Predicted Time  : "
                f"{comparison['predicted_time']:.2f} s"
            )

            print(
                f"Actual Time     : "
                f"{comparison['actual_time']:.2f} s"
            )

            print(
                f"Timing Error    : "
                f"{comparison['time_error']:+.2f} s"
            )

            print(
                f"Absolute Error  : "
                f"{comparison['absolute_time_error']:.2f} s"
            )

            print(
                f"Drift Eligible  : "
                f"{comparison['drift_eligible']}"
            )


        if (
            interarrival[
                "comparisons"
            ]
        ):

            print("\n")

            print(
                "=" * 60
            )

            print(
                "Inter-arrival-by-Inter-arrival Comparison"
            )

            print(
                "=" * 60
            )

            for comparison in (
                interarrival[
                    "comparisons"
                ]
            ):

                print(
                    f"\nInter-arrival "
                    f"{comparison['prediction_number']}"
                )

                print(
                    "-" * 40
                )

                print(
                    f"Predicted Inter-arrival : "
                    f"{comparison['predicted_interarrival_time']:.2f} s"
                )

                print(
                    f"Actual Inter-arrival    : "
                    f"{comparison['actual_interarrival_time']:.2f} s"
                )

                print(
                    f"Error                   : "
                    f"{comparison['error']:+.2f} s"
                )

                print(
                    f"Absolute Error           : "
                    f"{comparison['absolute_error']:.2f} s"
                )

                print(
                    f"Job ID                  : "
                    f"{comparison['job_id']}"
                )


        if (
            setup[
                "comparisons"
            ]
        ):

            print("\n")

            print(
                "=" * 60
            )

            print(
                "Setup-by-Setup Comparison"
            )

            print(
                "=" * 60
            )

            for comparison in (
                setup[
                    "comparisons"
                ]
            ):

                print(
                    f"\nSetup "
                    f"{comparison['prediction_number']}"
                )

                print(
                    "-" * 40
                )

                print(
                    f"Predicted Setup Time : "
                    f"{comparison['predicted_setup_time']:.2f} s"
                )

                print(
                    f"Actual Setup Time    : "
                    f"{comparison['actual_setup_time']:.2f} s"
                )

                print(
                    f"Error                : "
                    f"{comparison['error']:+.2f} s"
                )

                print(
                    f"Absolute Error       : "
                    f"{comparison['absolute_error']:.2f} s"
                )

                print(
                    f"Job ID               : "
                    f"{comparison['job_id']}"
                )