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
    kon   : float  Association rate constant  (M⁻¹ s⁻¹)
    koff  : float  Dissociation rate constant (s⁻¹)
    Rmax  : float  Maximum SPR response       (nm)
    ka2   : float  Forward conformational rate (s⁻¹)  [two_state only]
    kd2   : float  Reverse conformational rate (s⁻¹)  [two_state only]
    km    : float  Mass transfer coefficient  (nm M⁻¹ s⁻¹)  [transport only];
                   same dimension as kon*Rmax — transport-limited when km << kon*Rmax
    model : str    'langmuir', 'two_state', or 'transport'
    dt    : float  Time resolution             (s)
    """

    MODELS = ('langmuir', 'two_state', 'transport')

    def __init__(self, kon=1e4, koff=1e-3, Rmax=1.0,
                 ka2=0.0, kd2=0.0, km=1e3, model='langmuir', dt=1.0):
        if model not in self.MODELS:
            raise ValueError(f"model must be one of {self.MODELS}")
        self.kon   = float(kon)
        self.koff  = float(koff)
        self.Rmax  = float(Rmax)
        self.ka2   = float(ka2)
        self.kd2   = float(kd2)
        self.km    = float(km)
        self.model = model
        self.dt    = float(dt)

    # ── Public properties ────────────────────────────────────────────────────

    @property
    def Kd(self):
        """Equilibrium dissociation constant (M)."""
        return self.koff / self.kon

    @property
    def Kd_apparent(self):
        """Apparent Kd including the two-state correction (M).

        For langmuir/transport: same as Kd.
        For two_state: Kd_app = Kd * kd2 / (kd2 + ka2)  (tighter than Kd).
        """
        if self.model == 'two_state' and (self.ka2 + self.kd2) > 0:
            return self.Kd * self.kd2 / (self.kd2 + self.ka2)
        return self.Kd

    def Req(self, concentration):
        """Steady-state response at the given analyte concentration (nm)."""
        C = float(concentration)
        return self.Rmax * C / (self.Kd_apparent + C)

    def simulate_isotherm(self, concentrations):
        """Compute the Langmuir isotherm (equilibrium binding curve).

        Returns the steady-state SPR response R_eq for each analyte
        concentration, using the model-appropriate apparent Kd.

        Parameters
        ----------
        concentrations : array-like  Analyte concentrations (M).

        Returns
        -------
        c    : ndarray (N,)  Concentrations (M).
        Req  : ndarray (N,)  Equilibrium response (nm).
        """
        c   = np.asarray(concentrations, dtype=float).ravel()
        Req = self.Rmax * c / (self.Kd_apparent + c)
        return c, Req

    # ── Main simulation entry point ──────────────────────────────────────────

    def simulate(self, durations, concentrations, bulk_n,
                 bulk_sensitivity=0.0, noise_std=0.0, rng_seed=None,
                 t_sample=None):
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

        if t_sample is not None:
            n = max(1, round(t_sample / self.dt))
            trim = (len(time) // n) * n
            time   = time[:trim].reshape(-1, n).mean(axis=1)
            signal = signal[:trim].reshape(-1, n).mean(axis=1)

        if noise_std > 0:
            signal += rng.normal(0.0, noise_std, size=signal.shape)

        return time, signal

    # ── Langmuir 1:1 model ───────────────────────────────────────────────────

    def _langmuir_phase(self, C, duration, R0, t_offset):
        """Analytical Langmuir phase solution."""
        t    = np.arange(0.0, duration + self.dt * 0.5, self.dt)
        kobs = self.kon * C + self.koff
        if kobs < 1e-30:
            signal = np.full_like(t, R0)
        else:
            Req    = self.Rmax * self.kon * C / kobs   # = 0 when C = 0
            signal = Req + (R0 - Req) * np.exp(-kobs * t)

        R_end = float(signal[-1])
        return t + t_offset, signal, R_end

    # ── Two-film transport-limited model ────────────────────────────────────

    def _transport_phase(self, C, duration, R0, t_offset):
        """Numerical integration for the two-film transport-limited model.

        Surface ODE (quasi-steady-state transport layer):
            dR/dt = km * [kon * (Rmax - R) * C - koff * R] / (km + kon * (Rmax - R))

        Limits:
            km >> kon*(Rmax-R)  ->  pure Langmuir
            km << kon*(Rmax-R)  ->  dR/dt = km * C  (transport-limited, tau independent of C)
        """
        def odes(t, y):
            R     = y[0]
            Rfree = self.Rmax - R
            denom = self.km + self.kon * Rfree
            dR    = self.km * (self.kon * Rfree * C - self.koff * R) / denom
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
            dR1 = self.kon * C * Rfree - self.koff * R1 - self.ka2 * R1 + self.kd2 * R2
            dR2 = self.ka2 * R1 - self.kd2 * R2
            return [dR1, dR2]

        t_eval = np.arange(0.0, duration + self.dt * 0.5, self.dt)
        sol = solve_ivp(odes, [0.0, duration], R0, t_eval=t_eval,
                        method='RK45', rtol=1e-8, atol=1e-10, dense_output=False)
        R1, R2 = sol.y
        signal = R1 + R2
        R_end  = np.array([R1[-1], R2[-1]])
        return sol.t + t_offset, signal, R_end

# ── Usage example ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    KON, KOFF, RMAX = 1e4, 1e-4, 1.0   # kon (M⁻¹s⁻¹), koff (s⁻¹), Rmax (nm)  →  Kd = 10 nM
    sim = SPRKineticsSimulator(kon=KON, koff=KOFF, Rmax=RMAX, model='langmuir', dt=1.0)

    print(f"Kd          = {sim.Kd*1e9:.1f} nM")
    print(f"tau_dissoc  = {1/KOFF:.0f} s")

    # 7 concentrations log-spaced from Kd/10 to Kd*100 (reaches saturation)
    concentrations = np.logspace(np.log10(sim.Kd / 10), np.log10(sim.Kd * 100), 7)

    # 60 s baseline + 15 min assoc + 15 min dissoc
    durations = [60, 900, 900]

    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    def _clabel(C):
        return f'{C*1e9:.2g} nM'

    # kinetics — one curve per concentration
    Req_pts = []
    fig_k, ax_k = plt.subplots()
    for i, C in enumerate(concentrations):
        color = colors[i % len(colors)]
        t, s  = sim.simulate(durations, [0, C, 0], [0, 0, 0])
        ax_k.plot(t, s, color=color, label=_clabel(C))
        Req_pts.append(sim.Req(C))

    ax_k.axvline(durations[0],                color='gray', ls=':', linewidth=0.8)
    ax_k.axvline(durations[0] + durations[1], color='gray', ls=':', linewidth=0.8)
    ax_k.set_xlabel('Time (s)')
    ax_k.set_ylabel('Signal (nm)')
    ax_k.set_title(f'1:1 Langmuir  |  Kd = {sim.Kd*1e9:.0f} nM'
                   f'  kon = {KON:.0e} /M/s  koff = {KOFF:.0e} /s')
    ax_k.legend(title='Concentration', fontsize=8)
    fig_k.tight_layout()

    # isotherm — continuous curve + simulated concentrations coloured to match
    c_iso = np.logspace(np.log10(sim.Kd / 100), np.log10(sim.Kd * 1000), 300)
    _, Req_iso = sim.simulate_isotherm(c_iso)

    fig_i, ax_i = plt.subplots()
    ax_i.semilogx(c_iso * 1e9, Req_iso, 'b-', zorder=1)
    for i, (C, Req) in enumerate(zip(concentrations, Req_pts)):
        ax_i.plot(C * 1e9, Req, 'o', color=colors[i % len(colors)],
                  zorder=5, label=_clabel(C))
    ax_i.axvline(sim.Kd * 1e9, color='gray', ls='--', linewidth=0.8,
                 label=f'Kd = {sim.Kd*1e9:.1f} nM')
    ax_i.axhline(sim.Rmax / 2, color='gray', ls=':', linewidth=0.8)
    ax_i.axhline(sim.Rmax,     color='gray', ls=':', linewidth=0.8,
                 label=f'Rmax = {sim.Rmax} nm')
    ax_i.set_xlabel('Concentration (nM)')
    ax_i.set_ylabel('R_eq (nm)')
    ax_i.set_title('Langmuir isotherm')
    ax_i.legend(title='Concentration', fontsize=8)
    fig_i.tight_layout()

    plt.show()
