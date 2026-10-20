from enum import Enum


class MachineState(Enum):
    

    IDLE = "IDLE"

    SETUP = "SETUP"

    PROCESSING = "PROCESSING"

    FAULTED = "FAULTED"

    REPAIR = "REPAIR"