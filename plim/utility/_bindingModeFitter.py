#%%
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# ── Experimental data ────────────────────────────────────────────────────────
t_exp = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
y_exp = np.array([0, 0.0, 0.0, 0.4, 0.55, 0.65, 0.72, 0.77, 0.80, 0.82, 0.83])

t_exp = time 
y_exp = signalGrid[:,3,0]


A = 1.0   # concentration of analyte A (known)

# ── Fixed / free / derived parameter configuration ───────────────────────────
# None      → free (fitted)
# float     → fixed at that value
# "derived" → computed in compute_derived()
FIXED = {
    "kon":   None,
    "kd1":   None,
    "ka2":   None,
    "kd2":   0,
    "Rmax":  None,
    "R1_0":  0.0,    # initial R1 (typically 0)
    "R2_0":  0.0,    # initial R2 (typically 0)
    "t0":    225.110340,
}

BOUNDS = {
    "kon":   (1e-6, 1e6),
    "kd1":   (1e-6, 1e2),
    "ka2":   (1e-6, 1e2),
    "kd2":   (1e-6, 1e2),
    "Rmax":  (1e-3, 1e4),
    "R1_0":  (0.0,  1e3),
    "R2_0":  (0.0,  1e3),
    "t0":    (t_exp[0], t_exp[-1]),
}

GUESS = {
    "kon":   0.21,
    "kd1":   0.1,
    "ka2":   0.404847,
    "kd2":   0.005,
    "Rmax":  1.0,
    "R1_0":  0.0,
    "R2_0":  0.0,
    "t0":    220.0,
}

ALL_PARAMS = ["kon", "kd1", "ka2", "kd2", "Rmax", "R1_0", "R2_0", "t0"]

def compute_derived(d):
    # no derived parameters currently — add here if needed
    return d

free_params    = [p for p in ALL_PARAMS if FIXED[p] is None]
fixed_params   = {p: v for p, v in FIXED.items() if isinstance(v, (float, int))}
derived_params = [p for p in ALL_PARAMS if FIXED[p] == "derived"]

print("Free:   ", free_params)
print("Fixed:  ", fixed_params)
print("Derived:", derived_params)

def pack(param_dict):
    return [param_dict[p] for p in free_params]

def unpack(vec):
    d = dict(zip(free_params, vec))
    d.update(fixed_params)
    d = compute_derived(d)
    return d

# ── ODE system ───────────────────────────────────────────────────────────────
# A + B  ⇌  AB  ⇌  AB*
# R1 = [AB],  R2 = [AB*]
# dR1/dt = kon·A·(Rmax − R1 − R2) − kd1·R1 − ka2·R1 + kd2·R2
# dR2/dt = ka2·R1 − kd2·R2
# Signal = R1 + R2
def ode(t, y, kon, kd1, ka2, kd2, Rmax, A):
    R1, R2 = y
    dR1 = kon * A * (Rmax - R1 - R2) - kd1 * R1 - ka2 * R1 + kd2 * R2
    dR2 = ka2 * R1 - kd2 * R2
    return [dR1, dR2]

# ── Simulate: constant before t0, ODE after t0 ───────────────────────────────
def simulate(t, p):
    kon, kd1, ka2, kd2, Rmax, R1_0, R2_0, t0 = (
        p["kon"], p["kd1"], p["ka2"], p["kd2"],
        p["Rmax"], p["R1_0"], p["R2_0"], p["t0"]
    )
    mask_after = t > t0
    # signal is constant at R1_0 + R2_0 before t0
    signal_out = np.full_like(t, R1_0 + R2_0)

    t_after = t[mask_after]
    if len(t_after) == 0:
        return signal_out

    sol = solve_ivp(
        lambda t, y: ode(t, y, kon, kd1, ka2, kd2, Rmax, A),
        t_span=(t0, t_after[-1]),
        y0=[R1_0, R2_0],
        t_eval=t_after,
        method="RK45",
        rtol=1e-8, atol=1e-10,
    )
    if not sol.success:
        return np.full_like(t, 1e10)

    signal_out[mask_after] = sol.y[0] + sol.y[1]   # R1 + R2
    return signal_out

