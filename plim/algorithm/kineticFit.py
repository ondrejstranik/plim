'''
package to fit binding kinetic data
'''

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf
import inspect
import csv
from lmfit import Model
from enum import Enum
import inspect

def functionPFO(x,x0,a,b):
    ''' pseudo first order binding curve'''
    res = x*0.0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0.0
    #b = np.abs(b) + 1e-6
    b += 1e-6

    res[xb] = a*(1-np.exp(-(x[xb]-x0)/b))
    return res

def functionEDecay(x,x0,a,b):
    ''' exponential decay function '''
    res = x*0.0
    xb = x>=x0
    xa = x< x0
    res[xa] = a
    #b = np.abs(b) + 1e-6
    b += 1e-6

    res[xb] = a*np.exp(-(x[xb]-x0)/b)
    return res

def functionZO(x,x0,a):
    ''' Zero Order binding (linear) function - approximation of PFO'''
    res = x*0.0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0
    res[xb] = a*(x[xb]-x0)
    return res


#def functionPFO(x,x0,a,b):
#    xMod = (erf((x-x0)/10)+1)/2*(x-x0)
#    res = a*(1-np.exp(-xMod*b))
#    return res

def functionP1(x,c0,c1):
    ''' linear function'''
    res = c0 + c1*x
    return res

def functionBinding(x,time0,tau,amp,p0,p1):
    return functionPFO(x,time0,amp,tau) + functionP1(x-time0,p0,p1)

def functionLinearBinding(x,time0,slope,p0,p1):
    return functionZO(x,time0,slope) + functionP1(x-time0,p0,p1)

def functionDesorption(x,time0,tau,amp,p0,p1):
    return functionEDecay(x,time0,amp,tau) + functionP1(x-time0,p0,p1)

def functionDoubleBinding(x,time0,tau1,amp1,tau2,amp2,p0,p1):
    ''' double exponential association + linear background '''
    return (functionPFO(x,time0,amp1,tau1)
            + functionPFO(x,time0,amp2,tau2)
            + functionP1(x-time0,p0,p1))


class FitType(Enum):
    ADSORPTION = ("adsorption", functionBinding)
    DESORPTION = ("desorption", functionDesorption)
    LINEAR = ("linear", functionLinearBinding)
    ADSORPTION_DOUBLE = ("adsorption_double", functionDoubleBinding)

    def __init__(self, label, fitFunction):
        self.label = label
        self.function = fitFunction
        sig = inspect.signature(fitFunction)
        self.parameters = [p for p in sig.parameters.keys() if p != 'self']

    @classmethod
    def from_label(cls, label_string):
        for member in cls:
            if member.label == label_string:
                return member
        raise ValueError(f"'{label_string}' it is not defined FitType.label")


