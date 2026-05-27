"""
SPR adsorption/desorption kinetics simulator.

Supported models
----------------
langmuir   : 1:1 Langmuir binding        A + B <-> AB
two_state  : conformational change        A + B <-> AB <-> AB*
transport  : two-film mass transport      Langmuir + diffusion layer, parameter km (nm M⁻¹ s⁻¹)

Output units match the rest of the plim codebase: time in seconds, signal in nm.
"""

import numpy as np
from scipy.integrate import solve_ivp


class SPRKineticsSimulator:
    """Simulate SPR sensor adsorption/desorption kinetics.

    Parameters
    ----------
    ka    : float  Association rate constant  (M⁻¹ s⁻¹)
    kd    : float  Dissociation rate constant (s⁻¹)
    Rmax  : float  Maximum SPR response       (nm)
    ka2   : float  Forward conformational rate (s⁻¹)  [two_state only]
    kd2   : float  Reverse conformational rate (s⁻¹)  [two_state only]
    km    : float  Mass transfer coefficient  (nm M⁻¹ s⁻¹)  [transport only];
                   same dimension as ka*Rmax — transport-limited when km << ka*Rmax
    model : str    'langmuir', 'two_state', or 'transport'
    dt    : float  Time resolution             (s)
    """

    MODELS = ('langmuir', 'two_state', 'transport')

    def __init__(self, ka=1e4, kd=1e-3, Rmax=1.0,
                 ka2=0.0, kd2=0.0, km=1e3, model='langmuir', dt=1.0):
        if model not in self.MODELS:
            raise ValueError(f"model must be one of {self.MODELS}")
        self.ka    = float(ka)
        self.kd    = float(kd)
        self.Rmax  = float(Rmax)
        self.ka2   = float(ka2)
        self.kd2   = float(kd2)
        self.km    = float(km)
        self.model = model
        self.dt    = float(dt)

    # ── Public properties ────────────────────────────────────────────────────

    @property
    def KD(self):
        """Equilibrium dissociation constant (M)."""
        return self.kd / self.ka

    def Req(self, concentration):
        """Steady-state response at the given analyte concentration (nm)."""
        C = float(concentration)
        return self.Rmax * C / (self.KD + C)

    # ── Main simulation entry point ──────────────────────────────────────────

    def simulate(self, durations, concentrations, bulk_n,
                 bulk_sensitivity=0.0, noise_std=0.0, rng_seed=None):
        """Simulate an SPR experiment defined as a sequence of sections.

        Each section has a duration, an analyte concentration (drives surface
        kinetics) and a bulk refractive index (adds a step offset when
        bulk_sensitivity is non-zero).  The surface state carries over between
        sections.

        Parameters
        ----------
        durations        : array-like  Duration of each section (s).
        concentrations   : array-like  Analyte concentration in each section (M);
                           set to 0 for buffer/dissociation sections.
        bulk_n           : array-like  Bulk refractive index in each section (RIU).
        bulk_sensitivity : float       Bulk RI sensitivity (nm/RIU); 0 disables
                           the bulk contribution.
        noise_std        : float       Std-dev of Gaussian noise (nm).
        rng_seed         : int | None  Random seed for reproducibility.

        Returns
        -------
        time   : ndarray (N,)  Absolute time axis (s).
        signal : ndarray (N,)  SPR response (nm), surface + bulk contributions.
        """
        durations      = np.asarray(durations,      dtype=float).ravel()
        concentrations = np.asarray(concentrations, dtype=float).ravel()
        bulk_n         = np.asarray(bulk_n,         dtype=float).ravel()

        if not (len(durations) == len(concentrations) == len(bulk_n)):
            raise ValueError("durations, concentrations and bulk_n must have the same length.")

        rng   = np.random.default_rng(rng_seed)
        n_ref = bulk_n[0]

        time_segments   = []
        signal_segments = []
        t_offset = 0.0
        R0 = np.zeros(2) if self.model == 'two_state' else np.zeros(1)

        for dur, C, n in zip(durations, concentrations, bulk_n):
            if self.model == 'langmuir':
                t_sec, s_surf, R0_val = self._langmuir_phase(C, dur, R0[0], t_offset)
                R0 = np.array([R0_val])
            elif self.model == 'transport':
                t_sec, s_surf, R0_val = self._transport_phase(C, dur, R0[0], t_offset)
                R0 = np.array([R0_val])
            else:
                t_sec, s_surf, R0 = self._two_state_phase(C, dur, R0, t_offset)

            s_bulk = bulk_sensitivity * (n - n_ref)
            time_segments.append(t_sec)
            signal_segments.append(s_surf + s_bulk)
            t_offset += dur

        time   = np.concatenate(time_segments)
        signal = np.concatenate(signal_segments)

        if noise_std > 0:
            signal += rng.normal(0.0, noise_std, size=signal.shape)

        return time, signal

    # ── Langmuir 1:1 model ───────────────────────────────────────────────────

    def _langmuir_phase(self, C, duration, R0, t_offset):
        """Analytical Langmuir phase solution."""
        t = np.arange(0.0, duration + self.dt * 0.5, self.dt)
        kobs = self.ka * C + self.kd
        if kobs < 1e-30:
            signal = np.full_like(t, R0)
        else:
            Req = self.Rmax * self.ka * C / kobs   # = 0 when C = 0
            signal = Req + (R0 - Req) * np.exp(-kobs * t)

        R_end = float(signal[-1])
        return t + t_offset, signal, R_end

    # ── Two-film transport-limited model ────────────────────────────────────

    def _transport_phase(self, C, duration, R0, t_offset):
        """Numerical integration for the two-film transport-limited model.

        Surface ODE (quasi-steady-state transport layer):
            dR/dt = km * [ka * (Rmax - R) * C - kd * R] / (km + ka * (Rmax - R))

        Limits:
            km >> ka*(Rmax-R)  ->  pure Langmuir
            km << ka*(Rmax-R)  ->  dR/dt = km * C  (transport-limited, tau independent of C)
        """
        def odes(t, y):
            R     = y[0]
            Rfree = self.Rmax - R
            denom = self.km + self.ka * Rfree
            dR    = self.km * (self.ka * Rfree * C - self.kd * R) / denom
            return [dR]

        t_eval = np.arange(0.0, duration + self.dt * 0.5, self.dt)
        sol    = solve_ivp(odes, [0.0, duration], [R0], t_eval=t_eval,
                           method='RK45', rtol=1e-8, atol=1e-10)
        signal = sol.y[0]
        return sol.t + t_offset, signal, float(signal[-1])

    # ── Two-state conformational change model ────────────────────────────────

    def _two_state_phase(self, C, duration, R0, t_offset):
        """Numerical integration for the two-state model."""
        def odes(t, y):
            R1, R2 = y
            Rfree = self.Rmax - R1 - R2
            dR1 = self.ka * C * Rfree - self.kd * R1 - self.ka2 * R1 + self.kd2 * R2
            dR2 = self.ka2 * R1 - self.kd2 * R2
            return [dR1, dR2]

        t_eval = np.arange(0.0, duration + self.dt * 0.5, self.dt)
        sol = solve_ivp(odes, [0.0, duration], R0, t_eval=t_eval,
                        method='RK45', rtol=1e-8, atol=1e-10, dense_output=False)
        R1, R2 = sol.y
        signal = R1 + R2
        R_end = np.array([R1[-1], R2[-1]])
        return sol.t + t_offset, signal, R_end

