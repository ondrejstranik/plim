# -*- coding: utf-8 -*-
"""
set of functions to fit a curve


Created on Tue Nov 19 13:12:23 2019

@author: OStranik
"""
import sys
from matplotlib import pylab as plt
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import nnls
from scipy.optimize import fminbound
from scipy.optimize import brentq
from scipy import integrate


def gaussian(x, amp, cen, wid):
    return amp * np.exp(-(x-cen)**2 / (wid/(2*np.sqrt(2*np.log(2))))**2)

def multigaussian( x, amp, cen, wid):
    mg = np.zeros_like(x).astype('float')
    for A,C,W in zip(amp,cen, wid):
        mg += gaussian(x,A,C,W)
    return mg

def fit_polynom(x,y,Np = 10):
    z = np.polyfit(x, y, Np)
    p = np.poly1d(z)
    return p

def fit_polynom_ext(x,y, Np = 10):
    z = np.polyfit(np.hstack((2*x[0] - x[1],x,2*x[-1]-x[-2])),
                    np.hstack((2*y[0] -y[1],y,2*y[-1]-y[-2])), Np)
    p = np.poly1d(z)    
    return p

def fit_polynom_der(x,y,Np = 10):
    def xrenorm(xx):
        return (xx-x.mean())/x.std()
    def resid(pars, x, y):
        return ((y-np.polyval(pars,x))**2).sum()
    def constr(pars, x, y):
        return (np.polyval(np.polyder(pars,m = 1),x[[0,-1]]) - 
                [(y[1]-y[0])/(x[1]-x[0]),(y[-1]-y[-2])/(x[-1]-x[-2])] )

    con = {'type': 'eq', 'fun': constr, 'args': (xrenorm(x),y)}
    res = minimize(resid,np.ones(Np),args = (xrenorm(x),y), 
                   method='trust-constr', options={'maxiter':5000000}, 
                   constraints=con)
    p = np.poly1d(res.x)
    return lambda xx:p(xrenorm(xx))

def fit_gaussian(x,y,Np = 10):
    matg = np.zeros((x.size,Np))
    gcen = np.linspace(x[0]-(x[-1]-x[0])/(Np-1),x[-1]+(x[-1]-x[0])/(Np-1),Np, dtype=float)
    gfwhm = (x[-1]-x[0])/(Np-2)*4
    for ii in range(Np):
        matg[:,ii] = gaussian(x,1, gcen[ii],gfwhm).T
    (spR_coeff, _) = nnls(matg,y)
    return lambda xx: multigaussian(xx,spR_coeff,gcen,gcen*0 + gfwhm)

def get_peakmax(f,peakwidth = 80, ini_guess = 550):
    peakmax = fminbound(lambda xx: -f(xx),ini_guess-peakwidth,ini_guess+peakwidth)
    return peakmax
 
def get_peakstart(f,peakwidth = 80, ini_guess = 550):
    try:
        lstart = brentq( lambda xx: f(xx) - f(xx+peakwidth),ini_guess-peakwidth, ini_guess)
    except:
        lstart = 0
    return lstart
    
def get_peakcenter(f,peakwidth =80, ini_guess = 550):
    lstart = get_peakstart(f,peakwidth, ini_guess)
    nom = integrate.quad( lambda xx:f(xx)*xx,lstart,lstart+peakwidth)[0]
    denom = integrate.quad( lambda xx:f(xx),lstart,lstart+peakwidth)[0]
    if denom != 0:
        peakcenter = nom/denom
    else:
        peakcenter = 0
    return peakcenter

