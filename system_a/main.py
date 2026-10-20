import simpy

from system_a.models.workstation import Workstation
from system_a.simulation.behaviour_engine import BehaviourEngine
from system_a.simulation.job_generator import JobGenerator
from system_a.simulation.worker_generator import WorkerGenerator

from system_b.digital_twin import DigitalTwin


def state_name(state):

    return getattr(
        state,
        "name",
        str(state),
    )


def percentage(value):
    return f"{value * 100:.2f}%"


def main():


    env = simpy.Environment()


    digital_twin = DigitalTwin()

    worker_generator = WorkerGenerator()

    workers = (
        worker_generator.get_workers()
    )

    worker_profiles = (
        worker_generator.get_worker_profiles()
    )

    behaviour_engine = BehaviourEngine(


        processing_time_mean=10.0,

        processing_time_std=1.0,

        drift_per_job=0.2,

        failure_probability=0.25,

        response_time_mean=2.0,

        response_time_std=0.4,

        repair_time_mean=3.0,

        repair_time_std=0.5,

        worker_profiles=worker_profiles,
    )


    workstation = Workstation(
        env=env,

        workstation_id="WS_01",

        behaviour_engine=behaviour_engine,

        workers=workers,

        worker_job_limit_sampler=(
            worker_generator
            .sample_worker_job_limit
        ),

        event_receiver=digital_twin,
    )

   
    # Job Generator - SYSTEM A

    job_generator = JobGenerator(
        env=env,

        workstation=workstation,

        min_interarrival_time=12.0,

        max_interarrival_time=24.0,
    )

 

    env.process(
        job_generator.generate_jobs()
    )

   

    TRAINING_TIME = 1000

    VALIDATION_END_TIME = TRAINING_TIME + 200

    WINDOW_SIZE = 20

   
    # TRAINING PHASE
    

    print()
    print("=" * 70)
    print("SYSTEM A + SYSTEM B")
    print("=" * 70)

    print()
    print("Training Phase")

    print(
        f"Training Time              : "
        f"{TRAINING_TIME:.2f} s"
    )

    print(
        f"Number of Workers          : "
        f"{len(workers)}"
    )

    print(
        f"Initial Worker             : "
        f"{workstation.active_worker.worker_id}"
    )

    print(
        "Inter-arrival Distribution : "
        "Uniform(12.0, 24.0)"
    )

    print(
        "Mean Inter-arrival Time    : "
        "18.0 s"
    )

    print()

    

    digital_twin.start_training()

   

    env.run(
        until=TRAINING_TIME
    )

    
    # TRAINING SUMMARY
   

    print()
    print("=" * 70)
    print("SYSTEM B - TRAINING COMPLETED")
    print("=" * 70)

    state = (
        digital_twin.get_operational_state()
    )

    behaviour = (
        digital_twin.get_behaviour_model()
    )

    print(
        f"Training Time              : "
        f"{TRAINING_TIME:.2f} s"
    )

    print(
        f"Machine State              : "
        f"{state_name(state.machine_state)}"
    )

    print(
        f"Digital Twin Time          : "
        f"{state.simulation_time:.2f} s"
    )

    print(
        f"Observed Jobs              : "
        f"{behaviour.observed_jobs}"
    )

    print(
        f"Observed Arrivals          : "
        f"{behaviour.observed_arrivals}"
    )

    print(
        f"Mean Processing Time       : "
        f"{behaviour.processing_mean:.2f} s"
    )

    print(
        f"Mean Idle Time             : "
        f"{behaviour.mean_idle_time:.2f} s"
    )

    print(
        f"Mean Queue Waiting Time    : "
        f"{behaviour.mean_waiting_time:.2f} s"
    )

    print(
        f"Mean Fault Response Time   : "
        f"{behaviour.mean_fault_response_time:.2f} s"
    )

    print(
        f"Mean Repair Time           : "
        f"{behaviour.mean_repair_time:.2f} s"
    )

    
    # LEARNED MARKOV MODEL
    

    print()
    print("=" * 70)
    print("SYSTEM B - LEARNED MARKOV TRANSITIONS")
    print("=" * 70)

    markov = (
        digital_twin.behaviour_estimator
        .get_markov_chain()
    )

    if len(markov.transition_counts) == 0:

        print(
            "No transitions learned."
        )

    else:

        for (
            current_state,
            next_state
        ), count in markov.transition_counts.items():

            print(
                f"{state_name(current_state):12s} -> "
                f"{state_name(next_state):12s} : "
                f"{count}"
            )


        print()
        print("-" * 70)
        print("LEARNED TRANSITION PROBABILITIES")
        print("-" * 70)

        for current_state in sorted(
            {
                transition[0]
                for transition in markov.transition_counts
            },
            key=lambda state: state_name(state),
        ):

            outgoing = {
                next_state: count
                for (
                    state,
                    next_state
                ), count in markov.transition_counts.items()
                if state == current_state
            }

            total = sum(
                outgoing.values()
            )

            if total <= 0:
                continue

            print()
            print(
                f"{state_name(current_state)}"
            )

            for next_state in sorted(
                outgoing,
                key=lambda state: state_name(state),
            ):

                probability = (
                    outgoing[next_state]
                    / total
                )

                print(
                    f"  -> {state_name(next_state):12s} : "
                    f"{probability:.4f} "
                    f"(count={outgoing[next_state]})"
                )

    # START SLIDING-WINDOW ADAPTIVE VALIDATION
   

    print()
    print("=" * 70)
    print("SYSTEM B - STARTING ADAPTIVE VALIDATION")
    print("=" * 70)

    digital_twin.start_sliding_window_adaptive_validation(
        window_size=WINDOW_SIZE
    )

    print(
        f"Sliding Window Size       : "
        f"{WINDOW_SIZE}"
    )

    print(
        "Rolling Prediction         : ENABLED"
    )

    print(
        "State Validation           : ENABLED"
    )

    print(
        "Timing CUSUM               : ENABLED"
    )

    print(
        "Sliding-Window Adaptation  : ENABLED"
    )

    print(
        "Bayesian Prediction Bias   : DISABLED"
    )


    initial_prediction = (
        digital_twin.start_rolling_prediction()
    )

    if initial_prediction is None:

        print()
        print(
            "Initial prediction could not "
            "be generated."
        )

    else:

        print()
        print("=" * 70)
        print("SYSTEM B - INITIAL ONE-STEP PREDICTION")
        print("=" * 70)

        print(
            f"Current State   : "
            f"{initial_prediction['current_state']}"
        )

        print(
            f"Holding Time    : "
            f"{initial_prediction['holding_time']:.2f} s"
        )

        print(
            f"Next State      : "
            f"{initial_prediction['next_state']}"
        )

        print(
            f"Transition Time : "
            f"{initial_prediction['transition_time']:.2f} s"
        )

        if (
            initial_prediction.get(
                "setup_time"
            )
            is not None
        ):

            print(
                f"Predicted Setup : "
                f"{initial_prediction['setup_time']:.2f} s"
            )

   
    # ADAPTIVE VALIDATION PHASE
    

    print()
    print("=" * 70)
    print("SYSTEM B - ADAPTIVE VALIDATION PHASE")
    print("=" * 70)

    print(
        f"Validation interval        : "
        f"{TRAINING_TIME:.2f} -> "
        f"{VALIDATION_END_TIME:.2f} s"
    )

    print(
        f"Behaviour Window Size     : "
        f"{WINDOW_SIZE} observations"
    )

    env.run(
        until=VALIDATION_END_TIME
    )


    digital_twin.stop_rolling_prediction()


    print()
    print("=" * 70)
    print("SYSTEM B - FINAL DIGITAL TWIN STATE")
    print("=" * 70)

    state = (
        digital_twin.get_operational_state()
    )

    print(
        f"Machine State              : "
        f"{state_name(state.machine_state)}"
    )

    print(
        f"Simulation Time             : "
        f"{state.simulation_time:.2f} s"
    )

    print(
        f"Operating Mode              : "
        f"{digital_twin.get_mode()}"
    )

    print(
        f"Total Observable Events     : "
        f"{len(workstation.event_log)}"
    )

    print(
        f"Sliding Window Enabled      : "
        f"{digital_twin.is_sliding_window_enabled()}"
    )

    print(
        f"Sliding Window Size         : "
        f"{digital_twin.get_sliding_window_size()}"
    )

    print(
        f"Adaptation Enabled          : "
        f"{digital_twin.is_adaptation_enabled()}"
    )

    
    # FINAL BEHAVIOUR MODEL
   

    print()
    print("=" * 70)
    print("SYSTEM B - CURRENT BEHAVIOUR MODEL")
    print("=" * 70)

    behaviour = (
        digital_twin.get_behaviour_model()
    )

    print(
        f"Observed Jobs              : "
        f"{behaviour.observed_jobs}"
    )

    print(
        f"Observed Arrivals          : "
        f"{behaviour.observed_arrivals}"
    )

    print(
        f"Mean Inter-arrival Time    : "
        f"{behaviour.mean_interarrival_time:.2f} s"
    )

    print(
        f"Mean Setup Time            : "
        f"{behaviour.mean_setup_time:.2f} s"
    )

    print(
        f"Mean Processing Time       : "
        f"{behaviour.processing_mean:.2f} s"
    )

    print(
        f"Mean Idle Time             : "
        f"{behaviour.mean_idle_time:.2f} s"
    )

    print(
        f"Mean Queue Waiting Time    : "
        f"{behaviour.mean_waiting_time:.2f} s"
    )

    print(
        f"Mean Fault Response Time   : "
        f"{behaviour.mean_fault_response_time:.2f} s"
    )

    print(
        f"Mean Repair Time           : "
        f"{behaviour.mean_repair_time:.2f} s"
    )

    
    # WORKER ESTIMATION
    

    if hasattr(
        behaviour,
        "worker_behaviours",
    ):

        print()
        print("=" * 70)
        print("SYSTEM B - LEARNED WORKER MODELS")
        print("=" * 70)

        if not behaviour.worker_behaviours:

            print(
                "No worker-conditioned models "
                "have been learned yet."
            )

        else:

            for (
                worker_id,
                worker_model,
            ) in sorted(
                behaviour.worker_behaviours.items()
            ):

                print()
                print(
                    f"Worker: {worker_id}"
                )

                print(
                    f"  Observed Setups       : "
                    f"{worker_model.observed_setups}"
                )

                print(
                    f"  Mean Setup Time       : "
                    f"{worker_model.mean_setup_time:.2f} s"
                )

                print(
                    f"  Observed Processing    : "
                    f"{worker_model.observed_processing_cycles}"
                )

                print(
                    f"  Mean Processing Time  : "
                    f"{worker_model.processing_mean:.2f} s"
                )

                print(
                    f"  Observed Faults       : "
                    f"{worker_model.observed_fault_responses}"
                )

                print(
                    f"  Mean Fault Response   : "
                    f"{worker_model.mean_fault_response_time:.2f} s"
                )

                print(
                    f"  Observed Repairs      : "
                    f"{worker_model.observed_repairs}"
                )

                print(
                    f"  Mean Repair Time      : "
                    f"{worker_model.mean_repair_time:.2f} s"
                )

   
    # ROLLING PREDICTION RESULTS
    

    online_evaluator = (
        digital_twin
        .get_online_prediction_evaluator()
    )

    online_evaluator.print_summary()


    prediction_metrics = (
        digital_twin.get_prediction_results()
    )

    print()
    print("=" * 70)
    print("THESIS RESEARCH RESULTS - SYSTEM B")
    print("=" * 70)

    
    # 1. OVERALL PREDICTION PERFORMANCE
   

    print()
    print("OVERALL PREDICTION PERFORMANCE")
    print("-" * 70)

    print(
        f"State Predictions          : "
        f"{prediction_metrics.get('evaluated_predictions', 0)}"
    )
    print(
        f"Correct State Predictions  : "
        f"{prediction_metrics.get('correct_states', 0)}"
    )
    print(
        f"State Prediction Accuracy  : "
        f"{percentage(prediction_metrics.get('state_accuracy', 0.0))}"
    )
    print(
        f"Timing Evaluations         : "
        f"{prediction_metrics.get('timing_evaluated_predictions', 0)}"
    )
    print(
        f"Timing MAE                 : "
        f"{prediction_metrics.get('mae', 0.0):.2f} s"
    )
    print(
        f"Timing RMSE                : "
        f"{prediction_metrics.get('rmse', 0.0):.2f} s"
    )
    print(
        f"Timing Bias                : "
        f"{prediction_metrics.get('mean_timing_error', 0.0):+.2f} s"
    )
    print(
        f"Timing Accuracy +/-1s      : "
        f"{percentage(prediction_metrics.get('timing_accuracy_1s', 0.0))}"
    )
    print(
        f"Timing Accuracy +/-2s      : "
        f"{percentage(prediction_metrics.get('timing_accuracy_2s', 0.0))}"
    )
    print(
        f"Timing Accuracy +/-5s      : "
        f"{percentage(prediction_metrics.get('timing_accuracy_5s', 0.0))}"
    )
    print(
        f"Median Absolute Error      : "
        f"{prediction_metrics.get('median_absolute_timing_error', 0.0):.2f} s"
    )

   
    # 2. PER-TRANSITION PERFORMANCE
    

    print()
    print("PER-TRANSITION PERFORMANCE")
    print("-" * 70)

    transition_metrics = prediction_metrics.get(
        "transition_metrics",
        {},
    )

    if not transition_metrics:
        print("No transition-level metrics available.")
    else:
        for transition, metric in sorted(
            transition_metrics.items(),
            key=lambda item: (
                str(item[0][0]),
                str(item[0][1]),
            ),
        ):
            print(
                f"{state_name(transition[0])} -> "
                f"{state_name(transition[1])}"
            )
            print(
                f"  State Accuracy : "
                f"{percentage(metric.get('state_accuracy', 0.0))}"
            )
            print(
                f"  Timing MAE     : "
                f"{metric.get('mae', 0.0):.2f} s"
            )
            print(
                f"  Timing RMSE    : "
                f"{metric.get('rmse', 0.0):.2f} s"
            )
            print(
                f"  Timing Bias    : "
                f"{metric.get('mean_timing_error', 0.0):+.2f} s"
            )

    
    # 3. WORKER CHARACTERISTIC RECOVERY
    

    print()
    print("WORKER CHARACTERISTIC RECOVERY")
    print("-" * 70)
    print(
        "System A = hidden ground truth | "
        "System B = learned estimate"
    )
    print()

    worker_models = getattr(
        behaviour,
        "worker_behaviours",
        {},
    )

    
    # System A realized worker-conditioned processing means
    
    system_a_worker_processing_samples = {}

    processing_starts = {}

    for event in getattr(
        workstation,
        "event_log",
        [],
    ):
        event_type = getattr(
            getattr(event, "event_type", None),
            "value",
            str(getattr(event, "event_type", "")),
        )
        worker_id = getattr(
            event,
            "worker_id",
            None,
        )
        job_id = getattr(
            event,
            "job_id",
            None,
        )
        timestamp = getattr(
            event,
            "timestamp",
            None,
        )

        if (
            event_type == "JOB_START"
            and worker_id is not None
            and job_id is not None
            and timestamp is not None
        ):
            processing_starts[job_id] = (
                worker_id,
                float(timestamp),
            )

        elif (
            event_type == "JOB_COMPLETED"
            and job_id is not None
            and timestamp is not None
        ):
            start_record = processing_starts.pop(
                job_id,
                None,
            )

            if start_record is not None:
                start_worker, start_time = start_record
                duration = float(timestamp) - start_time

                if duration >= 0.0:
                    system_a_worker_processing_samples.setdefault(
                        start_worker,
                        [],
                    ).append(duration)

    system_a_worker_processing_means = {
        worker_id: (
            sum(samples) / len(samples)
            if samples
            else None
        )
        for worker_id, samples in (
            system_a_worker_processing_samples.items()
        )
    }

    if not worker_profiles:
        print("No System A worker ground truth available.")
    elif not worker_models:
        print("No System B worker-conditioned models learned.")
    else:
        print(
            f"{'Worker':<10}"
            f"{'Characteristic':<20}"
            f"{'System A':>14}"
            f"{'System B':>14}"
            f"{'Abs. Error':>14}"
        )
        print("-" * 72)

        worker_characteristic_specs = (
            (
                "setup_mean",
                "Setup Mean",
                "setup_mean",
            ),
            (
                "processing_mean",
                "Processing Mean",
                "system_a_realized_processing_mean",
            ),
            (
                "fault_response_mean",
                "Fault Response Mean",
                "repair_response_mean",
            ),
            (
                "repair_mean",
                "Repair Mean",
                "repair_adjustment_mean",
            ),
        )

        worker_errors = {
            "setup_mean": [],
            "processing_mean": [],
            "fault_response_mean": [],
            "repair_mean": [],
        }

        for worker_id in sorted(
            worker_profiles,
            key=lambda value: str(value),
        ):
            profile = worker_profiles[
                worker_id
            ]
            worker_model = worker_models.get(
                worker_id
            )

            if worker_model is None:
                continue

            learned_values = {
                "setup_mean": (
                    worker_model.mean_setup_time
                ),
                "processing_mean": (
                    worker_model.processing_mean
                ),
                "fault_response_mean": (
                    worker_model.mean_fault_response_time
                ),
                "repair_mean": (
                    worker_model.mean_repair_time
                ),
            }

            for key, label, truth_key in (
                worker_characteristic_specs
            ):
                if truth_key == "system_a_realized_processing_mean":
                    true_value = (
                        system_a_worker_processing_means.get(
                            worker_id
                        )
                    )
                else:
                    true_value = profile.get(
                        truth_key
                    )
                learned_value = learned_values[
                    key
                ]

                if (
                    true_value is None
                    or learned_value is None
                ):
                    continue

                try:
                    error = abs(
                        float(learned_value)
                        - float(true_value)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                worker_errors[key].append(
                    error
                )

                print(
                    f"{str(worker_id):<10}"
                    f"{label:<20}"
                    f"{float(true_value):>14.3f}"
                    f"{float(learned_value):>14.3f}"
                    f"{error:>14.3f}"
                )

        print()
        print("WORKER CHARACTERISTIC MAE")
        for key, label, _ in (
            worker_characteristic_specs
        ):
            errors = worker_errors[key]
            mae = (
                sum(errors) / len(errors)
                if errors
                else 0.0
            )
            print(
                f"  {label:<24}: "
                f"{mae:.3f} s"
            )

    
    # TRANSITION DRIFT DETECTION
    

    adaptation_manager = (
        digital_twin.get_adaptation_manager()
    )

    transition_drift_summary = (
        adaptation_manager.get_transition_drift_summary()
    )
   
    detected_transition_drifts = int(
        transition_drift_summary.get(
            "detected_drifts",
            0,
        )
    )

    print()
    print("POINT 3 - TRANSITION DRIFT DETECTION")
    print("-" * 70)

    print(
        f"Transition Observations     : "
        f"{len(adaptation_manager.get_transition_monitoring_history())}"
    )
    print(
        f"Detected State Drifts       : "
        f"{detected_transition_drifts}"
    )

    detector_status = transition_drift_summary.get(
        "detector",
        {},
    )

    if detector_status:
        print(
            f"Reference K                 : "
            f"{detector_status.get('reference_value', 'n/a')}"
        )
        print(
            f"Threshold H                 : "
            f"{detector_status.get('threshold', 'n/a')}"
        )
        print(
            f"Current CUSUM               : "
            f"{detector_status.get('cusum', 'n/a')}"
        )

    transition_history = (
        adaptation_manager.get_transition_monitoring_history()
    )

    if transition_history:
        print()
        print("RECENT TRANSITION-SURPRISE OBSERVATIONS")
        for record in transition_history[-10:]:
            current = record.get(
                "current_state",
                "?",
            )
            nxt = record.get(
                "next_state",
                "?",
            )
            probability = record.get(
                "probability"
            )
            surprise = record.get(
                "surprise"
            )
            cusum = record.get(
                "cusum"
            )
            detected = record.get(
                "drift_detected",
                False,
            )

            print(
                f"  {state_name(current)} -> "
                f"{state_name(nxt)} | "
                f"P={probability if probability is not None else 'n/a'} | "
                f"z={surprise if surprise is not None else 'n/a'} | "
                f"CUSUM={cusum if cusum is not None else 'n/a'} | "
                f"Drift={detected}"
            )
    else:
        print("No transition-surprise history available.")

   
    # 5. TIMING CUSUM DRIFT REPORT
    

    timing_transition_summary = (
        adaptation_manager.get_transition_summary()
    )

    print()
    print("TIMING CUSUM DRIFT REPORT")
    print("-" * 70)
    print("CUSUM Type                  : Two-sided timing CUSUM")

    timing_k = None
    timing_h = None

    for summary in timing_transition_summary.values():
        cusum = summary.get("cusum", {})
        detector = adaptation_manager.get_drift_detector(
            summary.get("cusum", {}).get("transition", (None, None))[0],
            summary.get("cusum", {}).get("transition", (None, None))[1],
        )
        if detector is not None:
            timing_k = getattr(detector, "reference_value", None)
            timing_h = getattr(detector, "threshold", None)
            break

    if timing_k is None or timing_h is None:
        
        for summary in timing_transition_summary.values():
            detector = adaptation_manager.get_drift_detector(
                summary.get("cusum", {}).get("transition", (None, None))[0],
                summary.get("cusum", {}).get("transition", (None, None))[1],
            )
            if detector is not None:
                timing_k = getattr(detector, "reference_value", None)
                timing_h = getattr(detector, "threshold", None)
                break

    print(
        f"Reference K                 : "
        f"{timing_k if timing_k is not None else 'n/a'}"
    )
    print(
        f"Threshold H                 : "
        f"{timing_h if timing_h is not None else 'n/a'}"
    )
    print()

    timing_total_errors = 0
    timing_total_drifts = 0
    timing_total_updates = 0

    for transition, summary in sorted(
        timing_transition_summary.items(),
        key=lambda item: (str(item[0][0]), str(item[0][1])),
    ):
        observed_errors = int(summary.get("observed_errors", 0) or 0)
        detected_drifts = int(summary.get("detected_drifts", 0) or 0)
        model_updates = int(summary.get("model_updates", 0) or 0)
        cusum = summary.get("cusum", {}) or {}

        timing_total_errors += observed_errors
        timing_total_drifts += detected_drifts
        timing_total_updates += model_updates

        
        print(
            f"{state_name(transition[0])} -> "
            f"{state_name(transition[1])}"
        )
        print(
            f"  Eligible Errors       : {observed_errors}"
        )
        print(
            f"  Detected Drifts       : {detected_drifts}"
        )
        print(
            f"  Model Updates         : {model_updates}"
        )
        print(
            f"  Positive CUSUM        : "
            f"{cusum.get('positive_cusum', 0.0):.4f}"
        )
        print(
            f"  Negative CUSUM        : "
            f"{cusum.get('negative_cusum', 0.0):.4f}"
        )
        print(
            f"  Last Drift Direction  : "
            f"{cusum.get('last_drift_direction') or 'None'}"
        )
        print()

    print("TIMING CUSUM TOTALS")
    print("-" * 70)
    print(
        f"Total Eligible Errors       : {timing_total_errors}"
    )
    print(
        f"Total Detected Drifts       : {timing_total_drifts}"
    )
    print(
        f"Total Model Updates         : {timing_total_updates}"
    )

    # 6. BEHAVIOURAL-CHANNEL CUSUM REPORT
  

    behaviour_cusum_summary = (
        adaptation_manager.get_behaviour_summary()
    )

    print()
    print("BEHAVIOURAL-CHANNEL CUSUM REPORT")
    print("-" * 70)

    for channel, summary in sorted(
        behaviour_cusum_summary.items(),
        key=lambda item: str(item[0]),
    ):
        cusum = summary.get("cusum", {}) or {}
        print(f"Channel: {channel}")
        print(
            f"  Eligible Errors       : "
            f"{summary.get('observed_errors', 0)}"
        )
        print(
            f"  Detected Drifts       : "
            f"{summary.get('detected_drifts', 0)}"
        )
        print(
            f"  Model Updates         : "
            f"{summary.get('model_updates', 0)}"
        )
        print(
            f"  Positive CUSUM        : "
            f"{cusum.get('positive_cusum', 0.0):.4f}"
        )
        print(
            f"  Negative CUSUM        : "
            f"{cusum.get('negative_cusum', 0.0):.4f}"
        )
        print(
            f"  Last Drift Direction  : "
            f"{cusum.get('last_drift_direction') or 'None'}"
        )
        print()

    
    # 7.  PARALLEL ADAPTATION BENCHMARK
    

    transition_adaptation_summary = (
        adaptation_manager.get_transition_adaptation_summary()
    )

    evaluation = (
        transition_adaptation_summary.get(
            "evaluation",
            {},
        )
    )

    sliding = evaluation.get(
        "sliding_window",
        {},
    )
    bayesian = evaluation.get(
        "bayesian",
        {},
    )

    print()
    print("POINT 4 - PARALLEL ADAPTATION BENCHMARK")
    print("-" * 70)
    print(
        f"{'Metric':<30}"
        f"{'Sliding Window':>20}"
        f"{'Bayesian':>20}"
    )
    print("-" * 70)

    print(
        f"{'Evaluated Predictions':<30}"
        f"{sliding.get('evaluated_predictions', 0):>20}"
        f"{bayesian.get('evaluated_predictions', 0):>20}"
    )
    print(
        f"{'Correct Predictions':<30}"
        f"{sliding.get('correct_predictions', 0):>20}"
        f"{bayesian.get('correct_predictions', 0):>20}"
    )
    print(
        f"{'State Accuracy':<30}"
        f"{percentage(sliding.get('state_accuracy', 0.0)):>20}"
        f"{percentage(bayesian.get('state_accuracy', 0.0)):>20}"
    )

    print()
    print(
        f"Adaptation Events            : "
        f"{transition_adaptation_summary.get('adaptation_count', 0)}"
    )

   
    # 6. ADAPTATION EFFECT
    

    print()
    print("ADAPTATION EFFECT ON PREDICTION ERROR")
    print("-" * 70)

    prediction_results = getattr(
        online_evaluator,
        "results",
        [],
    )

    adaptation_history = (
        adaptation_manager.get_transition_adaptation_history()
    )

    adaptation_timestamps = []

    for record in adaptation_history:
        for key in (
            "timestamp",
            "event_timestamp",
            "time",
        ):
            value = record.get(key)
            if isinstance(value, (int, float)):
                adaptation_timestamps.append(float(value))
                break

    first_adaptation_time = (
        min(adaptation_timestamps)
        if adaptation_timestamps
        else None
    )

    
    adaptation_prediction_boundary = None

    if adaptation_history:
        boundary_candidates = [
            record.get("history_size")
            for record in adaptation_history
            if isinstance(record.get("history_size"), int)
        ]
        if boundary_candidates:
            adaptation_prediction_boundary = min(
                boundary_candidates
            )

    before_errors = []
    after_errors = []

    for result in prediction_results:
        error = result.get(
            "absolute_timing_error"
        )
        timestamp = result.get(
            "actual_time"
        )

        if error is None:
            continue

        prediction_index = result.get(
            "prediction_number",
            result.get("index"),
        )

        if first_adaptation_time is not None and isinstance(
            timestamp,
            (int, float),
        ):
            is_before = timestamp < first_adaptation_time
        elif (
            adaptation_prediction_boundary is not None
            and isinstance(prediction_index, int)
        ):
            is_before = (
                prediction_index
                <= adaptation_prediction_boundary
            )
        else:
            
            is_before = True

        if is_before:
            before_errors.append(float(error))
        else:
            after_errors.append(float(error))

    def mean_error(values):
        return (
            sum(values) / len(values)
            if values
            else None
        )

    def rmse_error(values):
        return (
            (
                sum(
                    value * value
                    for value in values
                )
                / len(values)
            ) ** 0.5
            if values
            else None
        )

    before_mae = mean_error(
        before_errors
    )
    after_mae = mean_error(
        after_errors
    )
    before_rmse = rmse_error(
        before_errors
    )
    after_rmse = rmse_error(
        after_errors
    )

    if first_adaptation_time is not None:
        baseline_label = str(first_adaptation_time)
    elif adaptation_prediction_boundary is not None:
        baseline_label = (
            f"prediction/history boundary "
            f"{adaptation_prediction_boundary}"
        )
    else:
        baseline_label = "n/a"

    print(
        f"Adaptation Baseline Point    : "
        f"{baseline_label}"
    )

    print(
        f"Before - Timing MAE          : "
        f"{before_mae:.2f} s"
        if before_mae is not None
        else "Before - Timing MAE          : n/a"
    )
    print(
        f"Before - Timing RMSE         : "
        f"{before_rmse:.2f} s"
        if before_rmse is not None
        else "Before - Timing RMSE         : n/a"
    )
    print(
        f"After  - Timing MAE          : "
        f"{after_mae:.2f} s"
        if after_mae is not None
        else "After  - Timing MAE          : n/a"
    )
    print(
        f"After  - Timing RMSE         : "
        f"{after_rmse:.2f} s"
        if after_rmse is not None
        else "After  - Timing RMSE         : n/a"
    )

    if (
        before_mae is not None
        and after_mae is not None
        and before_mae > 0
    ):
        mae_improvement = (
            (
                before_mae
                - after_mae
            )
            / before_mae
        )
        print(
            f"Timing MAE Improvement       : "
            f"{percentage(mae_improvement)}"
        )

    if (
        before_rmse is not None
        and after_rmse is not None
        and before_rmse > 0
    ):
        rmse_improvement = (
            (
                before_rmse
                - after_rmse
            )
            / before_rmse
        )
        print(
            f"Timing RMSE Improvement      : "
            f"{percentage(rmse_improvement)}"
        )

   
    # 7. SIM2REAL FIDELITY SUMMARY
    

    print()
    print("SIM2REAL FIDELITY SUMMARY")
    print("-" * 70)
    print(
        "System B is evaluated on its ability to infer "
        "System A behaviour from observable events, "
        "detect persistent changes, and adapt its "
        "predictive model."
    )
    print(
        f"State Prediction Accuracy    : "
        f"{percentage(prediction_metrics.get('state_accuracy', 0.0))}"
    )
    print(
        f"Timing MAE                   : "
        f"{prediction_metrics.get('mae', 0.0):.2f} s"
    )
    print(
        f"Timing RMSE                  : "
        f"{prediction_metrics.get('rmse', 0.0):.2f} s"
    )
    print(
        f"Point 3 State Drifts Detected : "
        f"{detected_transition_drifts}"
    )
    timing_cusum_drifts = adaptation_manager.get_detected_drifts()
    timing_model_updates = adaptation_manager.get_model_updates()
    print(
        f"Timing CUSUM Drifts Detected  : "
        f"{timing_cusum_drifts}"
    )
    print(
        f"Timing Model Updates          : "
        f"{timing_model_updates}"
    )
    print(
        f"Point 4 Adaptation Events     : "
        f"{transition_adaptation_summary.get('adaptation_count', 0)}"
    )
    print(
        f"Sliding Window Accuracy      : "
        f"{percentage(sliding.get('state_accuracy', 0.0))}"
    )
    print(
        f"Bayesian Accuracy             : "
        f"{percentage(bayesian.get('state_accuracy', 0.0))}"
    )

   
    # END RESEARCH RESULTS REPORT

    print()
    print("=" * 70)
    print("SYSTEM B - ADAPTIVE SYNCHRONIZATION")
    print("=" * 70)

    adaptation_summary = (
        digital_twin.get_adaptation_summary()
    )

    print(
        f"Adaptation Enabled : "
        f"{adaptation_manager.is_enabled()}"
    )

    print(
        "Architecture       : "
        "Transition-specific CUSUM + "
        "behavioural adaptation"
    )

    total_observed_errors = 0

    total_detected_drifts = 0

    total_model_updates = 0

    for (
        transition,
        summary,
    ) in adaptation_summary.items():

        current_state = transition[0]

        next_state = transition[1]

        transition_name = (
            f"{current_state} -> "
            f"{next_state}"
        )

        print()
        print("-" * 70)
        print(
            f"Transition: {transition_name}"
        )
        print("-" * 70)

        observed_errors = (
            summary.get(
                "observed_errors",
                0,
            )
        )

        detected_drifts = (
            summary.get(
                "detected_drifts",
                0,
            )
        )

        model_updates = (
            summary.get(
                "model_updates",
                0,
            )
        )

        total_observed_errors += (
            observed_errors
        )

        total_detected_drifts += (
            detected_drifts
        )

        total_model_updates += (
            model_updates
        )

        print(
            f"Eligible Errors       : "
            f"{observed_errors}"
        )

        print(
            f"Detected Drifts       : "
            f"{detected_drifts}"
        )

        print(
            f"Model Updates         : "
            f"{model_updates}"
        )

    
    # ADAPTATION TOTALS
   

    print()
    print("=" * 70)
    print("SYSTEM B - ADAPTATION TOTALS")
    print("=" * 70)

    print(
        f"Total Eligible Errors  : "
        f"{total_observed_errors}"
    )

    print(
        f"Total Detected Drifts  : "
        f"{total_detected_drifts}"
    )

    print(
        f"Total Model Updates    : "
        f"{total_model_updates}"
    )

    # FINAL SYSTEM A EVENT SUMMARY

    print()
    print("=" * 70)
    print("SYSTEM A - OBSERVABLE EVENT SUMMARY")
    print("=" * 70)

    print()

    print(
        "Events Generated:",
        len(workstation.event_log),
    )

    print(
        "Jobs Generated:",
        job_generator.job_counter,
    )

    print(
        "Jobs Completed by Current Worker:",
        workstation.jobs_completed_by_worker,
    )

    print(
        "Current Worker:",
        workstation.active_worker.worker_id,
    )

    print(
        "Current Worker Job Limit:",
        workstation.worker_job_limit,
    )

    print()


    event_counts = {}

    for event in workstation.event_log:

        event_name = (
            event.event_type.value
        )

        event_counts[event_name] = (
            event_counts.get(
                event_name,
                0,
            )
            + 1
        )

    print("EVENT COUNTS")
    print("-" * 70)

    for (
        event_name,
        count,
    ) in sorted(
        event_counts.items()
    ):

        print(
            f"{event_name:<30}"
            f"{count}"
        )

    print()

    # Worker Changes
   

    print("WORKER CHANGES")
    print("-" * 70)

    for worker_change in (
        workstation.worker_change_log
    ):

        worker_id = (
            worker_change["worker_id"]
        )

        limit = (
            worker_change["worker_job_limit"]
        )

        initial = (
            worker_change["initial"]
        )

        print(
            f"[{worker_change['timestamp']:8.2f}] "
            f"Worker={worker_id} "
            f"JobLimit={limit} "
            f"Initial={initial}"
        )

    print()

    print("=" * 70)
    print("SIMULATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()