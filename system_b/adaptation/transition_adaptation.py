from __future__ import annotations

from collections import Counter, deque
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


Transition = Tuple[Any, Any]


class TransitionAdaptation:


    def __init__(
        self,
        states: Sequence[Any],
        window_size: int = 50,
        dirichlet_prior: float = 1.0,
    ) -> None:

        if not states:
            raise ValueError(
                "states must contain at least one state."
            )

        if window_size <= 0:
            raise ValueError(
                "window_size must be > 0."
            )

        if dirichlet_prior <= 0:
            raise ValueError(
                "dirichlet_prior must be > 0."
            )

        
        self.states: List[Any] = list(
            dict.fromkeys(states)
        )

        self.window_size = int(
            window_size
        )

        self.dirichlet_prior = float(
            dirichlet_prior
        )

        
        # Shared observed transition history
     

        self.transition_history: List[
            Transition
        ] = []

       
        # Sliding-window branch
        

        self.window: deque[
            Transition
        ] = deque(
            maxlen=self.window_size
        )

        self.sliding_window_matrix: Dict[
            Any, Dict[Any, float]
        ] = self._empty_matrix()

       
        # Bayesian branch
        

        self.dirichlet_counts: Dict[
            Any, Dict[Any, float]
        ] = self._empty_matrix()

        self.bayesian_matrix: Dict[
            Any, Dict[Any, float]
        ] = self._empty_matrix()

        self._initialise_bayesian_prior()


        self.adaptation_count = 0

        self.last_adaptation: Optional[
            Dict[str, Any]
        ] = None

       
        self.sliding_window_evaluated = 0
        self.sliding_window_correct = 0
        self.bayesian_evaluated = 0
        self.bayesian_correct = 0
        self.branch_evaluation_history: List[
            Dict[str, Any]
        ] = []


    def _empty_matrix(
        self,
    ) -> Dict[Any, Dict[Any, float]]:
       

        return {
            state: {
                destination: 0.0
                for destination in self.states
            }
            for state in self.states
        }

   

    def _initialise_bayesian_prior(
        self,
    ) -> None:
       

        for state in self.states:

            for destination in self.states:

                self.dirichlet_counts[
                    state
                ][destination] = (
                    self.dirichlet_prior
                )

        self._recalculate_bayesian_matrix()

    def _predict_from_matrix(
        self,
        matrix: Dict[Any, Dict[Any, float]],
        current_state: Any,
    ) -> Any:
        row = matrix.get(current_state, {})
        if not row:
            return None
        return max(row.items(), key=lambda item: item[1])[0]

    def _evaluate_branches(
        self,
        current_state: Any,
        next_state: Any,
    ) -> None:
        sw_prediction = self._predict_from_matrix(
            self.sliding_window_matrix,
            current_state,
        )
        bayes_prediction = self._predict_from_matrix(
            self.bayesian_matrix,
            current_state,
        )

        sw_available = (
            current_state in self.sliding_window_matrix
            and any(
                value > 0.0
                for value in self.sliding_window_matrix[current_state].values()
            )
        )
        bayes_available = current_state in self.bayesian_matrix

        if sw_available:
            self.sliding_window_evaluated += 1
            if sw_prediction == next_state:
                self.sliding_window_correct += 1

        if bayes_available:
            self.bayesian_evaluated += 1
            if bayes_prediction == next_state:
                self.bayesian_correct += 1

        self.branch_evaluation_history.append(
            {
                "transition": (current_state, next_state),
                "sliding_window_prediction": sw_prediction,
                "sliding_window_available": sw_available,
                "sliding_window_correct": (
                    sw_prediction == next_state
                    if sw_available else None
                ),
                "bayesian_prediction": bayes_prediction,
                "bayesian_available": bayes_available,
                "bayesian_correct": (
                    bayes_prediction == next_state
                    if bayes_available else None
                ),
            }
        )

   
    # Observation
    

    def observe_transition(
        self,
        current_state: Any,
        next_state: Any,
    ) -> None:
        

        transition = (
            current_state,
            next_state,
        )

        self._evaluate_branches(
            current_state,
            next_state,
        )

        self.transition_history.append(
            transition
        )

        self.window.append(
            transition
        )

        
        # Sliding Window
        

        self._recalculate_sliding_window()

       
        # Bayesian Dirichlet
        

        self._update_bayesian_counts(
            current_state,
            next_state,
        )

        self._recalculate_bayesian_matrix()


    def _recalculate_sliding_window(
        self,
    ) -> None:

        matrix = self._empty_matrix()

        counts: Dict[
            Any, Counter
        ] = {
            state: Counter()
            for state in self.states
        }

        for current_state, next_state in self.window:

            if current_state not in counts:
                continue

            if next_state not in self.states:
                continue

            counts[
                current_state
            ][next_state] += 1

        for current_state in self.states:

            total = sum(
                counts[
                    current_state
                ].values()
            )

            if total <= 0:
                continue

            for next_state in self.states:

                matrix[
                    current_state
                ][next_state] = (
                    counts[
                        current_state
                    ][next_state]
                    / total
                )

        self.sliding_window_matrix = matrix


    def _update_bayesian_counts(
        self,
        current_state: Any,
        next_state: Any,
    ) -> None:
        

        if current_state not in self.dirichlet_counts:
            return

        if next_state not in self.states:
            return

        self.dirichlet_counts[
            current_state
        ][next_state] += 1.0

    

    def _recalculate_bayesian_matrix(
        self,
    ) -> None:

        matrix = self._empty_matrix()

        for current_state in self.states:

            row = self.dirichlet_counts[
                current_state
            ]

            total = sum(
                row.values()
            )

            if total <= 0:
                continue

            for next_state in self.states:

                matrix[
                    current_state
                ][next_state] = (
                    row[next_state]
                    / total
                )

        self.bayesian_matrix = matrix

   
    # Adaptation snapshot
    

    def adapt(
        self,
    ) -> Dict[str, Any]:
       

        self.adaptation_count += 1

        self.last_adaptation = {
            "adaptation_number": (
                self.adaptation_count
            ),
            "history_size": (
                len(self.transition_history)
            ),
            "window_size": (
                len(self.window)
            ),
            "sliding_window_matrix": (
                self.get_sliding_window_matrix()
            ),
            "bayesian_matrix": (
                self.get_bayesian_matrix()
            ),
            "evaluation": (
                self.get_evaluation_metrics()
            ),
        }

        return dict(
            self.last_adaptation
        )

  
    # Prediction access
   

    def get_sliding_window_probability(
        self,
        current_state: Any,
        next_state: Any,
    ) -> float:
       

        return self.sliding_window_matrix.get(
            current_state,
            {},
        ).get(
            next_state,
            0.0,
        )


    def get_bayesian_probability(
        self,
        current_state: Any,
        next_state: Any,
    ) -> float:
        

        return self.bayesian_matrix.get(
            current_state,
            {},
        ).get(
            next_state,
            0.0,
        )

    # Matrix access
   

    def get_sliding_window_matrix(
        self,
    ) -> Dict[Any, Dict[Any, float]]:
       

        return {
            state: dict(
                row
            )
            for state, row
            in self.sliding_window_matrix.items()
        }

    

    def get_bayesian_matrix(
        self,
    ) -> Dict[Any, Dict[Any, float]]:
        

        return {
            state: dict(
                row
            )
            for state, row
            in self.bayesian_matrix.items()
        }

    # History access
  

    def get_transition_history(
        self,
    ) -> List[Transition]:
       

        return list(
            self.transition_history
        )

    

    def get_window_history(
        self,
    ) -> List[Transition]:
       

        return list(
            self.window
        )


    def get_state_space(
        self,
    ) -> List[Any]:
        

        return list(
            self.states
        )

    

    def get_adaptation_count(
        self,
    ) -> int:
       

        return self.adaptation_count

   

    def get_last_adaptation(
        self,
    ) -> Optional[Dict[str, Any]]:
        

        if self.last_adaptation is None:
            return None

        return dict(
            self.last_adaptation
        )

    

    def get_evaluation_metrics(
        self,
    ) -> Dict[str, Any]:
        
        return {
            "sliding_window": {
                "evaluated_predictions": self.sliding_window_evaluated,
                "correct_predictions": self.sliding_window_correct,
                "state_accuracy": (
                    self.sliding_window_correct
                    / self.sliding_window_evaluated
                    if self.sliding_window_evaluated else 0.0
                ),
            },
            "bayesian": {
                "evaluated_predictions": self.bayesian_evaluated,
                "correct_predictions": self.bayesian_correct,
                "state_accuracy": (
                    self.bayesian_correct
                    / self.bayesian_evaluated
                    if self.bayesian_evaluated else 0.0
                ),
            },
        }

    def get_branch_evaluation_history(
        self,
    ) -> List[Dict[str, Any]]:
        
        return [dict(record) for record in self.branch_evaluation_history]

    def reset(
        self,
        preserve_bayesian_prior: bool = True,
    ) -> None:
        

        self.transition_history.clear()

        self.window.clear()

        self.sliding_window_matrix = (
            self._empty_matrix()
        )

        if preserve_bayesian_prior:

            self.dirichlet_counts = (
                self._empty_matrix()
            )

            self._initialise_bayesian_prior()

        self.adaptation_count = 0

        self.last_adaptation = None
        self.sliding_window_evaluated = 0
        self.sliding_window_correct = 0
        self.bayesian_evaluated = 0
        self.bayesian_correct = 0
        self.branch_evaluation_history.clear()