class KineticFit:
    ''' class for fitting binding kinetics curves'''

    DEFAULT = {'fitType': FitType.ADSORPTION # type of kinetic fit 
               }


    def __init__(self,**kwargs):
        ''' initialization of the parameters '''

        # data
        self.time = None # numpy 1D array
        self.signal = None # numpy array each column represent one set

        # info about the data
        self.table = {'name': None}

        # fitting parameters
        self.fittedParam = None
        self.fitType = self.DEFAULT['fitType']
        self.model = None
        self.modelParams = None

        self.setFitFunction()

    def setSignal(self,signal):
        ''' define '''
        self.signal = signal

    def setTime(self,time):
        ''' set the corresponding time'''
        self.time = time

    def setTable(self,table):
        ''' set additional info about the fitting data '''
        self.table = table         

    def setFitParameter(self, name=None, value=None, fixed=None, fitType=None, min=None, max=None):
        ''' set fitting parameters'''
        if fitType is not None: self.setFitFunction(fitType)
        if name is not None:
            self.modelParams[name].set(
                **({} if value is None else {'value': value}),
                **({} if fixed is None else {'vary': not fixed}),
                **({} if min   is None else {'min':   min}),
                **({} if max   is None else {'max':   max}),
            )

    def setFitFunction(self, fitType:FitType =None):
        ''' define fit function '''
        if fitType is not None:
            self.fitType = fitType
            self.model = Model(fitType.function)
            self.modelParams = self.model.make_params()

    def calculateFit(self):
        ''' calculate fits'''
        nFit = self.signal.shape[1]
        self.fittedParam = np.zeros((nFit,len(self.modelParams)))

        for ii in range(nFit):
            try:
                result = self.model.fit(self.signal[:,ii],self.modelParams, x= self.time)
                self.fittedParam[ii,:] = np.array([result.best_values[_name] 
                                                for _name in result.best_values.keys()])
            except:
                print(f'could not fit signal{ii}')
        print(f'model parameters {self.modelParams}')


    def getFittedSignal(self,idx):
        return self.model.func(self.time,*self.fittedParam[idx,:])

    def getCleanDataFit(self):
        '''Return signal and fit with background subtracted for all curves.

        Returns
        -------
        clean_signal : ndarray (n_time, n_curves)  Raw signal minus background.
        clean_fit    : ndarray (n_time, n_curves)  Fitted curve minus background.
        '''
        nFit = self.signal.shape[1]
        clean_signal = np.empty_like(self.signal)
        clean_fit    = np.empty((len(self.time), nFit))
        for ii in range(nFit):
            bg = self.getFittedBackground(ii)
            clean_signal[:, ii] = self.signal[:, ii] - bg
            clean_fit[:, ii]    = self.getFittedSignal(ii) - bg
        return clean_signal, clean_fit


    def getFittedBackground(self,idx):
        _param = self.fittedParam[idx,:]*1.0
        if self.fitType == FitType.LINEAR:
            _param[1]= 0 # set slope of binding to zero
        if self.fitType == FitType.ADSORPTION:
            _param[2]= 0 # set amplitude of binding to zero
        if self.fitType == FitType.DESORPTION:
            _param[2]= 0 # set amplitude of desorption to zero
        if self.fitType == FitType.ADSORPTION_DOUBLE:
            _param[2]= 0 # amp1
            _param[4]= 0 # amp2
        return self.model.func(self.time,*_param)
        

    def saveFitInfo(self,folder,fileName):
        ''' save fits info into .txt file'''
        # save info table
        # structure is following
        # fitType.label
        # header - name param1 param2 ....
        # value - name param1 param2 ... (curve1)
        # value - name param1 param2 ... (curve2)
        # value - name param1 param2 ... (curveN)
        
        # 2. Build the dictionary dynamically
        _dataDict = {'name': self.table['name']}

        # 3. Loop through the parameters and map them to the column index
        for index, param in enumerate(self.fitType.parameters):
            _dataDict[param] = self.fittedParam[:, index]

        with open(folder +"/" + fileName, "w") as outfile:
        
            # pass the csv file to csv.writer function.
            #writer = csv.writer(outfile, delimiter ='\t')
            writer = csv.writer(outfile, delimiter =',')
            # write label of the fitting type
            writer.writerow(self.fitType.label)            
            # pass the dictionary keys to writerow
            # function to frame the columns of the csv file
            writer.writerow(_dataDict.keys())
            # make use of writerows function to append
            # the remaining values to the corresponding
            # columns using zip function.
            writer.writerows(zip(*_dataDict.values()))
        print('fit info exported')

    def loadFitInfo(self,folder,fileName):
        ''' load fit info
         return
          fitType.label (string)
           list of name of each curve
            2D numpy array with parameters of the fit for each curve '''
        name= []

        with open(folder +"/" + fileName) as infile:
            # 1. Read the very first row to get the fitType label
            # .strip() removes any hidden newline characters (\n)
            raw_label = infile.readline().strip()
            # Clean up commas if it was saved as a CSV row (e.g., "my_label,")
            fitTypeLabel = raw_label.split(',')[0]
            
            reader = csv.DictReader(infile, delimiter=',')

            # get the names of the parameters (without the name parameter)
            param_columns_dict = {key: [] for key in reader.fieldnames if key != 'name'}

            for row in reader:
                for param_key in param_columns_dict.keys():
                    param_columns_dict[param_key].append(float(row[param_key]))

            fittedParam = np.array(list(param_columns_dict.values()), dtype=float).T


        return (fitTypeLabel, name, fittedParam)

if __name__ == "__main__":
    pass















