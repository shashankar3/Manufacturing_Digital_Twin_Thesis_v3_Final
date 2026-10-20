import math


class SemiMarkov:

    
    # Generic Duration Sampler
    

    def __sample_duration(
        self,
        distribution,
        mean_time,
    ):

        
        # Validate learned mean
        

        valid_mean = None

        if mean_time is not None:

            try:

                mean_time = float(
                    mean_time
                )

                if (
                    math.isfinite(mean_time)
                    and mean_time >= 0.0
                ):

                    valid_mean = mean_time

            except (
                TypeError,
                ValueError,
                FloatingPointError,
            ):

                valid_mean = None

        
        # Near-Zero Duration
        

        ZERO_TIME_THRESHOLD = 1e-6

        if (
            valid_mean is not None
            and valid_mean <= ZERO_TIME_THRESHOLD
        ):

            return valid_mean

       
        # Sample from learned distribution.
      

        if distribution is not None:

            try:

                distribution_object = (
                    distribution.get(
                        "distribution_object"
                    )
                )

                if distribution_object is not None:

                    sampled_time = float(
                        distribution_object.rvs()
                    )

                   
                    # Validate sampled value
                   

                    if (
                        math.isfinite(
                            sampled_time
                        )
                        and sampled_time >= 0.0
                    ):

                       

                        if (
                            valid_mean is not None
                            and valid_mean > 0.0
                        ):

                            MAX_MEAN_MULTIPLIER = 10.0

                            maximum_reasonable_time = (
                                valid_mean
                                * MAX_MEAN_MULTIPLIER
                            )

                            if (
                                sampled_time
                                <= maximum_reasonable_time
                            ):

                                return sampled_time

                        else:

                            return sampled_time

            except (
                AttributeError,
                ValueError,
                TypeError,
                KeyError,
                FloatingPointError,
            ):

                pass

       
        
        # Use learned mean duration.
        

        if valid_mean is not None:

            return valid_mean

       
        # No valid knowledge available
        

        return None

    
    # Machine-State Holding Time
    

    def sample_holding_time(
        self,
        current_state,
        behaviour_model,
    ):

        distribution = None

        mean_time = None

       
        # IDLE
       

        if current_state.name == "IDLE":

            distribution = (
                behaviour_model.idle_distribution
            )

            mean_time = (
                behaviour_model.mean_idle_time
            )

       
        # SETUP
       

        elif current_state.name == "SETUP":

            distribution = (
                behaviour_model.setup_distribution
            )

            mean_time = (
                behaviour_model.mean_setup_time
            )

        
        # PROCESSING
        

        elif current_state.name == "PROCESSING":

            distribution = (
                behaviour_model.processing_distribution
            )

            mean_time = (
                behaviour_model.processing_mean
            )

       
        # FAULTED
        

        elif current_state.name == "FAULTED":

            distribution = (
                behaviour_model.fault_response_distribution
            )

            mean_time = (
                behaviour_model.mean_fault_response_time
            )

       
        # REPAIR
       

        elif current_state.name == "REPAIR":

            distribution = (
                behaviour_model.repair_distribution
            )

            mean_time = (
                behaviour_model.mean_repair_time
            )

        
        # Unknown State
        

        else:

            return None

        return self.__sample_duration(
            distribution,
            mean_time,
        )

    
    # Job Inter-Arrival Time
    

    def sample_interarrival_time(
        self,
        behaviour_model,
    ):

        distribution = (
            behaviour_model.interarrival_distribution
        )

        mean_time = (
            behaviour_model.mean_interarrival_time
        )

        return self.__sample_duration(
            distribution,
            mean_time,
        )

  
    # Setup Time
   

    def sample_setup_time(
        self,
        behaviour_model,
    ):

        distribution = (
            behaviour_model.setup_distribution
        )

        mean_time = (
            behaviour_model.mean_setup_time
        )

        return self.__sample_duration(
            distribution,
            mean_time,
        )