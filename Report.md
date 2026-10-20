 Manufacturing Digital Twin: Learning, Synchronisation, Prediction, Drift Detection and Adaptation

 1. Scope

The implementation consists of two systems. System A simulates the manufacturing process and generates the actual events. System B receives those events and builds its own model of the system's operational states and behavioural characteristics.

The main objective is to investigate how System B learns from observations, predicts the next operational state and its timing, detects changes in behaviour, and adapts its model without directly accessing the hidden parameters used by System A.

The main execution flow is defined in `main.py`, while `digital_twin.py` coordinates the components of System B.


 2. Common Models

The Common Models folder defines the shared data structures and rules used by both System A and System B. It provides a consistent representation of manufacturing events, jobs, machine states, and valid state transitions.

These shared definitions allow System A to generate and communicate manufacturing events in a format that System B can interpret and use for synchronisation, learning, and prediction. They also ensure that both systems follow the same definitions of operational states and valid transitions.


 3. System A: Manufacturing Simulation

System A represents a manufacturing workstation using discrete-event simulation.

The main components are:

- `main.py` creates the SimPy environment and initialises the simulation.
- `behaviour_engine.py` defines the workstation's underlying processing behaviour, including processing times, failures, response times, repair times, and processing drift.
- `job_generator.py` generates incoming jobs and their arrival events.
- `worker_generator.py` creates workers and their associated profiles.
- `workstation.py` coordinates workstation operations and emits observable events.
- `event.py` defines the event data structure, while `event_type.py` defines the event types.
- `job.py` and `worker.py` represent jobs and workers.
- `machine_state.py` defines the machine states, while `state_transitions.py` specifies the allowed transitions between states.

The simulation uses predefined parameters to generate ground-truth behaviour. For example, the current configuration in `main.py` sets the processing-time mean to 10 seconds, the processing-time standard deviation to 1 second, the processing drift per job to 0.2, and the failure probability to 0.25. Repair and fault-response times are also configured.

These parameters remain within System A. System B receives the events emitted by the workstation but does not receive the hidden behaviour parameters or worker profiles.


 4. System B: Digital Twin Architecture

System B is coordinated by `digital_twin.py`. It connects the event receiver, state synchroniser, behavioural estimator, prediction engine, prediction evaluators, and adaptation components.

The main files are:

- `event_receiver.py` processes incoming events and coordinates the learning, validation, and adaptation workflow.
- `state_synchronizer.py` updates the Digital Twin's operational state and simulation time.
- `operational_state.py` maintains the current operational state.
- `behaviour_estimator.py` learns behavioural characteristics from observed events.
- `behaviour_model.py` stores the learned behavioural estimates.
- `markov_chain.py` learns state-transition probabilities.
- `semi_markov.py` models state durations and timing behaviour.
- `prediction_engine.py` combines state-transition and timing predictions.
- `online_prediction_evaluator.py` evaluates rolling one-step predictions.
- `adaptation_manager.py` coordinates drift monitoring and adaptation.
- `drift_detector.py` monitors timing prediction errors.
- `transition_drift_detector.py` monitors changes in state-transition behaviour.
- `transition_adaptation.py` updates transition probabilities when adaptation is required.
- `sliding_window.py` manages recent observations used for estimation.

These components work together but perform different functions. Synchronisation maintains the current state, learning estimates behaviour, prediction forecasts the next outcome, evaluation measures prediction performance, drift detection identifies persistent changes, and adaptation updates the model.

 5. Learning

Learning takes place mainly through `event_receiver.py`, `behaviour_estimator.py`, `feature_extractor.py`, `parameter_estimator.py`, `distribution_fitter.py`, `goodness_of_fit.py`, and `markov_chain.py`.

 5.1 Collecting observations

When an event arrives, `event_receiver.py` passes relevant information to the behavioural estimator. The estimator collects timing and contextual information from the observed events.

`feature_extractor.py` extracts information needed for estimation, including event timing and available context such as worker identity.

 5.2 Estimating behavioural parameters

`behaviour_estimator.py` coordinates the estimation process and updates the learned model stored in `behaviour_model.py`.

`parameter_estimator.py` estimates numerical parameters from observed samples. These include timing characteristics such as means and variability.

`distribution_fitter.py` evaluates candidate statistical distributions for observed durations, while `goodness_of_fit.py` assesses how well candidate distributions represent the collected samples.

The resulting estimates can describe behaviour such as job inter-arrival times, setup durations, processing durations, fault-response times, and repair durations.


 5.3 Learning state transitions

`markov_chain.py` maintains counts of observed transitions between operational states and converts those counts into transition probabilities.

For example, when a transition from PROCESSING to IDLE is observed, the corresponding transition count is updated. The model uses the accumulated observations to estimate the likelihood of each possible next state.


 6. Synchronisation

Synchronisation is implemented mainly in `event_receiver.py`, `state_synchronizer.py`, and `operational_state.py`.

`workstation.py` emits events when observable activities occur in System A. `event_receiver.py` receives these events and determines whether an event represents an actual machine-state transition.

