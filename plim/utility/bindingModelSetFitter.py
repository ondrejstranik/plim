import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt


class GlobalLocalFitter:
    """
    Fits an analytical model to multiple curves simultaneously.
    Parameters can be:
      - global  : shared across all curves (one value fitted for all)
      - local   : fitted independently per curve
      - fixed   : fixed at a given float value (same for all curves)
      - derived : computed from other parameters via compute_derived()

    Model
    -----
    R(t) = Req * (1 - C1*exp(-ka2*τ) - (1-C1)*exp(-κ*τ))  for t > t0
    R(t) = 0                                                 for t <= t0
    where τ = t - t0

    Parameters
    ----------
    datasets : list of (t, y) tuples, one per curve
    global_params  : list of param names to fit globally
    local_params   : list of param names to fit per curve
    fixed          : dict of param → float  (fixed values)
    bounds         : dict of param → (min, max)
    guess          : dict of param → float (or list of floats for local params)
    n_starts       : number of random multi-starts
    seed           : random seed

    Example
    -------
    fitter = GlobalLocalFitter(
        datasets=[(t1, y1), (t2, y2), (t3, y3)],
        global_params=["ka2", "kap", "C1"],
        local_params=["Req", "t0"],
    )
    fitter.fit()
    fitter.summary()
    fitter.plot()
    """

    ALL_PARAMS = ["Req", "C1", "ka2", "kap", "t0"]

    DEFAULT_BOUNDS = {
        "Req": (1e-6, 1e6),
        "C1":  (0.0,  1.0),
        "ka2": (1e-6, 1e2),
        "kap": (1e-6, 1e2),
        "t0":  (0.0,  None),   # upper bound set dynamically
    }

    DEFAULT_GUESS = {
        "Req": 1.0,
        "C1":  0.5,
        "ka2": 0.5,
        "kap": 0.1,
        "t0":  None,           # set dynamically per curve
    }

    def __init__(self, datasets, global_params, local_params,
                 fixed=None, bounds=None, guess=None,
                 n_starts=9, seed=42):

        self.datasets       = [(np.asarray(t, float), np.asarray(y, float))
                               for t, y in datasets]
        self.n_curves       = len(datasets)
        self.global_params  = global_params
        self.local_params   = local_params
        self.fixed          = fixed or {}
        self.bounds         = {**self.DEFAULT_BOUNDS,  **(bounds or {})}
        self.guess          = {**self.DEFAULT_GUESS,   **(guess  or {})}
        self.n_starts       = n_starts
        self.rng            = np.random.default_rng(seed)
        self.result_        = None

        # validate
        all_free = set(global_params) | set(local_params)
        all_fixed = set(self.fixed.keys())
        unknown = (all_free | all_fixed) - set(self.ALL_PARAMS)
        assert not unknown, f"Unknown parameters: {unknown}"
        overlap = set(global_params) & set(local_params)
        assert not overlap, f"Parameters cannot be both global and local: {overlap}"

        # fill dynamic defaults for t0 bounds and guess
        for i, (t, _) in enumerate(self.datasets):
            if self.bounds["t0"][1] is None:
                self.bounds["t0"] = (self.bounds["t0"][0], max(t))
        if self.guess["t0"] is None:
            self.guess["t0"] = np.mean([0.5 * (t[0] + t[-1])
                                        for t, _ in self.datasets])

    # ── Derived parameters (override in subclass) ────────────────────────────
    def compute_derived(self, d):
        return d

    # ── Parameter vector layout ──────────────────────────────────────────────
    # Vector structure:
    #   [ global_params... | curve0_local_params... | curve1_local_params... | ... ]

    def _build_vector(self, global_vals, local_vals_list):
        """Pack global + per-curve local values into one flat vector."""
        vec = list(global_vals)
        for lv in local_vals_list:
            vec.extend(lv)
        return np.array(vec)

    def _split_vector(self, vec):
        """Unpack flat vector into global values and per-curve local values."""
        n_global = len(self.global_params)
        n_local  = len(self.local_params)
        global_vals = vec[:n_global]
        local_vals_list = [
            vec[n_global + i * n_local: n_global + (i + 1) * n_local]
            for i in range(self.n_curves)
        ]
        return global_vals, local_vals_list

    def _make_param_dict(self, global_vals, local_vals, curve_idx=None):
        """Build a full parameter dict for one curve."""
        d = dict(self.fixed)
        d.update(zip(self.global_params, global_vals))
        d.update(zip(self.local_params,  local_vals))
        return self.compute_derived(d)

    def _build_bounds(self):
        """Build bounds list matching the flat parameter vector."""
        b = [self.bounds[p] for p in self.global_params]
        for _ in range(self.n_curves):
            b += [self.bounds[p] for p in self.local_params]
        return b

    def _build_guess(self):
        """Build initial guess vector."""
        g_global = [self.guess[p] for p in self.global_params]
        g_local  = [self.guess[p] for p in self.local_params]
        return self._build_vector(g_global, [g_local] * self.n_curves)

    # ── Model ────────────────────────────────────────────────────────────────
    def predict(self, t, params):
        Req = params["Req"]
        C1  = params["C1"]
        ka2 = params["ka2"]
        kap = params["kap"]
        t0  = params["t0"]
        tau = np.maximum(t - t0, 0.0)
        return np.where(
            t > t0,
            Req * (1 - C1 * np.exp(-ka2 * tau) - (1 - C1) * np.exp(-kap * tau)),
            0.0,
        )

    # ── Cost ─────────────────────────────────────────────────────────────────
    def _cost(self, vec):
        global_vals, local_vals_list = self._split_vector(vec)
        total = 0.0
        for i, (t, y) in enumerate(self.datasets):
            p = self._make_param_dict(global_vals, local_vals_list[i], i)
            residuals = self.predict(t, p) - y
            total += np.sum(residuals ** 2)
        return total

    # ── Fit ──────────────────────────────────────────────────────────────────
    def fit(self):
        bounds_list = self._build_bounds()
        base_guess  = self._build_guess()

        # clip base guess to bounds
        base_guess = np.array([
            np.clip(v, lo, hi if hi is not None else np.inf)
            for v, (lo, hi) in zip(base_guess, bounds_list)
        ])

        guesses = [base_guess] + [
            np.array([
                np.clip(v * self.rng.uniform(0.5, 2.0),
                        lo, hi if hi is not None else np.inf)
                for v, (lo, hi) in zip(base_guess, bounds_list)
            ])
            for _ in range(self.n_starts)
        ]

        best_res, best_cost = None, np.inf
        for g in guesses:
            res = minimize(
                self._cost, x0=g, method="L-BFGS-B", bounds=bounds_list,
                options={"ftol": 1e-12, "gtol": 1e-10, "maxiter": 50_000},
            )
            if res.fun < best_cost:
                best_cost, best_res = res.fun, res

        global_vals, local_vals_list = self._split_vector(best_res.x)

        self.result_ = {
            "global": dict(zip(self.global_params, global_vals)),
            "local":  [dict(zip(self.local_params, lv))
                       for lv in local_vals_list],
            "params": [self._make_param_dict(global_vals, lv)
                       for lv in local_vals_list],
            "SSE":    best_cost,
            "RMSE":   np.sqrt(best_cost / sum(len(y) for _, y in self.datasets)),
        }
        return self

    # ── Reporting ────────────────────────────────────────────────────────────
    def summary(self):
        if self.result_ is None:
            raise RuntimeError("Call fit() first.")

        print("=" * 50)
        print("  GLOBAL parameters:")
        for k, v in self.result_["global"].items():
            print(f"    {k:<8} = {v:.6f}")

        print("  LOCAL parameters:")
        for i, lp in enumerate(self.result_["local"]):
            print(f"    curve {i}:")
            for k, v in lp.items():
                print(f"      {k:<8} = {v:.6f}")

        if self.fixed:
            print("  FIXED parameters:")
            for k, v in self.fixed.items():
                print(f"    {k:<8} = {v:.6f}")

        print(f"  SSE    = {self.result_['SSE']:.6e}")
        print(f"  RMSE   = {self.result_['RMSE']:.6e}")
        print("=" * 50)

    def plot(self, n_points=500, labels=None):
        if self.result_ is None:
            raise RuntimeError("Call fit() first.")

        fig, ax = plt.subplots(figsize=(8, 4))
        colors = plt.cm.tab10(np.linspace(0, 1, self.n_curves))

        for i, (t, y) in enumerate(self.datasets):
            lbl   = labels[i] if labels else f"curve {i}"
            t_fine = np.linspace(t[0], t[-1], n_points)
            y_fit  = self.predict(t_fine, self.result_["params"][i])
            ax.scatter(t, y, color=colors[i], zorder=5)
            ax.plot(t_fine, y_fit, color=colors[i], lw=2, label=lbl)

        ax.set_xlabel("Time")
        ax.set_ylabel("R")
        ax.set_title("Global/Local Multi-Curve Fitting")
        ax.legend()
        plt.tight_layout()
        plt.savefig("fit_result.png", dpi=150)
        plt.show()


