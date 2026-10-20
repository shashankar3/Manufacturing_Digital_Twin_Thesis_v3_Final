from copy import deepcopy

from system_b.prediction.semi_markov import SemiMarkov


class PredictionEngine:
   

    def __init__(self, markov_chain):

        self.markov_chain = markov_chain
        self.semi_markov = SemiMarkov()

    
    # Behaviour Model Selection
   

    def _get_behaviour_model(
        self,
        behaviour_model,
        worker_id=None,
        machine_state=None,
    ):
       

        worker_dependent_states = {
            "SETUP",
            "PROCESSING",
            "REPAIR",
        }

        if machine_state is None:
            return behaviour_model

        # Convert enum states to their names where necessary.
        state_name = getattr(
            machine_state,
            "name",
            str(machine_state),
        )

        # IDLE and FAULTED are not worker-dependent.
        if state_name not in worker_dependent_states:
            return behaviour_model

        if (
            worker_id is not None
            and hasattr(
                behaviour_model,
                "worker_behaviours",
            )
        ):
            worker_behaviours = (
                behaviour_model.worker_behaviours
            )

            if worker_id in worker_behaviours:
                return worker_behaviours[
                    worker_id
                ]

        return behaviour_model

    
    # Generate Machine-State Prediction
   

    def predict(
        self,
        operational_state,
        behaviour_model,
        prediction_steps=10,
    ):
        

        state = deepcopy(
            operational_state
        )

        trajectory = []

        for _ in range(
            prediction_steps
        ):

            current_state = (
                state.machine_state
            )

            
            # Current worker
            

            current_worker_id = getattr(
                state,
                "current_worker_id",
                None,
            )

            
            # Predict next machine state
           

            next_state = (
                self.markov_chain.predict_next_state(
                    current_state
                )
            )

            if next_state is None:
                break

           
            # Select behavioural model
            

            prediction_behaviour = (
                self._get_behaviour_model(
                    behaviour_model,
                    current_worker_id,
                    current_state,
                )
            )

            # Predict holding time of current state
          

            holding_time = (
                self.semi_markov.sample_holding_time(
                    current_state,
                    prediction_behaviour,
                )
            )

            if holding_time is None:
                break

            holding_time = max(
                0.0,
                float(holding_time),
            )

            # Advance prediction clock
            

            transition_time = (
                state.simulation_time
                + holding_time
            )

            state.simulation_time = (
                transition_time
            )

           
            # Update predicted state
           

            state.machine_state = (
                next_state
            )

            
            # Store prediction
           

            prediction = {
                "current_state":
                    current_state.name,

                "holding_time":
                    round(
                        holding_time,
                        2,
                    ),

                "next_state":
                    next_state.name,

                "transition_time":
                    round(
                        float(
                            transition_time
                        ),
                        2,
                    ),

                "worker_id":
                    current_worker_id,
            }

            trajectory.append(
                prediction
            )

        return trajectory

   
    # Predict Incoming Job Arrivals
   

    def predict_job_arrivals(
        self,
        behaviour_model,
        start_time=0.0,
        prediction_count=10,
    ):
       

        current_time = float(
            start_time
        )

        arrivals = []

        for job_index in range(
            1,
            prediction_count + 1,
        ):

            interarrival_time = (
                self.semi_markov.sample_interarrival_time(
                    behaviour_model
                )
            )

            if interarrival_time is None:
                break

            interarrival_time = max(
                0.0,
                float(interarrival_time),
            )

            current_time += (
                interarrival_time
            )

            arrivals.append(
                {
                    "job_index":
                        job_index,

                    "interarrival_time":
                        round(
                            interarrival_time,
                            2,
                        ),

                    "arrival_time":
                        round(
                            current_time,
                            2,
                        ),
                }
            )

        return arrivals

    
    # Predict Next Job Arrival
   

    def predict_next_job_arrival(
        self,
        behaviour_model,
        current_time=0.0,
    ):
        

        interarrival_time = (
            self.semi_markov.sample_interarrival_time(
                behaviour_model
            )
        )

        if interarrival_time is None:
            return None

        interarrival_time = max(
            0.0,
            float(interarrival_time),
        )

        arrival_time = (
            float(current_time)
            + interarrival_time
        )

        return {
            "interarrival_time":
                round(
                    interarrival_time,
                    2,
                ),

            "arrival_time":
                round(
                    arrival_time,
                    2,
                ),
        }

    
    # Predict Next Setup
    

    def predict_next_setup(
        self,
        behaviour_model,
        worker_id=None,
    ):
        

        prediction_behaviour = (
            self._get_behaviour_model(
                behaviour_model,
                worker_id,
                "SETUP",
            )
        )

        setup_time = (
            self.semi_markov.sample_setup_time(
                prediction_behaviour
            )
        )

        if setup_time is None:
            return None

        return {
            "setup_time":
                round(
                    max(
                        0.0,
                        float(setup_time),
                    ),
                    2,
                ),

            "worker_id":
                worker_id,
        }