`state_synchronizer.py` updates the Digital Twin's operational state and associated time information. `operational_state.py` stores the resulting state representation.

Not every event changes the machine state. A worker change, for example, can provide useful information for behavioural learning without necessarily representing a transition between machine states.

The receiver therefore separates events used for behavioural observation from actual state transitions used by the prediction workflow.

This event-driven approach keeps System B aligned with the observed manufacturing process without giving it direct access to System A's internal simulation state.


 7. Prediction

Prediction is implemented mainly in `markov_chain.py`, `semi_markov.py`, and `prediction_engine.py`.

 7.1 State prediction

`markov_chain.py` uses learned transition probabilities to estimate the next operational state given the current state.

The default prediction selects the most probable learned next state. The prediction therefore depends on the current state and the transition probabilities learned from previous observations.

 7.2 Timing prediction

`semi_markov.py` handles timing separately from the next-state choice. It uses learned duration information and fitted distributions where available to estimate the timing of the next event or state transition.


 7.3 Combining the predictions

`prediction_engine.py` coordinates the state and timing models to generate the next prediction.

`digital_twin.py` exposes the prediction functionality and connects it to the online evaluation workflow.

The current experiment uses rolling one-step prediction. System B predicts the next eligible transition, compares the prediction with the subsequent observation, updates its model, and then generates the next prediction.


 8. Prediction Evaluation

The current rolling prediction experiment uses `online_prediction_evaluator.py`.

The evaluator compares predicted outcomes with observed outcomes and records state prediction performance and timing errors.

The reported measures include state accuracy, mean absolute timing error, root mean squared timing error, timing bias, and accuracy within specified timing-error tolerances. Per-transition results are also collected where sufficient observations are available.

The implementation separates state prediction errors from timing errors. A timing residual is only meaningful when the observed transition is eligible for timing evaluation.

The code also contains `prediction_validator.py`, which supports a separate open-loop prediction recording and evaluation path. The current rolling experiment uses `online_prediction_evaluator.py` for its principal online prediction metrics.

 9. Drift Detection

Drift detection identifies persistent changes in observed behaviour that make the existing model less accurate.

The main components are `drift_detector.py`, `transition_drift_detector.py`, and `adaptation_manager.py`.

 9.1 Timing drift

`drift_detector.py` implements CUSUM-style monitoring of prediction errors. CUSUM accumulates evidence from successive errors rather than treating every isolated deviation as a change in the system.

`adaptation_manager.py` coordinates the monitoring process and maintains separate detectors for supported timing and behavioural channels.

When persistent timing drift is detected, the manager can request an update of the corresponding behavioural estimates using observed data.

Prediction errors are used as evidence of drift. They are not treated as if they were actual processing-time measurements.

 9.2 Transition drift

Timing drift and transition drift represent different types of change.

Timing drift occurs when the duration associated with a transition changes. Transition drift occurs when the pattern of state transitions changes.

`transition_drift_detector.py` monitors changes in categorical transition behaviour. `adaptation_manager.py` connects this monitoring to the transition-adaptation process and maintains the associated monitoring history and summaries.


 10. Adaptation

Adaptation is coordinated by `adaptation_manager.py`, with supporting functionality in `sliding_window.py`, `behaviour_estimator.py`, and `transition_adaptation.py`.

 10.1 Behavioural adaptation

When timing drift is detected, `adaptation_manager.py` can request behavioural re-estimation through the adaptation callback configured in `digital_twin.py`.

`behaviour_estimator.py` updates the relevant behavioural estimates using observed event data. `sliding_window.py` provides the recent-observation window used by the sliding-window estimation workflow.

Using recent observations allows the model to respond to changing behaviour without giving the entire historical dataset equal influence.


 10.2 Transition adaptation

`transition_adaptation.py` supports two approaches for updating transition probabilities.

The sliding-window approach estimates transition probabilities from recent transition observations. The Bayesian approach uses a Dirichlet model to estimate a posterior-mean transition matrix from the prior and observed transition counts.

The implementation maintains these approaches as separate branches so that their results can be evaluated independently.

The transition-adaptation methods update state-transition probabilities, whereas behavioural adaptation updates timing and duration estimates.


 11. Overall Working

The execution flow is controlled by `main.py`.

First, System A is initialised and begins generating manufacturing events. System B receives those events through `event_receiver.py` and synchronises its state using `state_synchronizer.py`.

During the initial learning period, `behaviour_estimator.py` learns timing characteristics and `markov_chain.py` learns transition probabilities. The prediction components then use the learned models to predict the next state and its timing.

During rolling validation, `online_prediction_evaluator.py` compares predictions with actual observations. `drift_detector.py` and `transition_drift_detector.py` monitor persistent timing and transition deviations.

When drift criteria are met, `adaptation_manager.py` coordinates updates to the behavioural estimates or transition probabilities. The updated model is then used for subsequent predictions.

This creates a continuous loop of observation, synchronisation, learning, prediction, evaluation, drift detection, and adaptation.

