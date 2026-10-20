import random

from common_model.models.state_transitions import StateTransitions


class MarkovChain:
    

    def __init__(self):

       
        # Transition counts
        

        self.transition_counts = {}

       
        # Transition probabilities
       

        self.transition_probabilities = {}

   
    # Learn Transition
    

    def observe_transition(
        self,
        current_state,
        next_state,
    ):

       
        # Validate structural transition
        

        StateTransitions.validate(
            current_state,
            next_state,
        )

        key = (
            current_state,
            next_state,
        )

        self.transition_counts[key] = (
            self.transition_counts.get(
                key,
                0,
            )
            + 1
        )

        self.__update_probabilities()

   
    # Get Transition Probability
    

    def get_transition_probability(
        self,
        current_state,
        next_state,
    ):
        

        return self.transition_probabilities.get(
            (
                current_state,
                next_state,
            ),
            0.0,
        )

   
    # Update Transition Matrix
    

    def __update_probabilities(
        self,
    ):

        self.transition_probabilities.clear()

        
        # Total outgoing transitions from each state
        

        totals = {}

        for (
            current_state,
            _,
        ), count in self.transition_counts.items():

            totals[current_state] = (
                totals.get(
                    current_state,
                    0,
                )
                + count
            )

        
        # Compute probabilities
        

        for (
            current_state,
            next_state,
        ), count in self.transition_counts.items():

            total = totals.get(
                current_state,
                0,
            )

            if total <= 0:
                continue

            self.transition_probabilities[
                (
                    current_state,
                    next_state,
                )
            ] = (
                count / total
            )

    
    # Predict Next State
    

    def predict_next_state(
        self,
        current_state,
        sample=False,
    ):

        candidates = []

        allowed_states = (
            StateTransitions.allowed_next_states(
                current_state
            )
        )

        for (
            state,
            next_state,
        ), probability in (
            self.transition_probabilities.items()
        ):

            if (
                state == current_state
                and next_state in allowed_states
                and probability > 0.0
            ):

                candidates.append(
                    (
                        next_state,
                        probability,
                    )
                )

        if not candidates:
            return None

        
        # Safety normalisation
      

        total_probability = sum(
            probability
            for (
                _,
                probability,
            ) in candidates
        )

        if total_probability <= 0.0:
            return None

        candidates = [
            (
                next_state,
                probability / total_probability,
            )
            for (
                next_state,
                probability,
            ) in candidates
        ]

        
        # Prediction versus stochastic simulation
       

        if not sample:
            return max(
                candidates,
                key=lambda item: item[1],
            )[0]

        r = random.random()
        cumulative = 0.0

        for (
            next_state,
            probability,
        ) in candidates:

            cumulative += probability

            if r <= cumulative:
                return next_state

        return candidates[-1][0]

    
    # Public Accessor
    

    def get_transition_matrix(
        self,
    ):
        

        return self.transition_probabilities