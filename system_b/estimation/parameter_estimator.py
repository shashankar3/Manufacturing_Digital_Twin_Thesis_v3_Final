import numpy as np
from scipy import stats


class ParameterEstimator:
    

    MIN_STANDARD_DEVIATION = 1e-8

   
    # Descriptive Statistics
    

    def descriptive_statistics(self, samples):
       

        if samples is None:

            return {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        samples = np.asarray(
            samples,
            dtype=float,
        )

        samples = samples[
            np.isfinite(samples)
        ]

        if len(samples) == 0:

            return {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        return {
            "count": int(len(samples)),
            "mean": float(np.mean(samples)),
            "std": float(np.std(samples)),
            "min": float(np.min(samples)),
            "max": float(np.max(samples)),
        }


    # Distribution Parameter Estimation
    

    def estimate(self, samples):
        

        # Minimum Sample Requirement
        

        if samples is None:

            return {}

        if len(samples) < 2:

            return {}

        samples = np.asarray(
            samples,
            dtype=float,
        )

      
        # Remove Invalid Values
       

        samples = samples[
            np.isfinite(samples)
        ]

        if len(samples) < 2:

            return {}

        
        # Check Variability
        

        sample_std = np.std(
            samples
        )

        if sample_std <= self.MIN_STANDARD_DEVIATION:

            return {}

        estimates = {}

     
        # Normal Distribution
      

        try:

            mu, sigma = stats.norm.fit(
                samples
            )

            if (
                np.isfinite(mu)
                and np.isfinite(sigma)
                and sigma > 0.0
            ):

                estimates["normal"] = {
                    "mu": float(mu),
                    "sigma": float(sigma),
                }

        except Exception:
            pass

        
        # Lognormal Distribution
        

        if np.all(samples > 0.0):

            try:

                shape, loc, scale = (
                    stats.lognorm.fit(
                        samples,
                        floc=0,
                    )
                )

                if (
                    np.isfinite(shape)
                    and np.isfinite(loc)
                    and np.isfinite(scale)
                    and shape > 0.0
                    and scale > 0.0
                ):

                    estimates["lognormal"] = {
                        "shape": float(shape),
                        "loc": float(loc),
                        "scale": float(scale),
                    }

            except Exception:
                pass

        
        # Gamma Distribution
       

        if np.all(samples > 0.0):

            try:

                shape, loc, scale = (
                    stats.gamma.fit(
                        samples,
                        floc=0,
                    )
                )

                if (
                    np.isfinite(shape)
                    and np.isfinite(loc)
                    and np.isfinite(scale)
                    and shape > 0.0
                    and scale > 0.0
                ):

                    estimates["gamma"] = {
                        "shape": float(shape),
                        "loc": float(loc),
                        "scale": float(scale),
                    }

            except Exception:
                pass

       
        # Weibull Distribution
       

        if np.all(samples >= 0.0):

            try:

                shape, loc, scale = (
                    stats.weibull_min.fit(
                        samples,
                        floc=0,
                    )
                )

                if (
                    np.isfinite(shape)
                    and np.isfinite(loc)
                    and np.isfinite(scale)
                    and shape > 0.0
                    and scale > 0.0
                ):

                    estimates["weibull"] = {
                        "shape": float(shape),
                        "loc": float(loc),
                        "scale": float(scale),
                    }

            except Exception:
                pass

      
        # Exponential Distribution
       

        if np.all(samples >= 0.0):

            try:

                loc, scale = (
                    stats.expon.fit(
                        samples,
                        floc=0,
                    )
                )

                if (
                    np.isfinite(loc)
                    and np.isfinite(scale)
                    and scale > 0.0
                ):

                    estimates["exponential"] = {
                        "loc": float(loc),
                        "scale": float(scale),
                    }

            except Exception:
                pass

        return estimates

   
    # Worker-Conditioned Parameter Estimation
    

    def estimate_worker_parameters(
        self,
        worker_samples,
    ):

        if worker_samples is None:

            return {}

        if not isinstance(
            worker_samples,
            dict,
        ):

            return {}

        estimates_by_worker = {}

        for worker_id, samples in worker_samples.items():

            if worker_id is None:

                continue

            worker_id = str(
                worker_id
            )

            estimates = self.estimate(
                samples
            )

            if estimates:

                estimates_by_worker[
                    worker_id
                ] = estimates

        return estimates_by_worker

   
    # Worker Descriptive Statistics
   

    def worker_descriptive_statistics(
        self,
        worker_samples,
    ):

        if worker_samples is None:

            return {}

        if not isinstance(
            worker_samples,
            dict,
        ):

            return {}

        statistics_by_worker = {}

        for worker_id, samples in worker_samples.items():

            if worker_id is None:

                continue

            worker_id = str(
                worker_id
            )

            statistics_by_worker[
                worker_id
            ] = self.descriptive_statistics(
                samples
            )

        return statistics_by_worker