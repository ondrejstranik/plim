'''
package to fit binding kinetic data
'''

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf
import inspect
import csv


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
    res = x*0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0
    res[xb] = a*(1-np.exp(-(x[xb]-x0)/(b+1e-6)))
    return res

#def functionPFO(x,x0,a,b):
#    xMod = (erf((x-x0)/10)+1)/2*(x-x0)
#    res = a*(1-np.exp(-xMod*b))
#    return res



def funcP1(x,c0,c1):
    ''' linear function'''
    res = c0 + c1*x
    return res


class KineticFit:
    ''' class for fitting binding kinetics curves'''

    DEFAULT = {'fitType': 'adsorption' # type of kinetic fit
               }


    def __init__(self,**kwargs):
        ''' initialization of the parameters '''

        # data
        self.time = None # numpy 1D array
        self.signal = None # numpy array each column represent one set
        self.fitEstimate = None

        # info about the data
        self.table = {'name': None}

        # fitting parameters
        self.fitParam = None
        self.fixedParam = None
        self.fitType = self.DEFAULT['fitType']
        self.fitFunction = None
        self.bcgFunction = None

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

    def setFitParameter(self,time0=None,tau=None,amp=None,
                        fitType=None, fitEstimate = None, fixedParam=None):
        ''' set fitting parameters '''

        if fitType is not None: 
            self.fitType = fitType
            self.setFitFunction()
        if time0 is not None: self.fitEstimate[0] = time0
        if amp is not None: self.fitEstimate[1] = amp
        if tau is not None: self.fitEstimate[2] = tau
        if fitEstimate is not None: self.fitEstimate = fitEstimate

        if fixedParam is not None: self.fixedParam = fixedParam

    def setFitFunction(self):
        ''' define fit function depending on the number of polynomial parameters of background'''
        if self.fitType == 'adsorption':
            _fitFunction = functionPFO
            self.bcgFunction = funcP1
            self.fitFunction = lambda x,x0,a,b,c0,c1 : _fitFunction(x,x0,a,b) + self.bcgFunction(x,c0,c1)
            
            sig = inspect.signature(self.fitFunction)
            self.fitEstimate = np.zeros(len(sig.parameters)-1)

    def calculateFit(self):
        ''' calculate fits'''
        nFit = self.signal.shape[1]
        self.fitParam = np.zeros((nFit,len(self.fitEstimate)))
        if self.fixedParam is None: self.fixedParam = np.ones(len(self.fitEstimate),dtype=bool)

        self.fixedParam[4] = False

        print(f'fixedParam {self.fixedParam}')

        # TODO: not Working! correct it!
        minBound = [-np.inf if ii==True else self.fitEstimate[ii] for ii in self.fixedParam]
        maxBound = [np.inf if ii==True else self.fitEstimate[ii] for ii in self.fixedParam]

        print(minBound)
        print(maxBound)


        for ii in range(nFit):
            try:
                x = self.time
                y = self.signal[:,ii]
                popt,pocv = curve_fit(self.fitFunction,x,y,p0 = self.fitEstimate.tolist(),
                                      bounds=(minBound,maxBound))
                self.fitParam[ii,:] = popt
            except:
                print(f'did not find fit for signal {ii}')

    def saveFitInfo(self,folder,fileName):
        ''' save fits info into .txt file'''
        # save info table
        _dataDict = {'name': self.table['name'],
                 'time0': self.fitParam[:,0],
                 'amp': self.fitParam[:,1],
                 'tau': self.fitParam[:,2],
                 'c0': self.fitParam[:,3],
                 'c1': self.fitParam[:,4]}

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
        c0 = []
        c1 = []
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
                c0.append(float(row[4]))
                c1.append(float(row[5]))

        fitParam = np.array([time0,amp,tau,c0,c1])

        return name, fitParam

if __name__ == "__main__":
    pass















