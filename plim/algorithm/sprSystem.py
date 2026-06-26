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


# ── Usage example ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    system = SPRSystem()
    system.calibrate_from_BSA(
        bsa_signal=6
    )
    system.summary()
    system.plotSurfaceSensitivity()
    plt.show()

    # ── Conversions ──────────────────────────────────────────────────────────
    signal_nm = 0.3
    print(f"\n{signal_nm} nm  ->  {system.signal_to_coverage(signal_nm):.3f} ng/mm²")
