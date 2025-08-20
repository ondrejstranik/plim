''' testing script for fitting function variable parameters'''
#%%
from scipy.optimize import curve_fit
import numpy as np
from functools import partial
import inspect
from scipy._lib._util import getfullargspec_no_self as _getfullargspec
from lmfit import Model

#%%
def funcP(x,c0,c1,c2,c3):
    ''' fit function'''
    res =  c0+ c1*x + c2*x*2 + c3*x**3
    return res

gmodel = Model(funcP)

params = gmodel.make_params()

pFixed = [True,True,False,False]
pEst = [1,1,1,1]

for ii,name in enumerate(gmodel.param_names):
    params[name].value = pEst[ii]
    params[name].vary = pFixed[ii]


print(f'parameter names: {gmodel.param_names}')
#%%

xData = np.arange(10)
y_eval = gmodel.eval(params, x=xData)
yToFit = y_eval +np.random.normal(0, 0.2, xData.size)

result = gmodel.fit(yToFit, params, x=xData)

print(f'parameter best values: {result.best_values}')






