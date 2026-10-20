import random

import simpy

from common_model.models.event_type import EventType
from common_model.models.job import Job


class JobGenerator:
    

    def __init__(
        self,
        env: simpy.Environment,
        workstation,
        min_interarrival_time: float = 8.0,
        max_interarrival_time: float = 20.0,
    ):

        if min_interarrival_time <= 0:
            raise ValueError(
                "Minimum interarrival time must be > 0."
            )

        if (
            max_interarrival_time
            < min_interarrival_time
        ):
            raise ValueError(
                "Maximum interarrival time must be "
                "greater than or equal to minimum."
            )

        self.env = env

        self.workstation = workstation

        self.min_interarrival_time = (
            min_interarrival_time
        )

        self.max_interarrival_time = (
            max_interarrival_time
        )

        self.job_counter = 0

    
    # Job Generation
    

    def generate_jobs(self):

        while True:

            
            # Create job
            

            self.job_counter += 1

            job = Job(
                job_id=self.job_counter,
                arrival_time=self.env.now,
            )

           
            # Emit arrival event
            

            self.workstation.emit_event(
                event_type=EventType.JOB_ARRIVAL,
                job_id=job.job_id,
            )

            
            # Send job to workstation
            

            self.env.process(
                self.workstation.process_job(
                    job
                )
            )

            
            # Sample next arrival
            

            interarrival_time = random.uniform(
                self.min_interarrival_time,
                self.max_interarrival_time,
            )

            yield self.env.timeout(
                interarrival_time
            )