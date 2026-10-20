from scipy import stats


class DistributionFitter:
    
    # Generic Distribution Fitting
    

    def fit(self, estimated_parameters):
        

        fitted_distributions = {}

        if not estimated_parameters:

            return fitted_distributions

        
        # Normal
       

        if "normal" in estimated_parameters:

            p = estimated_parameters["normal"]

            try:

                sigma = float(
                    p["sigma"]
                )

                if sigma <= 0.0:

                    raise ValueError(
                        "Normal distribution scale must be positive."
                    )

                fitted_distributions["normal"] = (
                    stats.norm(
                        loc=float(
                            p["mu"]
                        ),
                        scale=sigma,
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                pass

       
        # Lognormal
        

        if "lognormal" in estimated_parameters:

            p = estimated_parameters["lognormal"]

            try:

                shape = float(
                    p["shape"]
                )

                loc = float(
                    p["loc"]
                )

                scale = float(
                    p["scale"]
                )

                if (
                    shape <= 0.0
                    or scale <= 0.0
                ):

                    raise ValueError(
                        "Lognormal shape and scale "
                        "must be positive."
                    )

                fitted_distributions["lognormal"] = (
                    stats.lognorm(
                        s=shape,
                        loc=loc,
                        scale=scale,
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                pass

        
        # Gamma
        

        if "gamma" in estimated_parameters:

            p = estimated_parameters["gamma"]

            try:

                shape = float(
                    p["shape"]
                )

                loc = float(
                    p["loc"]
                )

                scale = float(
                    p["scale"]
                )

                if (
                    shape <= 0.0
                    or scale <= 0.0
                ):

                    raise ValueError(
                        "Gamma shape and scale "
                        "must be positive."
                    )

                fitted_distributions["gamma"] = (
                    stats.gamma(
                        a=shape,
                        loc=loc,
                        scale=scale,
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                pass

        
        # Weibull
       

        if "weibull" in estimated_parameters:

            p = estimated_parameters["weibull"]

            try:

                shape = float(
                    p["shape"]
                )

                loc = float(
                    p["loc"]
                )

                scale = float(
                    p["scale"]
                )

                if (
                    shape <= 0.0
                    or scale <= 0.0
                ):

                    raise ValueError(
                        "Weibull shape and scale "
                        "must be positive."
                    )

                fitted_distributions["weibull"] = (
                    stats.weibull_min(
                        c=shape,
                        loc=loc,
                        scale=scale,
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                pass

        
        # Exponential
        

        if "exponential" in estimated_parameters:

            p = estimated_parameters["exponential"]

            try:

                loc = float(
                    p["loc"]
                )

                scale = float(
                    p["scale"]
                )

                if scale <= 0.0:

                    raise ValueError(
                        "Exponential scale "
                        "must be positive."
                    )

                fitted_distributions["exponential"] = (
                    stats.expon(
                        loc=loc,
                        scale=scale,
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                pass

        return fitted_distributions

    
    # Worker-Conditioned Distribution Fitting
    

    def fit_worker_distributions(
        self,
        worker_parameters,
    ):

        if worker_parameters is None:

            return {}

        if not isinstance(
            worker_parameters,
            dict,
        ):

            return {}

        fitted_by_worker = {}

        for worker_id, parameters in (
            worker_parameters.items()
        ):

            if worker_id is None:

                continue

            worker_id = str(
                worker_id
            )

            fitted = self.fit(
                parameters
            )

            if fitted:

                fitted_by_worker[
                    worker_id
                ] = fitted

        return fitted_by_worker