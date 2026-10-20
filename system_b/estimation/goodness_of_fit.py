import numpy as np
from scipy import stats


class GoodnessOfFit:

  
    # Single Dataset Evaluation
    

    def evaluate(
        self,
        samples,
        fitted_distributions,
    ):
        

        if samples is None:

            return None

        if fitted_distributions is None:

            return None

        if len(samples) < 2:

            return None

        samples = np.asarray(
            samples,
            dtype=float,
        )

        samples = samples[
            np.isfinite(samples)
        ]

        if len(samples) < 2:

            return None

        if not fitted_distributions:

            return None

        best_distribution = None

        best_result = None

        best_statistic = float(
            "inf"
        )

        
        # Evaluate Every Candidate Distribution
        

        for (
            name,
            distribution,
        ) in fitted_distributions.items():

            try:

                statistic, p_value = (
                    stats.kstest(
                        samples,
                        distribution.cdf,
                    )
                )

            except Exception:

                continue

            
            # Invalid statistic
            

            if not np.isfinite(
                statistic
            ):

                continue

            
            # Invalid p-value
           

            if not np.isfinite(
                p_value
            ):

                p_value = 0.0

           
            # Select smallest KS statistic
            

            if statistic < best_statistic:

                best_statistic = statistic

                best_distribution = name

                best_result = {
                    "distribution": best_distribution,
                    "distribution_object": distribution,
                    "ks_statistic": float(
                        statistic
                    ),
                    "p_value": float(
                        p_value
                    ),
                }

        return best_result

   
    # Worker-Conditioned Evaluation
  

    def evaluate_workers(
        self,
        worker_samples,
        worker_distributions,
    ):

        if worker_samples is None:

            return {}

        if worker_distributions is None:

            return {}

        if not isinstance(
            worker_samples,
            dict,
        ):

            return {}

        if not isinstance(
            worker_distributions,
            dict,
        ):

            return {}

        results = {}

        for (
            worker_id,
            samples,
        ) in worker_samples.items():

            if worker_id is None:

                continue

            worker_id = str(
                worker_id
            )

            fitted = worker_distributions.get(
                worker_id
            )

            if not fitted:

                continue

            result = self.evaluate(
                samples,
                fitted,
            )

            if result is not None:

                results[
                    worker_id
                ] = result

        return results