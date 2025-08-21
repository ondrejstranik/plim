'''
package to fit binding kinetic data
'''

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf
import inspect
import csv
from lmfit import Model

#def functionPFO(x,x0,a,b):
#    ''' pseudo first order binding curve'''
#    res = x*0
#    xb = x>=x0
#    xa = x< x0
#    res[xa] = 0
#    if b!=0:
#        res[xb] = a*(1-np.exp(-(x[xb]-x0)/b))
#    else:
#        res[xb] = a + x[xb]*0
#    return res

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

#def functionPFO(x,x0,a,b):
#    xMod = (erf((x-x0)/10)+1)/2*(x-x0)
#    res = a*(1-np.exp(-xMod*b))
#    return res

def functionP1(x,c0,c1):
    ''' linear function'''
    res = c0 + c1*x
    return res

def functionBinding(x,time0,tau,amp,p0,p1):
    return functionPFO(x,time0,amp,tau) + functionP1(x,p0,p1)


class KineticFit:
    ''' class for fitting binding kinetics curves'''

    DEFAULT = {'fitType': 'adsorption' # type of kinetic fit
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

    def setFitParameter(self,name = None,value = None, fixed= None, fitType=None):
        ''' set fitting parameters '''

        if fitType is not None: self.setFitFunction(fitType)

        if name is not None:
            if value is not None:
                self.modelParams[name].value = value
            if fixed is not None:
                self.modelParams[name].vary = ~fixed

    def setFitFunction(self, fitType=None):
        ''' define fit function '''
        if fitType is not None:
            self.fitType = fitType
        if self.fitType == 'adsorption':
            self.model = Model(functionBinding)
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


    def getFittedSignal(self,idx):
        return self.model.func(self.time,*self.fittedParam[idx,:])
    
    def getFittedBackground(self,idx):
        _param = self.fittedParam[idx,:]*1.0
        _param[2]= 0 # set aplitude of binding to zero
        return self.model.func(self.time,*_param)

    def saveFitInfo(self,folder,fileName):
        ''' save fits info into .txt file'''
        # save info table
        _dataDict = {'name': self.table['name'],
                 'time0': self.fittedParam[:,0],
                 'amp': self.fittedParam[:,1],
                 'tau': self.fittedParam[:,2],
                 'p0': self.fittedParam[:,3],
                 'p1': self.fittedParam[:,4]}

        with open(folder +"/" + fileName, "w") as outfile:
        
            # pass the csv file to csv.writer function.
            #writer = csv.writer(outfile, delimiter ='\t')
            writer = csv.writer(outfile, delimiter =',')
            # pass the dictionary keys to writerow
            # function to frame the columns of the csv file
            writer.writerow(_dataDict.keys())
            # make use of writerows function to append
            # the remaining values to the corresponding
            # columns using zip function.
            writer.writerows(zip(*_dataDict.values()))
        print('fit info exported')

    def loadFitInfo(self,folder,fileName):
        ''' load fit info '''
        name= []
        time0 = []
        amp = []
        tau = []
        p0 = []
        p1 = []
        with open(folder +"/" + fileName) as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            # skip header
            next(spamreader)
            for row in spamreader:
                if row == []: continue
                name.append(row[0])
                time0.append(float(row[1]))
                amp.append(float(row[2]))
                tau.append(float(row[3]))
                p0.append(float(row[4]))
                p1.append(float(row[5]))

        fitParam = np.array([time0,amp,tau,p0,p1])

        return name, fitParam

if __name__ == "__main__":
    pass















