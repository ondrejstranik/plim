import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt


class BindingModelFitter:
    """
    Fits the two-state analytical binding model to experimental data:
        R(t) = Req * (1 - C1*exp(-ka2*τ) - (1-C1)*exp(-κ*τ))   for t > t0
        R(t) = 0                                                   for t <= t0
    where τ = t - t0.

    Parameters
    ----------
    t_exp : array-like   Experimental time points
    y_exp : array-like   Experimental signal values
    fixed  : dict        Map of param name → float to fix, None to fit,
                         or "derived" if computed in compute_derived()
    bounds : dict        Map of param name → (min, max)
    guess  : dict        Map of param name → initial guess
    n_starts : int       Number of random multi-starts (default 9 + base)
    seed     : int       Random seed for reproducibility
    """

    ALL_PARAMS = ["Req", "C1", "ka2", "kap", "t0"]

    DEFAULT_FIXED = {
        "Req": None,
        "C1":  None,
        "ka2": None,
        "kap": None,
        "t0":  None,
    }

    DEFAULT_BOUNDS = {
        "Req": (1e-6, 1e6),
        "C1":  (0.0,  1.0),
        "ka2": (1e-6, 1e2),
        "kap": (1e-6, 1e2),
        "t0":  (None, None),   # set dynamically from t_exp
    }

    DEFAULT_GUESS = {
        "Req": 1.0,
        "C1":  0.5,
        "ka2": 0.5,
        "kap": 0.1,
        "t0":  None,           # set dynamically as midpoint of t_exp
    }

    def __init__(self, t_exp, y_exp, fixed=None, bounds=None, guess=None,
                 n_starts=9, seed=42):
        self.t_exp = np.asarray(t_exp, dtype=float)
        self.y_exp = np.asarray(y_exp, dtype=float)
        self.n_starts = n_starts
        self.rng = np.random.default_rng(seed)

        # merge user-supplied dicts with defaults
        self.fixed  = {**self.DEFAULT_FIXED,  **(fixed  or {})}
        self.bounds = {**self.DEFAULT_BOUNDS,  **(bounds or {})}
        self.guess  = {**self.DEFAULT_GUESS,   **(guess  or {})}

        # fill dynamic defaults
        t0, t1 = self.t_exp[0], self.t_exp[-1]
        if self.bounds["t0"] == (None, None):
            self.bounds["t0"] = (t0, t1)
        if self.guess["t0"] is None:
            self.guess["t0"] = 0.5 * (t0 + t1)

        # categorise parameters
        self.free_params    = [p for p in self.ALL_PARAMS if self.fixed[p] is None]
        self.fixed_params   = {p: v for p, v in self.fixed.items()
                               if isinstance(v, (float, int))}
        self.derived_params = [p for p in self.ALL_PARAMS
                               if self.fixed[p] == "derived"]

        self.result_ = None   # filled after fit()

    # ── Parameter helpers ────────────────────────────────────────────────────
    def compute_derived(self, d):
        """Override to add derived parameter relationships."""
        return d

    def _pack(self, param_dict):
        return [param_dict[p] for p in self.free_params]

    def _unpack(self, vec):
        d = dict(zip(self.free_params, vec))
        d.update(self.fixed_params)
        return self.compute_derived(d)

    # ── Model ────────────────────────────────────────────────────────────────
    def predict(self, t, params=None):
        """
        Evaluate the model at times t.
        Uses best-fit parameters if params is None (after fit() has been called).
        """
        if params is None:
            if self.result_ is None:
                raise RuntimeError("Call fit() before predict().")
            params = self.result_["params"]
        Req, C1, ka2, kap, t0 = (
            params["Req"], params["C1"], params["ka2"], params["kap"], params["t0"]
        )
        tau = np.maximum(t - t0, 0.0)
        return np.where(
            t > t0,
            Req * (1 - C1 * np.exp(-ka2 * tau) - (1 - C1) * np.exp(-kap * tau)),
            0.0,
        )

    # ── Cost ─────────────────────────────────────────────────────────────────
    def _cost(self, vec):
        p = self._unpack(vec)
        return np.sum((self.predict(self.t_exp, p) - self.y_exp) ** 2)

    # ── Fit ──────────────────────────────────────────────────────────────────
    def fit(self):
        """Run multi-start L-BFGS-B optimisation. Returns self."""
        bounds_free = [self.bounds[p] for p in self.free_params]
        base_guess  = self._pack(self.guess)

        guesses = [base_guess] + [
            [np.clip(v * self.rng.uniform(0.5, 2.0), lo, hi)
             for v, (lo, hi) in zip(base_guess, bounds_free)]
            for _ in range(self.n_starts)
        ]

        best_res, best_cost = None, np.inf
        for g in guesses:
            res = minimize(
                self._cost, x0=g, method="L-BFGS-B", bounds=bounds_free,
                options={"ftol": 1e-12, "gtol": 1e-10, "maxiter": 50_000},
            )
            if res.fun < best_cost:
                best_cost, best_res = res.fun, res

        best_params = self._unpack(best_res.x)
        self.result_ = {
            "params":  best_params,
            "SSE":     best_cost,
            "RMSE":    np.sqrt(best_cost / len(self.t_exp)),
            "success": best_res.success,
            "message": best_res.message,
        }
        return self

    # ── Reporting ────────────────────────────────────────────────────────────
    def summary(self):
        """Print a summary of the fit results."""
        if self.result_ is None:
            raise RuntimeError("Call fit() first.")
        p = self.result_["params"]
        print("=" * 45)
        for name in self.ALL_PARAMS:
            tag = ("(fixed)"   if name in self.fixed_params   else
                   "(derived)" if name in self.derived_params else "")
            print(f"  {name:<6} = {p[name]:.6f}  {tag}")
        print(f"  SSE    = {self.result_['SSE']:.6e}")
        print(f"  RMSE   = {self.result_['RMSE']:.6e}")
        print("=" * 45)

    def plot(self, n_points=500,ax=None):
        """Plot experimental data and fitted model."""
        if self.result_ is None:
            raise RuntimeError("Call fit() first.")
        t_fine = np.linspace(self.t_exp[0], self.t_exp[-1], n_points)
        y_fit  = self.predict(t_fine)
        t0     = self.result_["params"]["t0"]

        if ax is None:
            fig, ax = plt.subplots()
            #plt.figure(figsize=(7, 4))
            ax.scatter(self.t_exp, self.y_exp, label="Experimental data",
                        color="steelblue", zorder=5)
            ax.plot(t_fine, y_fit, label="Fitted model", color="tomato", lw=2)
            ax.axvline(t0, color="gray", linestyle="--")
            #ax.axvline(t0, color="gray", linestyle="--", label=f"t0 = {t0:.2f}")
            ax.set_xlabel("Time [s]")
            ax.set_ylabel("Signal [nm]")
            ax.set_title("Data Fit")
            ax.legend()
            fig.tight_layout()

            return fig, ax

            #plt.savefig("fit_result.png", dpi=150)
            #plt.show()
        else:
            ax.scatter(self.t_exp, self.y_exp, label="Experimental data",
                        color="steelblue", zorder=5)
            ax.plot(t_fine, y_fit, label="Fitted model", color="tomato", lw=2)
            ax.axvline(t0, color="gray", linestyle="--", label=f"t0 = {t0:.2f}")



# ── Usage ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # Replace with your actual data
    t_exp = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    y_exp = np.array([0, 0.0, 0.0, 0.4, 0.55, 0.65, 0.72, 0.77, 0.80, 0.82, 0.83])

    # Example: fix t0, let everything else be free
    fitter = BindingModelFitter(
        t_exp, y_exp,
        fixed={"t0": 2.0},          # fix t0 at 2.0
        guess={"Req": 0.9, "C1": 0.6},
    )

    fitter.fit()
    fitter.summary()
    fitter.plot()

    # Access results programmatically
    print("ka2 =", fitter.result_["params"]["ka2"])