from typing import Dict, FrozenSet

from common_model.models.machine_state import MachineState


class StateTransitions:
    

    ALLOWED_TRANSITIONS: Dict[
        MachineState,
        FrozenSet[MachineState]
    ] = {
        MachineState.IDLE: frozenset({
            MachineState.SETUP,
            MachineState.FAULTED,
        }),

        MachineState.SETUP: frozenset({
            MachineState.PROCESSING,
            MachineState.FAULTED,
        }),

        MachineState.PROCESSING: frozenset({
            MachineState.IDLE,
            MachineState.SETUP,
            MachineState.FAULTED,
        }),

        MachineState.FAULTED: frozenset({
            MachineState.REPAIR,
        }),

        MachineState.REPAIR: frozenset({
            MachineState.SETUP,
            MachineState.PROCESSING,
            MachineState.IDLE,
        }),
    }

    @classmethod
    def is_valid(
        cls,
        current_state: MachineState,
        next_state: MachineState,
    ) -> bool:
        
        return next_state in cls.ALLOWED_TRANSITIONS.get(
            current_state,
            frozenset(),
        )

    @classmethod
    def allowed_next_states(
        cls,
        current_state: MachineState,
    ) -> FrozenSet[MachineState]:
        
        return cls.ALLOWED_TRANSITIONS.get(
            current_state,
            frozenset(),
        )

    @classmethod
    def validate(
        cls,
        current_state: MachineState,
        next_state: MachineState,
    ) -> None:
       
        if not cls.is_valid(current_state, next_state):
            raise ValueError(
                f"Invalid machine-state transition: "
                f"{current_state.value} -> {next_state.value}"
            )