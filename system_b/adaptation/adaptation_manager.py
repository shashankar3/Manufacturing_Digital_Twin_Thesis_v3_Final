from collections import defaultdict
from copy import deepcopy


class AdaptationManager:

   
    # Supported Adaptive Transitions
    

    ADAPTIVE_TRANSITIONS = {
        ("PROCESSING", "IDLE"),
        ("PROCESSING", "FAULTED"),
        ("SETUP", "PROCESSING"),
        ("SETUP", "FAULTED"),
        ("FAULTED", "REPAIR"),
        ("REPAIR", "PROCESSING"),
        ("REPAIR", "SETUP"),
    }

    
    # Supported Adaptive Behaviour Channels

    ADAPTIVE_BEHAVIOUR_CHANNELS = {
        "INCOMING_JOB",
        "SETUP",
    }
    

    def __init__(
        self,
        drift_detector=None,
        adaptation_callback=None,
        behaviour_adaptation_callback=None,
        transition_drift_detector=None,
        transition_adaptation=None,
    ):

       
        # Prototype CUSUM Detector
       

        self.drift_detector = drift_detector

       
        # Machine-State Behavioural Adaptation Callback
        

        self.adaptation_callback = adaptation_callback


        self.behaviour_adaptation_callback = (
            behaviour_adaptation_callback
        )


        self.transition_drift_detector = (
            transition_drift_detector
        )


        self.transition_adaptation = (
            transition_adaptation
        )


        self.transition_observations = 0
        self.transition_detected_drifts = 0
        self.last_transition_drift_result = None
        self.last_transition_adaptation = None

      
        self.transition_monitoring_history = []
        self.transition_adaptation_history = []

        # Adaptation State
       

        self.enabled = False

       
        # Transition-Specific Drift Detectors
        

        self.drift_detectors = {}

        
        # Behaviour-Channel CUSUM Detectors
       

        self.behaviour_drift_detectors = {}

        
        # Current Behaviour-Channel Episode Evidence
     

        self.behaviour_episode_errors = {}

       
        # Last Behaviour-Channel Drift Evidence
       

        self.last_behaviour_drift_evidence = {}

        
        # Behaviour-Channel Statistics
       

        self.behaviour_observed_errors = defaultdict(int)

        self.behaviour_detected_drifts = defaultdict(int)

        self.behaviour_model_updates = defaultdict(int)

       
        # Current CUSUM Episode Evidence

        self.current_episode_errors = {}

        
        # Last Detected Drift Evidence
        

        self.last_drift_evidence = {}

       
        # Adaptation Statistics
       

        self.observed_errors = defaultdict(int)

        self.detected_drifts = defaultdict(int)

        self.model_updates = defaultdict(int)

       

        self.__create_transition_channels()

   
    # Transition Channel Creation
    

    def __create_transition_channels(
        self,
    ):

        # Machine-State Transition Channels
       

        for transition in self.ADAPTIVE_TRANSITIONS:

           
            # Episode Evidence
            

            self.current_episode_errors[
                transition
            ] = []

           
            # Last Drift Evidence
            

            self.last_drift_evidence[
                transition
            ] = []

           
            # Drift Detector
            

            if self.drift_detector is not None:

                self.drift_detectors[
                    transition
                ] = deepcopy(
                    self.drift_detector
                )

        
        # Behaviour-Channel CUSUM Channels
        

        for channel in self.ADAPTIVE_BEHAVIOUR_CHANNELS:

            self.behaviour_episode_errors[
                channel
            ] = []

            self.last_behaviour_drift_evidence[
                channel
            ] = []

            if self.drift_detector is not None:

                self.behaviour_drift_detectors[
                    channel
                ] = deepcopy(
                    self.drift_detector
                )

    
    # Adaptation Control
   

    def enable(
        self,
    ):
        """
        Enable adaptive synchronization.

        Existing CUSUM states are preserved.
        """

        self.enabled = True

    

    def disable(
        self,
    ):
       

        self.enabled = False

    
    # Callback Configuration
    

    def set_adaptation_callback(
        self,
        callback,
    ):
        

        if callback is not None and not callable(
            callback
        ):
            raise TypeError(
                "adaptation callback must be callable or None."
            )

        self.adaptation_callback = callback

    
    # Behavioural Adaptation Callback Configuration
    

    def set_behaviour_adaptation_callback(
        self,
        callback,
    ):

        if callback is not None and not callable(
            callback
        ):
            raise TypeError(
                "behaviour adaptation callback must be "
                "callable or None."
            )

        self.behaviour_adaptation_callback = (
            callback
        )


    @staticmethod
    def __make_behaviour_channel_key(
        behaviour_channel,
    ):

        if hasattr(
            behaviour_channel,
            "name",
        ):
            behaviour_channel = (
                behaviour_channel.name
            )

        channel = str(
            behaviour_channel
        ).strip().upper()

        aliases = {
            "INCOMING": "INCOMING_JOB",
            "INCOMING_JOBS": "INCOMING_JOB",
            "JOB_ARRIVAL": "INCOMING_JOB",
            "JOB_ARRIVALS": "INCOMING_JOB",
            "INTERARRIVAL": "INCOMING_JOB",
            "INTER_ARRIVAL": "INCOMING_JOB",
            "INTERARRIVAL_TIME": "INCOMING_JOB",
            "INTER_ARRIVAL_TIME": "INCOMING_JOB",
            "ARRIVAL": "INCOMING_JOB",
            "ARRIVAL_TIME": "INCOMING_JOB",
            "SETUP_TIME": "SETUP",
            "SETUP_DURATION": "SETUP",
        }

        return aliases.get(
            channel,
            channel,
        )

   

    def is_supported_behaviour_channel(
        self,
        behaviour_channel,
    ):

        channel = (
            self.__make_behaviour_channel_key(
                behaviour_channel
            )
        )

        return (
            channel
            in self.ADAPTIVE_BEHAVIOUR_CHANNELS
        )

    
    # Behaviour Prediction Error Processing
    

    def observe_behaviour_error(
        self,
        behaviour_channel,
        error,
    ):

        
        # 1. Adaptation Disabled
       

        if not self.enabled:

            return None

        
        # 2. Identify Behaviour Channel
        

        channel = (
            self.__make_behaviour_channel_key(
                behaviour_channel
            )
        )

       
        # 3. Ignore Unsupported Channel
        

        if (
            channel
            not in self.ADAPTIVE_BEHAVIOUR_CHANNELS
        ):

            return None

       
        # 4. Normalize Error
        

        error = float(
            error
        )

        
        # 5. Record Eligible Error
        

        self.behaviour_observed_errors[
            channel
        ] += 1

       
        # 6. Store Current CUSUM Episode Evidence
        

        self.behaviour_episode_errors[
            channel
        ].append(
            error
        )

        
        # 7. Obtain Channel-Specific Detector
       

        drift_detector = (
            self.behaviour_drift_detectors.get(
                channel
            )
        )

        
        # 8. No Detector
        

        if drift_detector is None:

            return {
                "behaviour_channel": channel,
                "error": error,
                "drift_detected": False,
                "drift_direction": None,
                "adaptation_triggered": False,
                "adaptation_successful": False,
                "evidence": list(
                    self.behaviour_episode_errors[
                        channel
                    ]
                ),
                "evidence_count": len(
                    self.behaviour_episode_errors[
                        channel
                    ]
                ),
                "cusum_observed_errors": None,
                "cusum_detected_drifts": None,
            }

        
        # 9. CUSUM Drift Detection
       

        drift_detected = (
            drift_detector.observe(
                error
            )
        )

       
        # 10. No Drift
        

        if not drift_detected:

            return {
                "behaviour_channel": channel,
                "error": error,
                "drift_detected": False,
                "drift_direction": None,
                "adaptation_triggered": False,
                "adaptation_successful": False,
                "evidence": list(
                    self.behaviour_episode_errors[
                        channel
                    ]
                ),
                "evidence_count": len(
                    self.behaviour_episode_errors[
                        channel
                    ]
                ),
                "cusum_observed_errors": (
                    self.__get_detector_observed_errors(
                        drift_detector
                    )
                ),
                "cusum_detected_drifts": (
                    self.__get_detector_detected_drifts(
                        drift_detector
                    )
                ),
                "cusum_reset": False,
            }

       
        # 11. Drift Detected
        

        self.behaviour_detected_drifts[
            channel
        ] += 1

       
        # 12. Preserving Complete Drift Evidence
      

        drift_evidence = list(
            self.behaviour_episode_errors[
                channel
            ]
        )

        self.last_behaviour_drift_evidence[
            channel
        ] = list(
            drift_evidence
        )

        
        # 13. Drift Direction
        

        drift_direction = (
            drift_detector
            .get_last_drift_direction()
            if hasattr(
                drift_detector,
                "get_last_drift_direction",
            )
            else None
        )

        
        # 14. Trigger Behavioural Adaptation
        

        adaptation_triggered = (
            self.behaviour_adaptation_callback
            is not None
        )

        adaptation_successful = False
        adaptation_error = None

        if adaptation_triggered:

            try:

                result = (
                    self.behaviour_adaptation_callback(
                        channel,
                        list(
                            drift_evidence
                        ),
                    )
                )

                if result is True:

                    adaptation_successful = True

                    self.behaviour_model_updates[
                        channel
                    ] += 1

            except Exception as exc:

                adaptation_successful = False

                adaptation_error = (
                    repr(exc)
                )

       
        # 15. Start a New CUSUM Episode
       

        self.behaviour_episode_errors[
            channel
        ] = []

       
        # 16. Return Complete Result
       

        return {
            "behaviour_channel": channel,
            "error": error,
            "drift_detected": True,
            "drift_direction": drift_direction,
            "adaptation_triggered": (
                adaptation_triggered
            ),
            "adaptation_successful": (
                adaptation_successful
            ),
            "adaptation_error": (
                adaptation_error
            ),
            "evidence": list(
                drift_evidence
            ),
            "evidence_count": len(
                drift_evidence
            ),
            "cusum_observed_errors": (
                self.__get_detector_observed_errors(
                    drift_detector
                )
            ),
            "cusum_detected_drifts": (
                self.__get_detector_detected_drifts(
                    drift_detector
                )
            ),
            "cusum_reset": True,
        }

   
    # Behaviour Episode Evidence Access
   

    def get_current_behaviour_episode_errors(
        self,
        behaviour_channel=None,
    ):
        

        if behaviour_channel is not None:

            channel = (
                self.__make_behaviour_channel_key(
                    behaviour_channel
                )
            )

            return list(
                self.behaviour_episode_errors.get(
                    channel,
                    [],
                )
            )

        return {
            channel: list(
                errors
            )
            for (
                channel,
                errors,
            ) in self.behaviour_episode_errors.items()
        }

    
    # Last Behaviour Drift Evidence Access
    

    def get_last_behaviour_drift_evidence(
        self,
        behaviour_channel=None,
    ):
        

        if behaviour_channel is not None:

            channel = (
                self.__make_behaviour_channel_key(
                    behaviour_channel
                )
            )

            return list(
                self.last_behaviour_drift_evidence.get(
                    channel,
                    [],
                )
            )

        return {
            channel: list(
                errors
            )
            for (
                channel,
                errors,
            ) in self.last_behaviour_drift_evidence.items()
        }

    
    # Behaviour Error Statistics
    

    def get_behaviour_observed_errors(
        self,
        behaviour_channel=None,
    ):
       

        if behaviour_channel is not None:

            channel = (
                self.__make_behaviour_channel_key(
                    behaviour_channel
                )
            )

            return self.behaviour_observed_errors.get(
                channel,
                0,
            )

        return sum(
            self.behaviour_observed_errors.values()
        )

  
    # Behaviour Drift Statistics
   

    def get_behaviour_detected_drifts(
        self,
        behaviour_channel=None,
    ):
        

        if behaviour_channel is not None:

            channel = (
                self.__make_behaviour_channel_key(
                    behaviour_channel
                )
            )

            return self.behaviour_detected_drifts.get(
                channel,
                0,
            )

        return sum(
            self.behaviour_detected_drifts.values()
        )

   
    # Behaviour Model Update Statistics
   

    def get_behaviour_model_updates(
        self,
        behaviour_channel=None,
    ):
        

        if behaviour_channel is not None:

            channel = (
                self.__make_behaviour_channel_key(
                    behaviour_channel
                )
            )

            return self.behaviour_model_updates.get(
                channel,
                0,
            )

        return sum(
            self.behaviour_model_updates.values()
        )

    
    # Behaviour CUSUM Summary
  

    def get_behaviour_cusum_summary(
        self,
        behaviour_channel,
    ):
        

        channel = (
            self.__make_behaviour_channel_key(
                behaviour_channel
            )
        )

        detector = (
            self.behaviour_drift_detectors.get(
                channel
            )
        )

        if detector is None:

            return {
                "behaviour_channel": channel,
                "observed_errors": 0,
                "detected_drifts": 0,
                "positive_cusum": 0.0,
                "negative_cusum": 0.0,
                "last_drift_direction": None,
            }

        positive_cusum = 0.0
        negative_cusum = 0.0
        last_drift_direction = None

        if hasattr(
            detector,
            "get_positive_cusum",
        ):

            positive_cusum = float(
                detector.get_positive_cusum()
            )

        if hasattr(
            detector,
            "get_negative_cusum",
        ):

            negative_cusum = float(
                detector.get_negative_cusum()
            )

        if hasattr(
            detector,
            "get_last_drift_direction",
        ):

            last_drift_direction = (
                detector
                .get_last_drift_direction()
            )

        return {
            "behaviour_channel": channel,
            "observed_errors": (
                self.__get_detector_observed_errors(
                    detector
                )
            ),
            "detected_drifts": (
                self.__get_detector_detected_drifts(
                    detector
                )
            ),
            "positive_cusum": (
                positive_cusum
            ),
            "negative_cusum": (
                negative_cusum
            ),
            "last_drift_direction": (
                last_drift_direction
            ),
        }

    
    # Behaviour Summary
    

    def get_behaviour_summary(
        self,
    ):
        

        summary = {}

        for channel in (
            self.ADAPTIVE_BEHAVIOUR_CHANNELS
        ):

            summary[channel] = {
                "observed_errors":
                    self.get_behaviour_observed_errors(
                        channel
                    ),

                "detected_drifts":
                    self.get_behaviour_detected_drifts(
                        channel
                    ),

                "model_updates":
                    self.get_behaviour_model_updates(
                        channel
                    ),

                "current_episode_errors":
                    self.get_current_behaviour_episode_errors(
                        channel
                    ),

                "last_drift_evidence":
                    self.get_last_behaviour_drift_evidence(
                        channel
                    ),

                "cusum":
                    self.get_behaviour_cusum_summary(
                        channel
                    ),
            }

        return summary

   
    # Transition Identification
    

    @staticmethod
    def __make_transition_key(
        current_state,
        next_state,
    ):
        

        if hasattr(
            current_state,
            "name",
        ):
            current_state = (
                current_state.name
            )

        if hasattr(
            next_state,
            "name",
        ):
            next_state = (
                next_state.name
            )

        return (
            str(current_state),
            str(next_state),
        )

    
    # Supported Transition Check
   

    def is_supported_transition(
        self,
        current_state,
        next_state,
    ):
        

        transition = (
            self.__make_transition_key(
                current_state,
                next_state,
            )
        )

        return (
            transition
            in self.ADAPTIVE_TRANSITIONS
        )

    
    # Prediction Error Processing
    

    def observe_transition(
        self,
        current_state,
        next_state,
        probability,
    ):
        

        if (
            not self.enabled
            or self.transition_drift_detector is None
        ):
            return None

        result = (
            self.transition_drift_detector
            .observe_transition(
                current_state=current_state,
                next_state=next_state,
                probability=probability,
            )
        )

        self.transition_observations += 1
        self.last_transition_drift_result = dict(result)

       
        transition_record = dict(result)
        transition_record.update(
            {
                "current_state": current_state,
                "next_state": next_state,
                "probability": probability,
                "surprise": result.get(
                    "last_surprise"
                ),
            }
        )

        if self.transition_adaptation is not None:
            self.transition_adaptation.observe_transition(
                current_state=current_state,
                next_state=next_state,
            )

        if not result.get(
            "drift_detected",
            False,
        ):
            transition_record["drift_detected"] = False
            self.transition_monitoring_history.append(
                transition_record
            )

            return {
                "current_state": current_state,
                "next_state": next_state,
                "probability": probability,
                "surprise": result.get("last_surprise"),
                "cusum": result.get("cusum"),
                "drift_detected": False,
                "adaptation_triggered": False,
                "adaptation": None,
            }

        self.transition_detected_drifts += 1

        
        transition_record["drift_detected"] = True
        self.transition_monitoring_history.append(
            transition_record
        )

        adaptation_triggered = (
            self.transition_adaptation is not None
        )
        adaptation_result = None

        if adaptation_triggered:
            try:
                adaptation_result = (
                    self.transition_adaptation
                    .adapt()
                )
                self.last_transition_adaptation = (
                    adaptation_result
                )
                self.transition_adaptation_history.append(
                    {
                        "current_state": current_state,
                        "next_state": next_state,
                        "adaptation": (
                            dict(adaptation_result)
                            if isinstance(
                                adaptation_result,
                                dict,
                            )
                            else adaptation_result
                        ),
                    }
                )
            except Exception as exc:
                adaptation_result = {
                    "success": False,
                    "error": repr(exc),
                }

        
        self.transition_drift_detector.reset()

        return {
            "current_state": current_state,
            "next_state": next_state,
            "probability": probability,
            "surprise": result.get("last_surprise"),
            "cusum": result.get("cusum"),
            "drift_detected": True,
            "adaptation_triggered": adaptation_triggered,
            "adaptation": adaptation_result,
        }

    
    # Prediction Error Processing
    

    def observe_error(
        self,
        current_state,
        next_state,
        error,
    ):

        
        # 1. Adaptation Disabled
        

        if not self.enabled:

            return None

        
        # 2. Identify Transition
        

        transition = (
            self.__make_transition_key(
                current_state,
                next_state,
            )
        )

        
        # 3. Ignoring Unsupported Transition
       

        if (
            transition
            not in self.ADAPTIVE_TRANSITIONS
        ):

            return None

       
        # 4. Normalize Error
       

        error = float(
            error
        )

        
        # 5. Record Eligible Error
        

        self.observed_errors[
            transition
        ] += 1

       
        # 6. Store Current CUSUM Episode Evidence
        

        self.current_episode_errors[
            transition
        ].append(
            error
        )

        
        # 7. Obtain Transition-Specific Detector
       

        drift_detector = (
            self.drift_detectors.get(
                transition
            )
        )

        
        # No Detector
        

        if drift_detector is None:

            return {
                "transition": transition,
                "error": error,
                "drift_detected": False,
                "drift_direction": None,
                "adaptation_triggered": False,
                "adaptation_successful": False,
                "evidence": list(
                    self.current_episode_errors[
                        transition
                    ]
                ),
                "evidence_count": len(
                    self.current_episode_errors[
                        transition
                    ]
                ),
                "cusum_observed_errors": None,
                "cusum_detected_drifts": None,
            }

       
        # 8. CUSUM Drift Detection
        

        drift_detected = (
            drift_detector.observe(
                error
            )
        )

        
        # 9. No Drift
       

        if not drift_detected:

            return {
                "transition": transition,
                "error": error,
                "drift_detected": False,
                "drift_direction": None,
                "adaptation_triggered": False,
                "adaptation_successful": False,
                "evidence": list(
                    self.current_episode_errors[
                        transition
                    ]
                ),
                "evidence_count": len(
                    self.current_episode_errors[
                        transition
                    ]
                ),
                "cusum_observed_errors": (
                    self.__get_detector_observed_errors(
                        drift_detector
                    )
                ),
                "cusum_detected_drifts": (
                    self.__get_detector_detected_drifts(
                        drift_detector
                    )
                ),
                "cusum_reset": False,
            }

       
        # 10. Drift Detected
        

        self.detected_drifts[
            transition
        ] += 1

        
        # 11. Preserve Complete Drift Evidence
       

        drift_evidence = list(
            self.current_episode_errors[
                transition
            ]
        )

        self.last_drift_evidence[
            transition
        ] = list(
            drift_evidence
        )

       
        # 12. Drift Direction
        

        drift_direction = (
            drift_detector
            .get_last_drift_direction()
            if hasattr(
                drift_detector,
                "get_last_drift_direction",
            )
            else None
        )

        
        # 13. Trigger Behavioural Adaptation
        

        adaptation_triggered = (
            self.adaptation_callback is not None
        )

        adaptation_successful = False

        if adaptation_triggered:

            try:

                result = (
                    self.adaptation_callback(
                        transition,
                        list(
                            drift_evidence
                        ),
                    )
                )

                if result is True:

                    adaptation_successful = True

                    self.model_updates[
                        transition
                    ] += 1

            except Exception as exc:

                adaptation_successful = False

                adaptation_error = (
                    repr(exc)
                )

            else:

                adaptation_error = None

        else:

            adaptation_error = None

        
        # 14. Start a New CUSUM Episode
        

        self.current_episode_errors[
            transition
        ] = []

        
        # 15. Return Complete Adaptation Result
        

        return {
            "transition": transition,
            "error": error,
            "drift_detected": True,
            "drift_direction": drift_direction,
            "adaptation_triggered": (
                adaptation_triggered
            ),
            "adaptation_successful": (
                adaptation_successful
            ),
            "adaptation_error": (
                adaptation_error
            ),
            "evidence": list(
                drift_evidence
            ),
            "evidence_count": len(
                drift_evidence
            ),
            "cusum_observed_errors": (
                self.__get_detector_observed_errors(
                    drift_detector
                )
            ),
            "cusum_detected_drifts": (
                self.__get_detector_detected_drifts(
                    drift_detector
                )
            ),
            "cusum_reset": True,
        }

    
    # Internal Detector Statistics
    

    @staticmethod
    def __get_detector_observed_errors(
        detector,
    ):

        if detector is None:

            return None

        if hasattr(
            detector,
            "get_observed_errors",
        ):

            return detector.get_observed_errors()

        if hasattr(
            detector,
            "observed_errors",
        ):

            return detector.observed_errors

        return None

    

    @staticmethod
    def __get_detector_detected_drifts(
        detector,
    ):

        if detector is None:

            return None

        if hasattr(
            detector,
            "get_detected_drifts",
        ):

            return detector.get_detected_drifts()

        if hasattr(
            detector,
            "detected_drifts",
        ):

            return detector.detected_drifts

        return None

    
    # Episode Evidence Access
    

    def get_current_episode_errors(
        self,
        current_state=None,
        next_state=None,
    ):

        
        # Specific Transition
       

        if (
            current_state is not None
            and next_state is not None
        ):

            transition = (
                self.__make_transition_key(
                    current_state,
                    next_state,
                )
            )

            return list(
                self.current_episode_errors.get(
                    transition,
                    [],
                )
            )

        
        # All Transitions
        

        return {
            transition: list(
                errors
            )
            for (
                transition,
                errors,
            ) in self.current_episode_errors.items()
        }

    
    # Last Drift Evidence Access
    

    def get_last_drift_evidence(
        self,
        current_state=None,
        next_state=None,
    ):

        
        # Specific Transition
        

        if (
            current_state is not None
            and next_state is not None
        ):

            transition = (
                self.__make_transition_key(
                    current_state,
                    next_state,
                )
            )

            return list(
                self.last_drift_evidence.get(
                    transition,
                    [],
                )
            )

       
        # All Transitions
        

        return {
            transition: list(
                errors
            )
            for (
                transition,
                errors,
            ) in self.last_drift_evidence.items()
        }

    
    # Error Statistics
    

    def get_observed_errors(
        self,
        current_state=None,
        next_state=None,
    ):
        

        if (
            current_state is not None
            and next_state is not None
        ):

            transition = (
                self.__make_transition_key(
                    current_state,
                    next_state,
                )
            )

            return self.observed_errors.get(
                transition,
                0,
            )

        return sum(
            self.observed_errors.values()
        )

    
    # Drift Statistics
    

    def get_detected_drifts(
        self,
        current_state=None,
        next_state=None,
    ):
        

        if (
            current_state is not None
            and next_state is not None
        ):

            transition = (
                self.__make_transition_key(
                    current_state,
                    next_state,
                )
            )

            return self.detected_drifts.get(
                transition,
                0,
            )

        return sum(
            self.detected_drifts.values()
        )

    
    # Behavioural Model Update Statistics
    

    def get_model_updates(
        self,
        current_state=None,
        next_state=None,
    ):

        if (
            current_state is not None
            and next_state is not None
        ):

            transition = (
                self.__make_transition_key(
                    current_state,
                    next_state,
                )
            )

            return self.model_updates.get(
                transition,
                0,
            )

        return sum(
            self.model_updates.values()
        )

    
    # CUSUM Summary
    

    def get_cusum_summary(
        self,
        current_state,
        next_state,
    ):

        transition = (
            self.__make_transition_key(
                current_state,
                next_state,
            )
        )

        detector = (
            self.drift_detectors.get(
                transition
            )
        )

        if detector is None:

            return {
                "transition": transition,
                "observed_errors": 0,
                "detected_drifts": 0,
                "positive_cusum": 0.0,
                "negative_cusum": 0.0,
                "last_drift_direction": None,
            }

        positive_cusum = 0.0

        negative_cusum = 0.0

        last_drift_direction = None

        if hasattr(
            detector,
            "get_positive_cusum",
        ):

            positive_cusum = float(
                detector
                .get_positive_cusum()
            )

        if hasattr(
            detector,
            "get_negative_cusum",
        ):

            negative_cusum = float(
                detector
                .get_negative_cusum()
            )

        if hasattr(
            detector,
            "get_last_drift_direction",
        ):

            last_drift_direction = (
                detector
                .get_last_drift_direction()
            )

        return {
            "transition": transition,
            "observed_errors": (
                self.__get_detector_observed_errors(
                    detector
                )
            ),
            "detected_drifts": (
                self.__get_detector_detected_drifts(
                    detector
                )
            ),
            "positive_cusum": (
                positive_cusum
            ),
            "negative_cusum": (
                negative_cusum
            ),
            "last_drift_direction": (
                last_drift_direction
            ),
        }

    
    # Transition Summary
    

    def get_transition_summary(
        self,
    ):

        summary = {}

        for transition in (
            self.ADAPTIVE_TRANSITIONS
        ):

            current_state = (
                transition[0]
            )

            next_state = (
                transition[1]
            )

            cusum_summary = (
                self.get_cusum_summary(
                    current_state,
                    next_state,
                )
            )

            summary[transition] = {

                "observed_errors":
                    self.get_observed_errors(
                        current_state,
                        next_state,
                    ),

                "detected_drifts":
                    self.get_detected_drifts(
                        current_state,
                        next_state,
                    ),

                "model_updates":
                    self.get_model_updates(
                        current_state,
                        next_state,
                    ),

                "current_episode_errors":
                    self.get_current_episode_errors(
                        current_state,
                        next_state,
                    ),

                "last_drift_evidence":
                    self.get_last_drift_evidence(
                        current_state,
                        next_state,
                    ),

                "cusum":
                    cusum_summary,
            }

        return summary

    
    # Reset Transition Channel
    

    def reset_transition(
        self,
        current_state,
        next_state,
    ):
        

        transition = (
            self.__make_transition_key(
                current_state,
                next_state,
            )
        )

        
        # Reset Detector
        

        detector = (
            self.drift_detectors.get(
                transition
            )
        )

        if detector is not None:

            if hasattr(
                detector,
                "reset",
            ):

                detector.reset()

        
        # Clear Current Episode
        

        if transition in (
            self.current_episode_errors
        ):

            self.current_episode_errors[
                transition
            ] = []

        
        # Clear Last Drift Evidence
        

        if transition in (
            self.last_drift_evidence
        ):

            self.last_drift_evidence[
                transition
            ] = []

    
    # Reset Behaviour Channel
    

    def reset_behaviour_channel(
        self,
        behaviour_channel,
    ):
    

        channel = (
            self.__make_behaviour_channel_key(
                behaviour_channel
            )
        )

        if (
            channel
            not in self.ADAPTIVE_BEHAVIOUR_CHANNELS
        ):

            return False

        
        # Reset Detector
        

        detector = (
            self.behaviour_drift_detectors.get(
                channel
            )
        )

        if detector is not None:

            if hasattr(
                detector,
                "reset",
            ):

                detector.reset()

       
        # Clear Current Episode
        

        self.behaviour_episode_errors[
            channel
        ] = []

        
        # Clear Last Drift Evidence
        

        self.last_behaviour_drift_evidence[
            channel
        ] = []

        return True



    def get_transition_monitoring_history(
        self,
    ):
        
        return [
            dict(record)
            for record in self.transition_monitoring_history
        ]

    def get_transition_adaptation_history(
        self,
    ):
        
        return [
            dict(record)
            for record in self.transition_adaptation_history
        ]

    # Transition Drift Summary
    

    def get_transition_drift_summary(
        self,
    ):
        

        confirmed_history_drifts = sum(
            1
            for record in self.transition_monitoring_history
            if record.get("drift_detected", False)
        )

        
        detected_drifts = max(
            self.transition_detected_drifts,
            confirmed_history_drifts,
        )

        if self.transition_drift_detector is None:
            return {
                "enabled": False,
                "observations": self.transition_observations,
                "detected_drifts": detected_drifts,
                "confirmed_history_drifts": confirmed_history_drifts,
                "detector": None,
            }

        return {
            "enabled": True,
            "observations": self.transition_observations,
            "detected_drifts": detected_drifts,
            "confirmed_history_drifts": confirmed_history_drifts,
            "detector": self.transition_drift_detector.get_status(),
        }

    
    # Transition Adaptation Summary
    

    def get_transition_adaptation_summary(
        self,
    ):


        confirmed_history_adaptations = len(
            self.transition_adaptation_history
        )

        if self.transition_adaptation is None:
            return {
                "enabled": False,
                "last_adaptation": None,
                "adaptation_count": confirmed_history_adaptations,
                "confirmed_history_adaptations": (
                    confirmed_history_adaptations
                ),
            }

        adaptation_count = max(
            self.transition_adaptation.get_adaptation_count(),
            confirmed_history_adaptations,
        )

        return {
            "enabled": True,
            "last_adaptation": self.transition_adaptation.get_last_adaptation(),
            "adaptation_count": adaptation_count,
            "confirmed_history_adaptations": (
                confirmed_history_adaptations
            ),
            "sliding_window_matrix": self.transition_adaptation.get_sliding_window_matrix(),
            "bayesian_matrix": self.transition_adaptation.get_bayesian_matrix(),
            "evaluation": self.transition_adaptation.get_evaluation_metrics(),
        }

    def get_transition_branch_evaluation_history(
        self,
    ):
        """Return the Point-4 side-by-side branch evaluation history."""
        if self.transition_adaptation is None:
            return []
        return self.transition_adaptation.get_branch_evaluation_history()


    def get_transition_monitoring_summary(
        self,
    ):

        return {
            "drift_detection": self.get_transition_drift_summary(),
            "adaptation": self.get_transition_adaptation_summary(),
            "monitoring_history": (
                self.get_transition_monitoring_history()
            ),
            "adaptation_history": (
                self.get_transition_adaptation_history()
            ),
            "branch_evaluation_history": (
                self.get_transition_branch_evaluation_history()
            ),
        }
    def reset(
        self,
    ): 

        if self.transition_drift_detector is not None:
            self.transition_drift_detector.reset()

        self.transition_observations = 0
        self.transition_detected_drifts = 0
        self.last_transition_drift_result = None
        self.last_transition_adaptation = None
        self.transition_monitoring_history.clear()
        self.transition_adaptation_history.clear()


        
        # Reset Transition Channels
        

        for transition in (
            self.ADAPTIVE_TRANSITIONS
        ):

            self.reset_transition(
                transition[0],
                transition[1],
            )

        
        # Reset Behaviour Channels
        

        for channel in (
            self.ADAPTIVE_BEHAVIOUR_CHANNELS
        ):

            self.reset_behaviour_channel(
                channel
            )

        
        # Reset Statistics
        

        self.observed_errors.clear()

        self.detected_drifts.clear()

        self.model_updates.clear()

        self.behaviour_observed_errors.clear()

        self.behaviour_detected_drifts.clear()

        self.behaviour_model_updates.clear()

   
    # Reset Statistics Only
    

    def reset_statistics(
        self,
    ):
        
        self.transition_observations = 0
        self.transition_detected_drifts = 0
        self.last_transition_drift_result = None
        self.last_transition_adaptation = None
        self.transition_monitoring_history.clear()
        self.transition_adaptation_history.clear()


        self.observed_errors.clear()

        self.detected_drifts.clear()

        self.model_updates.clear()

        self.behaviour_observed_errors.clear()

        self.behaviour_detected_drifts.clear()

        self.behaviour_model_updates.clear()

    
    # Adaptation State
    

    def is_enabled(
        self,
    ):
        """
        Return True when adaptive synchronization is enabled.
        """

        return self.enabled

    
    # Supported Transitions
    

    def get_supported_transitions(
        self,
    ):
        

        return set(
            self.ADAPTIVE_TRANSITIONS
        )

    
    # Supported Behaviour Channels
    

    def get_supported_behaviour_channels(
        self,
    ):
        

        return set(
            self.ADAPTIVE_BEHAVIOUR_CHANNELS
        )

    
    # Detector Access
    

    def get_drift_detector(
        self,
        current_state,
        next_state,
    ):
        

        transition = (
            self.__make_transition_key(
                current_state,
                next_state,
            )
        )

        return self.drift_detectors.get(
            transition
        )

    
    # Behaviour Detector Access
    

    def get_behaviour_drift_detector(
        self,
        behaviour_channel,
    ):
        

        channel = (
            self.__make_behaviour_channel_key(
                behaviour_channel
            )
        )

        return (
            self.behaviour_drift_detectors.get(
                channel
            )
        )

    
    # Complete Adaptation Summary
    

    def get_summary(
        self,
    ):
        

        return {
            
            # Point 3: Categorical Transition Drift
           

            "transition_drift_monitoring": (
                self.get_transition_drift_summary()
            ),

            
            # Point 4: Parallel Transition Adaptation
            

            "transition_adaptation": (
                self.get_transition_adaptation_summary()
            ),

            "enabled": self.enabled,

            
            # Machine-State Transition Adaptation
            

            "transitions": (
                self.get_transition_summary()
            ),

            
            # Behavioural Timing Adaptation
            

            "behaviour_channels": (
                self.get_behaviour_summary()
            ),

            
            # Aggregate Statistics
           

            "total_observed_errors": (
                self.get_observed_errors()
            ),

            "total_detected_drifts": (
                self.get_detected_drifts()
            ),

            "total_model_updates": (
                self.get_model_updates()
            ),

            "total_behaviour_observed_errors": (
                self.get_behaviour_observed_errors()
            ),

            "total_behaviour_detected_drifts": (
                self.get_behaviour_detected_drifts()
            ),

            "total_behaviour_model_updates": (
                self.get_behaviour_model_updates()
            ),
        }

    

    def __repr__(
        self,
    ):
        

        return (
            "AdaptationManager("
            f"enabled={self.enabled}, "
            f"transitions="
            f"{len(self.ADAPTIVE_TRANSITIONS)}, "
            f"behaviour_channels="
            f"{len(self.ADAPTIVE_BEHAVIOUR_CHANNELS)}, "
            f"detected_drifts="
            f"{self.get_detected_drifts()}, "
            f"behaviour_drifts="
            f"{self.get_behaviour_detected_drifts()}"
            ")"
        )