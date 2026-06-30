"""
Physical description of an SPR sensor system.

Units used throughout:
  signal               nm          (plasmon resonance wavelength shift)
  bulk_sensitivity     nm/RIU
  surface_sensitivity  nm/(RIU·nm) (signal per RI change per layer thickness)
  evanescent_length    nm          (derived: S_bulk / S_d)
  dn_dc                cm³/g       (= mL/g; note: 1 cm³/g = 1 nm/(ng/mm²))
  coverage             ng/mm²

De Feijter formula for a thin adsorbed layer:
  signal = S_d * delta_n * d  =  S_d * dn_dc * Gamma
  where delta_n = layer RI contrast [RIU], d = layer thickness [nm], Gamma = surface mass [ng/mm²]

Derived quantities:
  l_d    = S_bulk / S_d       [nm/RIU] / [nm/(RIU·nm)] = [nm]
  Gamma  = signal / (S_d * dn_dc)                         [ng/mm²]
"""

import numpy as np
import matplotlib.pyplot as plt


class SPRSystem:
    """Physical description of an SPR sensor system.

    The surface sensitivity is stored in its instrument-native form nm/(RIU·nm),
    which is independent of the analyte's dn/dc.  Mass sensitivity and
    evanescent length are derived properties.

    Parameters
    ----------
    bulk_sensitivity    : float  Bulk RI sensitivity (nm/RIU).
    surface_sensitivity : float  Surface RI sensitivity (nm/(RIU·nm)).
    noise               : float  Instrument noise, 1σ RMS (nm).
    dn_dc               : float  Refractive index increment of the analyte
                                 (cm³/g, default 0.18 for proteins).
    """

    DEFAULT = {
        'bulk_sensitivity':    200,    # nm/RIU
        'surface_sensitivity': 8,      # nm/(RIU·nm)
        'noise':               2e-2,   # nm
        'dn_dc':               0.18,   # cm³/g, refractive index increment for proteins
        'n_medium':            1.333,  # buffer refractive index (water at 25 °C)
        'n_bsa':               1.47,   # refractive index of adsorbed BSA layer
        'd_bsa':               5.0,    # nm, BSA monolayer thickness
    }

    def __init__(self, bulk_sensitivity=None, surface_sensitivity=None, noise=None,
                 dn_dc=None, dt=1.0, bulk_n_baseline=0.0, bulk_n_sample=0.0,
                 rng_seed=None):
        self.bulk_sensitivity    = float(self.DEFAULT['bulk_sensitivity']    if bulk_sensitivity    is None else bulk_sensitivity)
        self.surface_sensitivity = float(self.DEFAULT['surface_sensitivity'] if surface_sensitivity is None else surface_sensitivity)
        self.noise               = float(self.DEFAULT['noise']               if noise               is None else noise)
        self.dn_dc               = self.DEFAULT['dn_dc'] if dn_dc is None else dn_dc
        self.dt               = float(dt)
        self.bulk_n_baseline  = float(bulk_n_baseline)
        self.bulk_n_sample    = float(bulk_n_sample)
        self.rng_seed         = rng_seed

    @property
    def dn_dc(self):
        """Refractive index increment of the analyte (cm³/g)."""
        return self._dn_dc

    @dn_dc.setter
    def dn_dc(self, value):
        self._dn_dc = float(value)

    def calibrate_bulk_sensitivity(self, signal, n):
        """Calibrate bulk sensitivity from measured signals and refractive indexes.

        Fits a linear model  signal = S_bulk * (n - n[0]) + offset  and sets
        self.bulk_sensitivity to the slope.

        Parameters
        ----------
        signal : array-like  Measured SPR signals (nm).
        n      : array-like  Corresponding refractive index values (RIU).

        Returns
        -------
        bulk_sensitivity : float  Fitted slope (nm/RIU).
        """
        signal = np.asarray(signal, dtype=float)
        n      = np.asarray(n,      dtype=float)
        slope, _ = np.polyfit(n - n[0], signal, 1)
        self.bulk_sensitivity = slope
        return slope

    def calibrate_from_BSA(self, bsa_signal,
                           n_bsa=None, d_bsa=None, n_medium=None):
        """Set surface sensitivity from a BSA monolayer adsorption measurement.

        BSA surface mass density is calculated from its physical properties via
        the de Feijter formula:
            rho_BSA   = (n_BSA - n_medium) / dn_dc   [g/cm³]
            Gamma_BSA = rho_BSA * d_BSA               [ng/mm²]
        using the unit identity  1 g/cm³ · 1 nm = 1 ng/mm².

        Parameters
        ----------
        bsa_signal : float  Measured SPR signal from BSA adsorption (nm).
        n_bsa      : float  Refractive index of adsorbed BSA layer
                            (default DEFAULT['n_bsa'], range 1.45–1.50).
        d_bsa      : float  Thickness of BSA monolayer (nm,
                            default DEFAULT['d_bsa'], range 4–7).
        n_medium   : float  Buffer refractive index
                            (default DEFAULT['n_medium']).
        """
        n_bsa    = self.DEFAULT['n_bsa']    if n_bsa    is None else n_bsa
        d_bsa    = self.DEFAULT['d_bsa']    if d_bsa    is None else d_bsa
        n_medium = self.DEFAULT['n_medium'] if n_medium is None else n_medium
        bsa_coverage             = self._layer_coverage(n_bsa, d_bsa, n_medium)
        surface_sensitivity_mass = bsa_signal / bsa_coverage        # nm/(ng/mm²)
        self.surface_sensitivity = surface_sensitivity_mass / self.dn_dc  # nm/(RIU·nm)

    def _layer_coverage(self, n_layer, d_layer, n_medium=1.333):
        """Surface mass density of a uniform adsorbed layer (ng/mm²).

        Uses the de Feijter formula:
            rho   = (n_layer - n_medium) / dn_dc   [g/cm³]
            Gamma = rho * d_layer                   [ng/mm²]
        Unit identity: 1 g/cm³ · 1 nm = 1 ng/mm²

        Parameters
        ----------
        n_layer  : float  Refractive index of the adsorbed layer.
        d_layer  : float  Layer thickness (nm).
        n_medium : float  Buffer refractive index (default 1.333, water).
        """
        rho = (n_layer - n_medium) / self.dn_dc   # g/cm³
        return rho * d_layer                       # ng/mm²  (1 g/cm³ · nm = 1 ng/mm²)

    # ── Derived quantities ───────────────────────────────────────────────────

    @property
    def evanescent_length(self):
        """Evanescent field 1/e intensity decay length (nm).

        Derived from the de Feijter formula integrating intensity:
            S_bulk = ∫₀^∞ S_d · exp(−z / l_d) dz  =  S_d · l_d
        so  l_d = S_bulk / S_d
        """
        return self.bulk_sensitivity / self.surface_sensitivity

    @property
    def LOD_coverage(self):
        """Limit of detection in surface mass density, 3σ criterion (ng/mm²)."""
        return 3.0 * self.noise / (self.surface_sensitivity * self.dn_dc)

    @property
    def LOD_bulk(self):
        """Limit of detection in bulk refractive index, 3σ criterion (RIU)."""
        return 3.0 * self.noise / self.bulk_sensitivity

    @property
    def LOD_surface(self):
        """Limit of detection in surface RI·thickness product, 3σ criterion (RIU·nm)."""
        return 3.0 * self.noise / self.surface_sensitivity

    # ── Unit conversions ─────────────────────────────────────────────────────

    def signal_to_coverage(self, signal):
        """Convert SPR signal (nm) to surface mass density (ng/mm²)."""
        return np.asarray(signal, dtype=float) / (self.surface_sensitivity * self.dn_dc)

    def coverage_to_signal(self, coverage):
        """Convert surface mass density (ng/mm²) to SPR signal (nm)."""
        return np.asarray(coverage, dtype=float) * (self.surface_sensitivity * self.dn_dc)

    def signal_to_surface_density(self, signal, M_Da):
        """Convert SPR signal to surface number density (molecules/μm²).

        signal [nm]  →  coverage [ng/mm²]  →  molecules/μm²

        Conversion:
            molecules/μm² = coverage [ng/mm²] · NA / (M_Da · 1e15)
            (1 ng/mm² = 1e-15 g/μm²;  M_Da [Da] = M_Da [g/mol])

        Parameters
        ----------
        signal : array-like  SPR signal (nm).
        M_Da   : float        Molecular mass of the analyte (Da).

        Returns
        -------
        surface_density : ndarray  Number of molecules per μm².
        """
        NA = 6.022e23
        coverage = self.signal_to_coverage(signal)   # ng/mm²
        return coverage * NA / (float(M_Da) * 1e15)  # molecules/μm²

    # ── Plotting ─────────────────────────────────────────────────────────────

    def plotSurfaceSensitivity(self):
        """Plot surface sensitivity s(z) = S_d · exp(−z / l_d) from 0 to l_d.

        Returns
        -------
        fig, ax
        """


        l_d = self.evanescent_length
        z   = np.linspace(0, l_d, 300)
        s   = self.surface_sensitivity * np.exp(-z / l_d)

        z_half = l_d * np.log(2)

        fig, ax = plt.subplots()
        ax.plot(z, s)
        ax.axvline(l_d, color='gray', ls='--', linewidth=0.8,
                   label=f'$l_d$ = {l_d:.0f} nm')
        ax.axvline(z_half, color='tab:orange', ls='--', linewidth=0.8,
                   label=f'$z_{{1/2}}$ = {z_half:.0f} nm')
        ax.set_xlabel('Distance from surface (nm)')
        ax.set_ylabel('Surface sensitivity (nm / (RIU·nm))')
        ax.set_title('Evanescent field — surface sensitivity profile')
        ax.legend(fontsize=9)
        fig.tight_layout()
        return fig, ax

    # ── Summary ──────────────────────────────────────────────────────────────

    def summary(self):
        """Print a summary of system parameters and derived quantities."""
        print("=" * 55)
        print("  SPR System")
        print("=" * 55)
        print(f"  Bulk sensitivity        : {self.bulk_sensitivity:.0f} nm/RIU")
        print(f"  Surface sensitivity     : {self.surface_sensitivity:.4f} nm/(RIU·nm)")
        print(f"  Noise (1σ)              : {self.noise:.4e} nm")
        print(f"  dn/dc                   : {self.dn_dc:.3f} cm³/g")
        print(f"  Evanescent length       : {self.evanescent_length:.1f} nm")
        print(f"  LOD coverage (3σ)       : {self.LOD_coverage:.2e} ng/mm²")
        print(f"  LOD bulk     (3σ)       : {self.LOD_bulk:.2e} RIU")
        print(f"  LOD surface  (3σ)       : {self.LOD_surface:.2e} RIU·nm")
        print("=" * 55)