# ── Cost function ─────────────────────────────────────────────────────────────
def cost(vec):
    p = unpack(vec)
    try:
        y_sim = simulate(t_exp, p)
        return np.sum((y_sim - y_exp) ** 2)
    except Exception:
        return 1e10

# ── Multi-start optimization ──────────────────────────────────────────────────
bounds_free = [BOUNDS[p] for p in free_params]

rng = np.random.default_rng(42)
base_guess = pack(GUESS)
guesses = [base_guess] + [
    [np.clip(v * rng.uniform(0.5, 2.0), lo, hi) for v, (lo, hi) in zip(base_guess, bounds_free)]
    for _ in range(1)
]

best_result = None
best_cost   = np.inf

for ii,g in enumerate(guesses):
    print(f'{ii} iteration')
    res = minimize(
        cost,
        x0=g,
        method="L-BFGS-B",
        bounds=bounds_free,
        options={"ftol": 1e-12, "gtol": 1e-10, "maxiter": 50_000},
    )
    if res.fun < best_cost:
        best_cost   = res.fun
        best_result = res

best_p = unpack(best_result.x)

print("=" * 45)
for name in ALL_PARAMS:
    tag = "(fixed)" if name in fixed_params else "(derived)" if name in derived_params else ""
    print(f"  {name:<8} = {best_p[name]:.6f}  {tag}")
print(f"  SSE      = {best_cost:.6e}")
print(f"  RMSE     = {np.sqrt(best_cost / len(t_exp)):.6e}")
print("=" * 45)


# ── Plot ─────────────────────────────────────────────────────────────────────
t_fine  = np.linspace(t_exp[0], t_exp[-1], 500)
#t_fine = t_ex
sig_fit = simulate(t_fine, best_p)

# also plot R1 and R2 individually
def simulate_states(t, p):
    kon, kd1, ka2, kd2, Rmax, R1_0, R2_0, t0 = (
        p["kon"], p["kd1"], p["ka2"], p["kd2"],
        p["Rmax"], p["R1_0"], p["R2_0"], p["t0"]
    )
    mask_after = t > t0
    R1_out = np.full_like(t, R1_0)
    R2_out = np.full_like(t, R2_0)
    t_after = t[mask_after]
    if len(t_after) == 0:
        return R1_out, R2_out
    sol = solve_ivp(
        lambda t, y: ode(t, y, kon, kd1, ka2, kd2, Rmax, A),
        t_span=(t0, t_after[-1]),
        y0=[R1_0, R2_0],
        t_eval=t_after,
        method="RK45", rtol=1e-8, atol=1e-10,
    )
    R1_out[mask_after] = sol.y[0]
    R2_out[mask_after] = sol.y[1]
    return R1_out, R2_out

R1_fit, R2_fit = simulate_states(t_fine, best_p)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Left: signal fit
ax = axes[0]
ax.scatter(t_exp, y_exp, label="Experimental signal", color="steelblue", zorder=5)
ax.plot(t_fine, sig_fit, label="R1 + R2 (fit)", color="tomato", lw=2)
ax.axvline(best_p["t0"], color="gray", linestyle="--", label=f"t0 = {best_p['t0']:.2f}")
ax.set_xlabel("Time"); ax.set_ylabel("Signal")
ax.set_title("Signal fit"); ax.legend()

# Right: individual states
ax = axes[1]
ax.plot(t_fine, R1_fit, label="R1 (AB)",  color="darkorange", lw=2)
ax.plot(t_fine, R2_fit, label="R2 (AB*)", color="purple",     lw=2)
ax.plot(t_fine, sig_fit, label="R1+R2",   color="tomato", lw=2, linestyle="--")
ax.axvline(best_p["t0"], color="gray", linestyle="--")
ax.set_xlabel("Time"); ax.set_ylabel("Response")
ax.set_title("Individual states"); ax.legend()

plt.tight_layout()
plt.savefig("fit_result.png", dpi=150)
plt.show()


# %%