def get_statistics(x,y,fitfun,ffvar,peakfun, pfvar, Nave = 1):
    peaksig = np.empty(0)
    for row in y.T:
        f = fitfun(x,row,**ffvar)
        peaksig = np.append(peaksig,peakfun(f,**pfvar))
    if Nave > 1:
        peaksig = np.mean(np.reshape(peaksig,(peaksig.shape[0]//Nave,Nave)), axis = 1)
    getmean = np.mean(peaksig)
    getstd = np.std(peaksig)
    getpeaksig = peaksig
    return (getmean,getstd,getpeaksig)

def TDataGen(x0 = np.arange(450,650,1, dtype=float),
             x = np.linspace(450,650,10, dtype=float),
             Nsig = 100 ,pcount = 1e6,
             NP_Nout = 1.33, NP_core ='Au',NP_shell ='Au',
             NP_r =40, NP_d_shell= 0, NP_density = 12e-6):
    try:
        sys.path.append(r'G:\office\work\projects - free\19-02-25 collidal lithography theory - Daniel\19-11-10 final codes daniel')
        from coreShell import c_coreshell as Cext
        C_NP0 = np.ravel(Cext(x0,NP_core,NP_shell,NP_Nout,NP_r,NP_d_shell,3)[:,1])
        C_NP = np.ravel(Cext(x,NP_core,NP_shell,NP_Nout,NP_r,NP_d_shell,3)[:,1])
    except:
        gp = ([3,1,1],[540, 560, 580],[100,100,100])
        C_NP0 = multigaussian(x0,*gp)  
        C_NP = multigaussian(x,*gp)
        print('approximation of NP spectra is used')
    Tideal = 1 - C_NP0*np.pi*NP_r**2*NP_density            
    I0data = pcount*np.ones((x.size,Nsig))
    I0data = np.random.poisson(I0data)    
    Idata = np.tile(pcount*(1 - C_NP*np.pi*NP_r**2*NP_density),(Nsig,1)).transpose()
    Idata = np.random.poisson(Idata)
    Tdata = Idata/I0data
    return (Tideal,Tdata)

def plotsummary(x0,y0,x,y,peakfits,peaklines,peakstd,myleg):
    f=plt.figure(figsize=(10,4))
    cm = plt.get_cmap('gist_rainbow')
    mycolors = [cm(1.*i/len(myleg)) for i in range(len(myleg))]
    ax1 = f.add_subplot(121)
    ax2 = f.add_subplot(222)
    ax3 = f.add_subplot(224)
    ax1.plot(x0,y0,'k.-',label='original curve')
    ax1.plot(x,y,'or',label='data')
    ax1.set_prop_cycle( color = mycolors)   
    ax1.plot(x0,peakfits.T)
    ax1.legend()
    ax1.set_ylabel('1-T')
    ax1.set_xlabel('wavelength [nm]')
    ax2.set_prop_cycle( color = mycolors)   
    ax2.plot(peaklines.T)
    ax2.set_ylabel('wavelength [nm]')
    ax3.bar(range(peakstd.size),peakstd, tick_label = myleg, color = mycolors)
    ax3.set_ylabel('std [nm]')
    ax3.set_xlabel('fit type')
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=70 )
    plt.show()
    return f

#%% start of the program 
if __name__== "__main__":


    #define ideal curve and measured data with noise 
    x0 = np.arange(450,650,1, dtype=float)
    Ndatapoints = 13
    x = np.linspace(450,650,Ndatapoints, dtype=float)
    Nsignals = 50
    Nparameters = 8
    Photoncounts = 1e6
    Nout1= 1.33
    Nout2 = 1.43
    NPden = 3e-6
 #   Peakguess = 550
 #   pwidth = 80

    # ref. index 1.33
    print('refractive index 1.33')
    (Tideal, Tdata) = TDataGen( x0,x,Nsig = Nsignals, pcount = Photoncounts,
                                NP_Nout =Nout1, NP_density = NPden)
    y0, y  = 1- Tideal, 1- Tdata

    # calculate the fits   
    mystat = list()
    myleg = list()
    mypeakfit = list()

    # peak max, different fits
    print('set 1')
    myleg.extend(['pol \n max'])
    mystat.extend(get_statistics(x,y,fit_polynom,{'Np':Nparameters},get_peakmax,{}))
    mypeakfit.extend(fit_polynom(x,y[:,0], **{'Np':Nparameters})(x0))
    myleg.extend(['pol_ext \n max'])
    mystat.extend(get_statistics(x,y,fit_polynom_ext,{'Np':Nparameters},get_peakmax,{}))
    mypeakfit.extend(fit_polynom_ext(x,y[:,0], **{'Np':Nparameters})(x0))
    myleg.extend(['pol_der \n max'])
    mystat.extend(get_statistics(x,y,fit_polynom_der,{'Np':Nparameters},get_peakmax,{}))
    mypeakfit.extend(fit_polynom_der(x,y[:,0],  **{'Np':Nparameters})(x0))
    myleg.extend(['gauss \n max'])
    mystat.extend(get_statistics(x,y,fit_gaussian,{'Np':Nparameters},get_peakmax,{}))
    mypeakfit.extend(fit_gaussian(x,y[:,0],  **{'Np':Nparameters})(x0))
    # peak center, different fits
    print('set 2')
    myleg.extend(['pol \n center'])
    mystat.extend(get_statistics(x,y,fit_polynom,{'Np':Nparameters},get_peakcenter,{}))
    mypeakfit.extend(fit_polynom(x,y[:,0], **{'Np':Nparameters})(x0))
    myleg.extend(['pol_ext \n center'])
    mystat.extend(get_statistics(x,y,fit_polynom_ext,{'Np':Nparameters},get_peakcenter,{}))
    mypeakfit.extend(fit_polynom_ext(x,y[:,0], **{'Np':Nparameters})(x0))
    myleg.extend(['pol_der \n center'])
    mystat.extend(get_statistics(x,y,fit_polynom_der,{'Np':Nparameters},get_peakcenter,{}))
    mypeakfit.extend(fit_polynom_der(x,y[:,0],  **{'Np':Nparameters})(x0))
    myleg.extend(['gauss \n center'])
    mystat.extend(get_statistics(x,y,fit_gaussian,{'Np':Nparameters},get_peakcenter,{}))
    mypeakfit.extend(fit_gaussian(x,y[:,0],  **{'Np':Nparameters})(x0))
    # peak start, different fits
    print('set 3')
    myleg.extend(['pol \n start'])
    mystat.extend(get_statistics(x,y,fit_polynom,{'Np':Nparameters},get_peakstart,{}))
    mypeakfit.extend(fit_polynom(x,y[:,0], **{'Np':Nparameters})(x0))
    myleg.extend(['pol_ext \n start'])
    mystat.extend(get_statistics(x,y,fit_polynom_ext,{'Np':Nparameters},get_peakstart,{}))
    mypeakfit.extend(fit_polynom_ext(x,y[:,0], **{'Np':Nparameters})(x0))
    myleg.extend(['pol_der \n start'])
    mystat.extend(get_statistics(x,y,fit_polynom_der,{'Np':Nparameters},get_peakstart,{}))
    mypeakfit.extend(fit_polynom_der(x,y[:,0],  **{'Np':Nparameters})(x0))
    myleg.extend(['gauss \n start'])
    mystat.extend(get_statistics(x,y,fit_gaussian,{'Np':Nparameters},get_peakstart,{}))
    mypeakfit.extend(fit_gaussian(x,y[:,0],  **{'Np':Nparameters})(x0))
    
    peakshift = np.array(mystat[0::3])
    peakstd = np.array(mystat[1::3])
    peaklines = np.stack(mystat[2::3], axis=0 )
    peakfits = np.reshape(mypeakfit, (len(mypeakfit)//x0.size,x0.size))


#%% display results
    plt.close('all')
    f = plotsummary(x0,y0,x,y[:,0],peakfits,peaklines,peakstd,myleg)
    f.suptitle('Photoncounts = {0}, parameters = {1}, datapoints = {2}'.format(
            Photoncounts,Nparameters, Ndatapoints))
    plt.tight_layout()