class SPRChamber:
    """Microfluidic chamber geometry and flow-transport properties for an SPR sensor.

    Computes the mass-transfer coefficient km and the diffusion (depletion) layer
    thickness δ using the Lévêque solution for laminar flow in a rectangular channel.

    Geometry
    --------
    The sensor surface is the bottom wall of a rectangular channel:
        height h  (μm) — gap between sensor and top wall
        width  w  (μm) — direction perpendicular to flow
        length L  (μm) — sensor-patch length along the flow direction

    Lévêque solution (valid for Pe = v·h/D >> 1):
        wall shear rate  γ = 6·Q / (w·h²)          [s⁻¹]
        km = 0.538 · (γ · D² / L)^(1/3)             [m/s]
        δ  = D / km                                  [m]

    Parameters
    ----------
    h : float  Channel height (μm).
    w : float  Channel width  (μm).
    L : float  Sensor-patch length along flow (μm).
    Q        : float        Volumetric flow rate (μL/min).
    D        : float | None Analyte diffusion coefficient (m²/s). Supply directly,
                            or omit and provide M_Da + molecule instead.
    M_Da     : float | None Molecular mass (Da) — D computed via Stokes-Einstein.
    molecule : str          Analyte type; selects density and hydration defaults.
                            'protein' : ρ = 1350 kg/m³, hydration = 1.3 (default)
                            'ssdna'   : ρ = 1500 kg/m³, hydration = 1.2
    T        : float        Temperature (K) used when computing D.
                            Default 298.15 K (25 °C).
    """

    NU_WATER = 1e-6   # kinematic viscosity of water at 25 °C (m²/s)

    _MOLECULE_PARAMS = {
        'protein': {'rho': 1350.0, 'hydration': 1.3},
        'ssdna':   {'rho': 1500.0, 'hydration': 1.2},
    }

    def __init__(self, h, w, L, Q, D=None, M_Da=None, molecule='protein', T=298.15):
        self.h = float(h) * 1e-6          # μm → m
        self.w = float(w) * 1e-6
        self.L = float(L) * 1e-6
        self.Q = float(Q) / 60 * 1e-9     # μL/min → m³/s

        self.M_Da = float(M_Da) if M_Da is not None else None

        if D is not None:
            self.D = float(D)
        elif M_Da is not None:
            if molecule not in self._MOLECULE_PARAMS:
                raise ValueError(f"molecule must be one of {list(self._MOLECULE_PARAMS)}")
            params = self._MOLECULE_PARAMS[molecule]
            self.D = self.diffusion_coefficient(M_Da, T=T, **params)
        else:
            raise ValueError("Provide D, or M_Da with molecule='protein'/'ssdna'.")

    # ── Derived transport quantities ─────────────────────────────────────────

    @property
    def flow_velocity(self):
        """Mean flow velocity (m/s)."""
        return self.Q / (self.h * self.w)

    @property
    def wall_shear_rate(self):
        """Wall shear rate for parabolic flow in a rectangular channel (s⁻¹).

        γ = 6·Q / (w·h²)  — exact for h << w (wide-channel limit).
        """
        return 6.0 * self.Q / (self.w * self.h**2)

    @property
    def Re(self):
        """Reynolds number Re = v·h / ν."""
        return self.flow_velocity * self.h / self.NU_WATER

    @property
    def Pe(self):
        """Péclet number Pe = v·h / D."""
        return self.flow_velocity * self.h / self.D

    @property
    def km(self):
        """Mass transfer coefficient (m/s) from the Lévêque solution.

        km = 0.538 · (γ · D² / L)^(1/3)

        Requires Pe >> 1.  The Péclet number is available as self.Pe.
        """
        return 0.538 * (self.wall_shear_rate * self.D**2 / self.L) ** (1.0 / 3.0)

    @property
    def delta(self):
        """Diffusion (depletion) layer thickness δ = D / km  (nm)."""
        return self.D / self.km * 1e9   # m → nm

    # ── Analyte properties ───────────────────────────────────────────────────

    @staticmethod
    def diffusion_coefficient(M_Da, T=298.15, rho=1350.0, hydration=1.3):
        """Estimate diffusion coefficient D for a globular protein (Stokes-Einstein).

        Steps
        -----
        1. Compute bare radius from molecular mass assuming a sphere of density ρ:
               r_bare = (3·M / (4π·NA·ρ))^(1/3)
        2. Apply hydration factor to get hydrodynamic radius:
               rh = hydration · r_bare
        3. Apply Stokes-Einstein:
               D = kB·T / (6π·η(T)·rh)

        Water viscosity η(T) uses the Vogel-Tammann-Fulcher approximation:
               η = 2.414e-5 · 10^(247.8 / (T − 140))  [Pa·s]

        Parameters
        ----------
        M_Da     : float  Molecular mass (Da).
        T        : float  Temperature (K). Default 298.15 K (25 °C).
        rho      : float  Protein density (kg/m³). Default 1350.
        hydration: float  Ratio rh / r_bare accounting for hydration shell.
                          Default 1.3.

        Returns
        -------
        D : float  Diffusion coefficient (m²/s).
        """
        kB = 1.381e-23
        NA = 6.022e23
        eta  = 2.414e-5 * 10 ** (247.8 / (T - 140.0))
        M_kg = M_Da / (NA * 1000)
        r_bare = (3.0 * M_kg / (4.0 * np.pi * rho)) ** (1.0 / 3.0)
        rh = hydration * r_bare
        return kB * T / (6.0 * np.pi * eta * rh)

    def damkohler(self, kon, Rmax):
        """Damköhler number Da = kon · Γmax / km  (dimensionless).

        Compares the surface binding rate to the diffusive transport rate.
        Da >> 1 : transport-limited  (apparent kinetics are distorted)
        Da << 1 : reaction-limited   (kinetics can be measured reliably)

        Derivation
        ----------
        The surface binding flux is  J_rxn = kon · C · Γmax  [mol/(m²·s)]
        The transport flux is        J_tr  = km · C           [mol/(m²·s)]
        Their ratio (independent of C):

            Da = kon [m³/(mol·s)] · Γmax [mol/m²] / km [m/s]

        Unit conversions applied internally:
            kon  [M⁻¹s⁻¹]  →  kon · 1e-3  [m³/(mol·s)]
            Rmax [ng/mm²]  →  Rmax · 1e-3 / self.M_Da  [mol/m²]

        Parameters
        ----------
        kon  : float  Association rate constant (M⁻¹ s⁻¹).
        Rmax : float  Maximum surface binding capacity (ng/mm²).

        Returns
        -------
        Da : float  Damköhler number (dimensionless).
        """
        kon_si    = kon  * 1e-3                    # M⁻¹s⁻¹  → m³/(mol·s)
        Gamma_max = Rmax * 1e-3 / float(self.M_Da) # ng/mm²   → mol/m²
        return kon_si * Gamma_max / self.km

    # ── Summary ─────────────────────────────────────────────────────────────

    def summary(self):
        """Print a summary of chamber geometry and transport quantities."""
        print("=" * 55)
        print("  SPR Chamber")
        print("=" * 55)
        print(f"  Channel height       : {self.h*1e6:.1f} μm")
        print(f"  Channel width        : {self.w*1e6:.1f} μm")
        print(f"  Sensor-patch length  : {self.L*1e6:.1f} μm")
        print(f"  Flow rate            : {self.Q*60*1e9:.1f} μL/min")
        print(f"  Diffusion coeff.     : {self.D:.2e} m²/s")
        print(f"  Mean flow velocity   : {self.flow_velocity*1e3:.2f} mm/s")
        print(f"  Wall shear rate      : {self.wall_shear_rate:.0f} s⁻¹")
        print(f"  Reynolds number      : {self.Re:.4f}  (laminar < 2000)")
        print(f"  Péclet number        : {self.Pe:.0f}  (Lévêque valid >> 1)")
        print(f"  km  (Lévêque)        : {self.km*1e6:.2f} μm/s")
        print(f"  δ   (depletion layer): {self.delta:.1f} nm")
        print("=" * 55)