# ── Usage ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # Simulate 3 curves with same kinetics but different Req and t0
    def true_model(t, Req, C1, ka2, kap, t0):
        tau = np.maximum(t - t0, 0.0)
        return np.where(t > t0,
            Req * (1 - C1*np.exp(-ka2*tau) - (1-C1)*np.exp(-kap*tau)), 0.0)

    rng = np.random.default_rng(0)
    t   = np.linspace(0, 10, 40)
    datasets = [
        (t, true_model(t, Req=1.0, C1=0.6, ka2=0.8, kap=0.2, t0=1.0) + rng.normal(0, 0.02, len(t))),
        (t, true_model(t, Req=1.5, C1=0.6, ka2=0.8, kap=0.2, t0=2.0) + rng.normal(0, 0.02, len(t))),
        (t, true_model(t, Req=0.7, C1=0.6, ka2=0.8, kap=0.2, t0=1.5) + rng.normal(0, 0.02, len(t))),
    ]

    fitter = GlobalLocalFitter(
        datasets=datasets,
        global_params=["ka2", "kap", "C1"],   # shared across all curves
        local_params=["Req", "t0"],            # fitted per curve
        fixed={},
    )

    fitter.fit()
    fitter.summary()
    fitter.plot(labels=["A=0.5", "A=1.0", "A=2.0"])