# ── Usage example ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # 40 bp ssDNA — strongly transport-limited model demonstrating that
    # 1 mM and 2 mM look indistinguishable (both saturate in ~3 s of a 300 s window)
    # ka = 2e5 M⁻¹s⁻¹, kd = 1e-4 s⁻¹  →  KD = 0.5 nM
    # km = 1e3 nm M⁻¹ s⁻¹  (km / (ka*Rmax) ≈ 0.002 → strongly transport-limited)
    sim = SPRKineticsSimulator(
        ka=2e5, kd=1e-4, Rmax=3,
        km=1e3, model='transport', dt=1.0,
    )
    print(f"KD              = {sim.KD * 1e9:.1f} nM")
    print(f"tau_dissoc      = {1/sim.kd:.0f} s")
    print(f"km/(ka*Rmax)    = {sim.km/(sim.ka*sim.Rmax):.4f}  (<<1 → strongly transport-limited)")

    noise          = 0.02
    n0             = 1.333
    durations      = [300, 300, 300]
    bulk_n         = [n0, n0, n0]
    concentrations = [1e-5, 1e-4, 5e-4, 1e-3, 2e-3, 5e-3]   # 10 µM → 5 mM

    def _clabel(C):
        return f'{C*1e6:.0f} µM' if C < 1e-3 else f'{C*1e3:.0f} mM'

    # tau_assoc approximation: tau ≈ 1/(ka*C) + Rmax/(km*C)
    print(f"\n{'C':>10}  {'tau_assoc (s)':>14}  {'tau_dissoc (s)':>14}")
    fig, ax = plt.subplots()
    for C in concentrations:
        tau_assoc = 1.0 / (sim.ka * C) + sim.Rmax / (sim.km * C)
        print(f"{_clabel(C):>10}  {tau_assoc:>14.1f}  {1/sim.kd:>14.1f}")
        t, s = sim.simulate(durations, [0, C, 0], bulk_n, noise_std=noise)
        ax.plot(t, s, label=_clabel(C))

    ax.axvline(300, color='gray', linestyle='--', linewidth=0.8)
    ax.axvline(600, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Signal (nm)')
    ax.set_title(f'40 bp ssDNA — transport-limited  (km = {sim.km:.0e} nm·M⁻¹·s⁻¹,  KD = {sim.KD*1e9:.0f} nM)')
    ax.legend(title='Concentration')
    fig.tight_layout()
    plt.show()
