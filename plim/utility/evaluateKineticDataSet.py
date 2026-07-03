''' script to evaluate kinetic data'''

#%%

from plim.algorithm.rateFit import RateFit
import matplotlib.pyplot as plt



ffolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-05-28 dnaConcentrationRow\fits'
files   = [
    #('20nM_fit.pkl',   20),
    ('50nM_fit.pkl',   50),
    ('100nM_fit.pkl',  100),
    ('1000nM_fit.pkl', 1000),
    ('2000nM_fit.pkl', 2000),
]

ffolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-06-03 spottingDNA\fits'
files   = [
    ('capture_5uM_target_10nM_fit.pkl',   10),
    ('capture_5uM_target_20nM_fit.pkl',   20),
    ('capture_5uM_target_50nM_fit.pkl',   50),
    ('capture_5uM_target_200nM_fit.pkl',   200),
    ('capture_5uM_target_1000nM_fit.pkl',  1000),


]



rf = RateFit()
rf.loadData(folder=ffolder, files=files)
rf.plotSignals()
rf.fitKinetics()
rf.plotKinetics()
rf.fitEquilibrium()
rf.plotEquilibrium()
plt.show()