# ── Usage example ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    system = SPRSystem(
            dt               = 3.0,      # 3 s sampling interval
            noise            = 0.02,     # 20 pm Gaussian noise
            bulk_sensitivity = 200.0,    # 200 nm/RIU
        )
    system.calibrate_from_BSA(bsa_signal=6)

    system.summary()
    system.plotSurfaceSensitivity()
    plt.show()

    # ── SPRChamber — ssDNA (24-mer, M = 7200 Da) ─────────────────────────────
    chamber = SPRChamber(h=400, w=4000, L=7000, Q=30,
                               M_Da=7200, molecule='ssdna')
    chamber.summary()

    # ── Damköhler number ─────────────────────────────────────────────────────
    # Units:  kon [M⁻¹s⁻¹] * 1e-3 → [m³/(mol·s)]
    #         Rmax [ng/mm²] * 1e-3 / M_Da → [mol/m²]
    #         Da = [m³/(mol·s)] * [mol/m²] / [m/s] = dimensionless  ✓
    kon  = 1e4   # M⁻¹s⁻¹  
    Rmax = system.signal_to_coverage(0.3)   # convert 1.1 nm SPR signal → ng/mm²
    Da   = chamber.damkohler(kon=kon, Rmax=Rmax)
    regime = ("reaction-limited" if Da < 0.1
              else "transport-limited" if Da > 10
              else "mixed regime")
    print(f"\nDamköhler number (ssDNA, kon={kon:.0e} /M/s, Rmax={Rmax:.3f} ng/mm²):")
    print(f"  Da = {Da:.4f}  →  {regime}")
