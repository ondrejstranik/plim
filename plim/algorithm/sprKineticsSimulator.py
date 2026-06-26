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

try:
    from plim.algorithm.sprSystem import SPRSystem
except ImportError:
    from sprSystem import SPRSystem


class SPRKineticsSimulator:
    """Simulate SPR sensor adsorption/desorption kinetics.

    Parameters
    ----------
    kon    : float      Association rate constant  (M⁻¹ s⁻¹)
    koff   : float      Dissociation rate constant (s⁻¹)
    Rmax   : float      Maximum SPR response       (nm)
    ka2    : float      Forward conformational rate (s⁻¹)  [two_state only]
    kd2    : float      Reverse conformational rate (s⁻¹)  [two_state only]
    km     : float      Mass transfer coefficient  (nm M⁻¹ s⁻¹)  [transport only];
                        same dimension as kon*Rmax — transport-limited when km << kon*Rmax
    model  : str        'langmuir', 'two_state', or 'transport'
    system : SPRSystem  Instrument parameters (dt, noise, bulk).
    """

    MODELS = ('langmuir', 'two_state', 'transport')

    def __init__(self, kon=1e4, koff=1e-3, Rmax=1.0,
                 ka2=0.0, kd2=0.0, km=1e3, model='langmuir',
                 system=None):
        if model not in self.MODELS:
            raise ValueError(f"model must be one of {self.MODELS}")
        self.kon    = float(kon)
        self.koff   = float(koff)
        self.Rmax   = float(Rmax)
        self.ka2    = float(ka2)
        self.kd2    = float(kd2)
        self.km     = float(km)
        self.model  = model
        self.system = system if system is not None else SPRSystem()

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
        t    = np.arange(0.0, duration + self.system.dt * 0.5, self.system.dt)
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

        t_eval = np.arange(0.0, duration + self.system.dt * 0.5, self.system.dt)
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

        t_eval = np.arange(0.0, duration + self.system.dt * 0.5, self.system.dt)
        sol = solve_ivp(odes, [0.0, duration], R0, t_eval=t_eval,
                        method='RK45', rtol=1e-8, atol=1e-10, dense_output=False)
        R1, R2 = sol.y
        signal = R1 + R2
        R_end  = np.array([R1[-1], R2[-1]])
        return sol.t + t_offset, signal, R_end

    # ── Plotting ─────────────────────────────────────────────────────────────

    def plotKinetics(self, concentrations, durations):
        """Plot simulated kinetic curves for each concentration.

        Uses self.system for noise and bulk sensitivity.

        Parameters
        ----------
        concentrations : array-like  Analyte concentrations (M).
        durations      : list        [t_baseline, t_assoc, t_dissoc] in seconds.

        Returns
        -------
        fig, ax
        """
        import matplotlib.pyplot as plt
        concentrations = np.asarray(concentrations, dtype=float).ravel()
        durations      = list(durations)
        colors         = plt.rcParams['axes.prop_cycle'].by_key()['color']
        bulk_n         = [self.system.bulk_n_baseline,
                          self.system.bulk_n_sample,
                          self.system.bulk_n_baseline]

        fig, ax = plt.subplots()
        for i, C in enumerate(concentrations):
            t, s = self.simulate(durations, [0, C, 0], bulk_n,
                                 bulk_sensitivity=self.system.bulk_sensitivity,
                                 noise_std=self.system.noise,
                                 rng_seed=self.system.rng_seed)
            ax.plot(t, s, color=colors[i % len(colors)],
                    label=f'{C*1e9:.2g} nM')

        ax.axvline(durations[0],                color='gray', ls=':', linewidth=0.8)
        ax.axvline(durations[0] + durations[1], color='gray', ls=':', linewidth=0.8)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal (nm)')
        ax.set_title(f'1:1 Langmuir  |  Kd = {self.Kd*1e9:.0f} nM'
                     f'  kon = {self.kon:.0e} /M/s  koff = {self.koff:.0e} /s')
        ax.legend(title='Concentration', fontsize=8)
        fig.tight_layout()
        return fig, ax

    def plotTau(self, concentrations):
        """Plot observed time constant τ = 1/(kon·C + koff) vs concentration.

        Parameters
        ----------
        concentrations : array-like  Analyte concentrations (M).

        Returns
        -------
        fig, ax
        """
        import matplotlib.pyplot as plt
        concentrations = np.asarray(concentrations, dtype=float).ravel()
        colors         = plt.rcParams['axes.prop_cycle'].by_key()['color']

        kobs = self.kon * concentrations + self.koff
        tau  = 1.0 / kobs

        req  = self.Rmax * concentrations / (self.Kd_apparent + concentrations)
        dtau = tau * self.system.noise / req

        fig, ax = plt.subplots()
        for i, (C, t, dt) in enumerate(zip(concentrations, tau, dtau)):
            ax.errorbar(C * 1e9, t, yerr=dt,
                        fmt='o', color=colors[i % len(colors)],
                        capsize=4, label=f'{C*1e9:.2g} nM')

        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Concentration (nM)')
        ax.set_ylabel('τ (s)')
        ax.set_title(f'Observed time constant  |  kon = {self.kon:.1e} /M/s'
                     f'  koff = {self.koff:.1e} /s')
        ax.legend(title='Concentration', fontsize=8)
        fig.tight_layout()
        return fig, ax

    def plotIsotherm(self, concentrations=None):
        """Plot the Langmuir isotherm, optionally marking specific concentrations.

        Parameters
        ----------
        concentrations : array-like | None  Concentrations to mark (M).

        Returns
        -------
        fig, ax
        """
        import matplotlib.pyplot as plt
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        c_iso = np.logspace(np.log10(self.Kd / 100), np.log10(self.Kd * 1000), 300)
        _, Req_iso = self.simulate_isotherm(c_iso)

        fig, ax = plt.subplots()
        ax.semilogx(c_iso * 1e9, Req_iso, 'b-', zorder=1)

        if concentrations is not None:
            concentrations = np.asarray(concentrations, dtype=float).ravel()
            for i, C in enumerate(concentrations):
                ax.errorbar(C * 1e9, self.Req(C), yerr=self.system.noise,
                            fmt='o', color=colors[i % len(colors)],
                            capsize=4, zorder=5, label=f'{C*1e9:.2g} nM')

        ax.axvline(self.Kd * 1e9, color='gray', ls='--', linewidth=0.8,
                   label=f'Kd = {self.Kd*1e9:.1f} nM')
        ax.axhline(self.Rmax / 2, color='gray', ls=':', linewidth=0.8)
        ax.axhline(self.Rmax,     color='gray', ls=':', linewidth=0.8,
                   label=f'Rmax = {self.Rmax} nm')
        ax.set_xlabel('Concentration (nM)')
        ax.set_ylabel('R_eq (nm)')
        ax.set_title('Langmuir isotherm')
        ax.legend(title='Concentration', fontsize=8)
        fig.tight_layout()
        return fig, ax


# ── Usage example ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    msSystem = SPRSystem(
            dt               = 3.0,      # 1 s sampling interval
            noise            = 0.02,     # 10 pm Gaussian noise
            bulk_sensitivity = 200.0,    # 200 nm/RIU
        )
    msSystem.calibrate_from_BSA(bsa_signal=6)


    sim = SPRKineticsSimulator(
        kon=1e4, koff=1e-4, Rmax=0.3, model='langmuir',
        system=msSystem)


    print(f"Kd = {sim.Kd*1e9:.1f} nM  |  tau_dissoc = {1/sim.koff:.0f} s")

    concentrations = np.logspace(np.log10(sim.Kd / 10), np.log10(sim.Kd * 100), 7)
    durations      = [60, 900, 900]   # 60 s baseline + 15 min assoc + 15 min dissoc

    sim.plotKinetics(concentrations, durations)
    sim.plotIsotherm(concentrations)
    sim.plotTau(concentrations)
    plt.show()
