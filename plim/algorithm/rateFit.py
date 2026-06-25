''' class to load kinetic fit results and extract kon, koff, KD '''

import numpy as np
from plim.algorithm.kineticFit import KineticFit
from lmfit import Model
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def _langmuir(c, Rmax, KD):
    return Rmax * c / (KD + c)


class RateFit:
    '''Load a series of KineticFit files, extract kinetic and equilibrium parameters.

    Parameters
    ----------
    folder    : str   Path to folder containing .pkl files.
    files     : list  List of (filename, concentration_nM) tuples.
    timeStart : float Time alignment offset for signal plots (default 0).
    '''

    def __init__(self):
        self.folder    = None
        self.files     = None
        self.timeStart = 0.0

        self.c      = None
        self.tau    = None
        self.tau_q1 = None
        self.tau_q3 = None
        self.amp    = None
        self.amp_q1 = None
        self.amp_q3 = None

        self.kon            = None
        self.koff           = None
        self.KD_kinetic     = None
        self.Rmax           = None
        self.KD_equilibrium = None

        self._kF_list   = []   # KineticFit objects kept for plotSignals
        self._result_k  = None
        self._result_lm = None

    # ------------------------------------------------------------------
    def loadData(self, folder, files):
        '''Load all files and collect median tau, amp with Q1/Q3.'''
        self.folder = folder
        self.files  = files
        c_list      = []
        tau_list    = []
        tau_q1_list = []
        tau_q3_list = []
        amp_list    = []
        amp_q1_list = []
        amp_q3_list = []
        self._kF_list = []

        for fname, conc in self.files:
            kF = KineticFit.loadFit(filePath=self.folder + '/' + fname)
            self._kF_list.append(kF)

            tau_st = kF.getParamStats('tau')
            amp_st = kF.getParamStats('amp')
            c_list.append(conc)
            tau_list.append(tau_st['median'])
            tau_q1_list.append(tau_st['q1'])
            tau_q3_list.append(tau_st['q3'])
            amp_list.append(amp_st['median'])
            amp_q1_list.append(amp_st['q1'])
            amp_q3_list.append(amp_st['q3'])

        self.c      = np.array(c_list)
        self.tau    = np.array(tau_list)
        self.tau_q1 = np.array(tau_q1_list)
        self.tau_q3 = np.array(tau_q3_list)
        self.amp    = np.array(amp_list)
        self.amp_q1 = np.array(amp_q1_list)
        self.amp_q3 = np.array(amp_q3_list)

    # ------------------------------------------------------------------
    def fitKinetics(self):
        '''Fit 1/tau vs concentration with a censored linear model (hockey stick).

        kobs_obs(c) = min(kon*c + koff, kobs_max)

        kobs_max is a free parameter representing the instrument resolution ceiling.
        All data points are used; the plateau constrains kobs_max while the linear
        part constrains kon and koff.
        '''
        kobs = 1 / self.tau

        def kobs_censored(c, kon, koff, kobs_max):
            return np.minimum(kon * c + koff, kobs_max)

        mdl    = Model(kobs_censored)
        params = mdl.make_params(
            kon     = dict(value=(kobs.max() - kobs.min()) / (self.c.max() - self.c.min()), min=0),
            koff    = dict(value=kobs.min(),   min=0),
            kobs_max= dict(value=kobs.max(),   min=0),
        )
        self._result_k   = mdl.fit(kobs, params, c=self.c)
        self.kon         = self._result_k.params['kon'].value
        self.koff        = self._result_k.params['koff'].value
        self._kobs_max   = self._result_k.params['kobs_max'].value
        self.KD_kinetic  = self.koff / self.kon
        # saturation flag for plot: points at or above the fitted ceiling
        self._saturated  = kobs >= self._kobs_max * 0.95
        print(self._result_k.fit_report())
        print(f'kon  = {self.kon:.3e} /nM/s')
        print(f'koff = {self.koff:.3e} /s')
        print(f'KD   = {self.KD_kinetic:.3e} nM')
        print(f'kobs_max = {self._kobs_max:.3e} /s  (tau_min ~ {1/self._kobs_max:.1f} s)')

    # ------------------------------------------------------------------
    def fitEquilibrium(self):
        '''Fit amp vs concentration with Langmuir model.

        Extracts Rmax, KD_equilibrium.
        '''
        mdl    = Model(_langmuir)
        params = mdl.make_params(
            Rmax= dict(value=self.amp.max() * 1.2,    min=0),
            KD  = dict(value=self.c[len(self.c)//2],  min=0),
        )
        self._result_lm     = mdl.fit(self.amp, params, c=self.c)
        self.Rmax           = self._result_lm.params['Rmax'].value
        self.KD_equilibrium = self._result_lm.params['KD'].value
        print(self._result_lm.fit_report())

    # ------------------------------------------------------------------
    def plotSignals(self):
        '''Plot all signals and fits time-aligned to timeStart.'''
        colors  = plt.rcParams['axes.prop_cycle'].by_key()['color']
        handles = []
        fig, ax = plt.subplots()

        for i, (kF, (_, conc)) in enumerate(zip(self._kF_list, self.files)):
            sig, fit      = kF.getCleanDataFit()
            time0_idx     = kF.fitType.parameters.index('time0')
            time_shifted  = kF.time[:, np.newaxis] - kF.fittedParam[:, time0_idx] + self.timeStart
            color         = colors[i % len(colors)]
            ax.plot(time_shifted, sig, '-',  color=color, alpha=0.4)
            ax.plot(time_shifted, fit, '--', color=color, alpha=0.9)
            handles.append(Line2D([0], [0], color=color, linestyle='--', label=f'{conc} nM'))

        ax.axvline(self.timeStart, color='gray', linestyle='--', linewidth=0.8)
        ax.set_xlabel('time (s)')
        ax.set_ylabel('signal (nm)')
        ax.legend(handles=handles)
        plt.tight_layout()

    # ------------------------------------------------------------------
    def plotKinetics(self):
        '''Plot 1/tau vs concentration with censored linear (hockey-stick) fit.'''
        kobs    = 1 / self.tau
        c_dense = np.linspace(0, self.c.max() * 1.1, 300)

        def kobs_censored(c, kon, koff, kobs_max):
            return np.minimum(kon * c + koff, kobs_max)

        kon      = self._result_k.params['kon'].value
        koff     = self._result_k.params['koff'].value
        kobs_max = self._result_k.params['kobs_max'].value

        fig, ax = plt.subplots()
        if self._saturated.any():
            ax.errorbar(self.c[self._saturated], kobs[self._saturated],
                        yerr=[kobs[self._saturated] - 1/self.tau_q3[self._saturated],
                              1/self.tau_q1[self._saturated] - kobs[self._saturated]],
                        fmt='s', color='gray', capsize=4, alpha=0.6,
                        label='instrument-limited')
        ax.errorbar(self.c[~self._saturated], kobs[~self._saturated],
                    yerr=[kobs[~self._saturated] - 1/self.tau_q3[~self._saturated],
                          1/self.tau_q1[~self._saturated] - kobs[~self._saturated]],
                    fmt='r*', capsize=4, label='data (median, Q1-Q3)')
        ax.plot(c_dense, kobs_censored(c_dense, kon, koff, kobs_max),
                'b-', label='hockey-stick fit')
        ax.axhline(kobs_max, color='gray', ls=':', linewidth=0.8,
                   label=f'kobs_max = {kobs_max:.3e} /s')
        ax.set_xlabel('Concentration (nM)')
        ax.set_ylabel('1/tau  (1/s)')
        ax.set_title(f'kon={self.kon:.2e} /nM/s,  koff={self.koff:.2e} /s,'
                     f'  KD={self.KD_kinetic:.2e} nM')
        ax.legend()
        plt.tight_layout()

    # ------------------------------------------------------------------
    def plotEquilibrium(self):
        '''Plot amp vs concentration with Langmuir fit (log x-axis).'''
        c_fit = np.logspace(np.log10(self.c.min()/3), np.log10(self.c.max()*3), 300)

        fig, ax = plt.subplots()
        ax.semilogx(c_fit, _langmuir(c_fit, self.Rmax, self.KD_equilibrium),
                    'b-', label='Langmuir fit')
        ax.errorbar(self.c, self.amp,
                    yerr=[self.amp - self.amp_q1, self.amp_q3 - self.amp],
                    fmt='ko', capsize=4, label='data (median, Q1-Q3)')
        ax.axvline(self.KD_equilibrium, color='gray', ls='--',
                   label=f'KD={self.KD_equilibrium:.2e} nM')
        ax.set_xlabel('Concentration (nM)')
        ax.set_ylabel('R signal (nm)')
        ax.legend()
        plt.tight_layout()


# %% --- usage ---
if __name__ == '__main__':
    ffolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-05-28 dnaConcentrationRow\fits'
    files   = [
        #('20nM_fit.pkl',   20),
        ('50nM_fit.pkl',   50),
        ('100nM_fit.pkl',  100),
        ('1000nM_fit.pkl', 1000),
        ('2000nM_fit.pkl', 2000),
    ]

    rf = RateFit()
    rf.loadData(folder=ffolder, files=files)
    rf.plotSignals()
    rf.fitKinetics()
    rf.plotKinetics()
    rf.fitEquilibrium()
    rf.plotEquilibrium()
    plt.show()
# %%
