class SlidingWindow:
    
    def __init__(
        self,
        window_size=20,
    ):
        

        if window_size <= 0:

            raise ValueError(
                "window_size must be greater than zero."
            )

        self.window_size = int(
            window_size
        )

       
        # Window Mode
       

        self.enabled = False

    
    # Window Control
   

    def enable(
        self,
        window_size=None,
    ):
        

        if window_size is not None:

            if window_size <= 0:

                raise ValueError(
                    "window_size must be greater than zero."
                )

            self.window_size = int(
                window_size
            )

        self.enabled = True

    

    def disable(
        self,
    ):
       

        self.enabled = False

    

    def select(
        self,
        samples,
    ):

        

        if samples is None:

            return []

        

        if not self.enabled:


            try:

                return samples.copy()

            except AttributeError:

                return list(
                    samples
                )

        
        # Sliding-Window Mode
        

        return samples[
            -self.window_size:
        ]

   

    def select_recent(
        self,
        samples,
        window_size=None,
    ):

        if samples is None:

            return []

        if window_size is None:

            window_size = (
                self.window_size
            )

        if window_size <= 0:

            raise ValueError(
                "window_size must be greater than zero."
            )

        window_size = int(
            window_size
        )

        return samples[
            -window_size:
        ]

   

    def get_sample_count(
        self,
        samples,
    ):

        if samples is None:

            return 0

        if not self.enabled:

            return len(
                samples
            )

        return min(
            len(samples),
            self.window_size,
        )

   
    

    def get_selection_info(
        self,
        samples,
    ):

        total_count = 0

        if samples is not None:

            total_count = len(
                samples
            )

        selected_count = (
            self.get_sample_count(
                samples
            )
        )

        return {
            "enabled": self.enabled,
            "window_size": self.window_size,
            "total_observations": total_count,
            "selected_observations": selected_count,
            "using_all_observations": (
                not self.enabled
            ),
        }

   

    def get_window_size(
        self,
    ):
        

        return self.window_size

   

    def is_enabled(
        self,
    ):
        

        return self.enabled


    def set_window_size(
        self,
        window_size,
    ):
        

        if window_size <= 0:

            raise ValueError(
                "window_size must be greater than zero."
            )

        self.window_size = int(
            window_size
        )


    def __repr__(
        self,
    ):
        

        return (
            "SlidingWindow("
            f"window_size="
            f"{self.window_size}, "
            f"enabled="
            f"{self.enabled}"
            ")"
        )