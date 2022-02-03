### This file is a part of the Syncpy library.
### Copyright 2015, ISIR / Universite Pierre et Marie Curie (UPMC)
### Main contributor(s): Giovanna Varni, Marie Avril,
### syncpy@isir.upmc.fr
### 
### This software is a computer program whose for investigating
### synchrony in a fast and exhaustive way. 
### 
### This software is governed by the CeCILL-B license under French law
### and abiding by the rules of distribution of free software.  You
### can use, modify and/ or redistribute the software under the terms
### of the CeCILL-B license as circulated by CEA, CNRS and INRIA at the
### following URL "http://www.cecill.info".

### As a counterpart to the access to the source code and rights to
### copy, modify and redistribute granted by the license, users are
### provided only with a limited warranty and the software's author,
### the holder of the economic rights, and the successive licensors
### have only limited liability.
### 
### In this respect, the user's attention is drawn to the risks
### associated with loading, using, modifying and/or developing or
### reproducing the software by the user in light of its specific
### status of free software, that may mean that it is complicated to
### manipulate, and that also therefore means that it is reserved for
### developers and experienced professionals having in-depth computer
### knowledge. Users are therefore encouraged to load and test the
### software's suitability as regards their requirements in conditions
### enabling the security of their systems and/or data to be ensured
### and, more generally, to use and operate it in the same conditions
### as regards security.
### 
### The fact that you are presently reading this means that you have
### had knowledge of the CeCILL-B license and that you accept its terms.

"""
.. moduleauthor:: Marie Avril
"""

import numpy as np # For math operation
import pandas as pd # For DataFrame
import matplotlib.pyplot as plt # Plotting package
from math import ceil

from Methods.utils import Standardize
from Method import Method, MethodArgList

class S_Estimator(Method):
    """
    S_Estimator computes the S-Estimator, Genuine and Random Synchronization index among multiple monovariate signals (organized as a list of pandas DataFrame). 
    
    **Reference :**
    
    * Cui, D. and al., Estimation of genuine and random synchronization in multivariate neural series. Neural Networks 23 (2010) 698-704.
    * Andrzejak, R. and al., Bivariate surrogate techniques: Necessity, strengths, and caveats. Physical Review E 68, 066202 (2003). 
    * Schreiber, T. and al., Surrogate time series. Physica D 142 (2000) 346-382.
    
    :param surr_nb_iter:
        Number of surrogate iterations. Default : 100 
    :type surr_nb_iter: int
    
    :param plot:
        if True the plot of surrogates signals is returned. Default: False
    :type plot: bool
    """
    argsList = MethodArgList()
    argsList.append('surr_nb_iter', 100, int,
                    'Number of surrogate iterations.')
    argsList.append('plot', False, bool, 'plot of surrogates signals is returned')

    ''' Constructor '''
    def __init__(self, surr_nb_iter = 100, plot = False, **kwargs):
        super(S_Estimator, self).__init__(plot, **kwargs)
        #In the constructor we can check that params have corrects values and initialize stuff
        
        ' Raise error if parameters are not in the correct type '
        try :
            if not(isinstance(surr_nb_iter, int)) : raise TypeError("Requires surr_nb_iter to be an integer")
            if not(isinstance(plot, bool))        : raise TypeError("Requires plot to be a boolean")
        except TypeError as err_msg:
            raise TypeError(err_msg)
            return
        
        ' Raise error if parameters do not respect input rules '
        try : 
            if surr_nb_iter <= 0 : raise ValueError("Requires surr_nb_iter to be a strictly positive scalar")
        except ValueError as err_msg:
            raise ValueError(err_msg)
            return
        
        self._surr_nb_iter = surr_nb_iter
        self._plot = plot
        
        return

    
    def plot_result(self, result):
        """
        Plot surrogates signals
        
        :param result:
            S-estimator result from compute() (only 'surrogate_signal' used)
        :type result: dict
        
        :returns: plt.figure 
         -- figure plot
        
        """
        ' Raise error if parameters are not in the correct type '
        try :
            if not(isinstance(result, dict)) : raise TypeError("Requires result to be a dictionary")
        except TypeError as err_msg:
            raise TypeError(err_msg)
            return
        
        ' Raise error if not the good dictionary '
        try : 
            if not 'surrogate_signal' in result : raise ValueError("Requires dictionary to be the output of compute() method")            
        except ValueError as err_msg:
            raise ValueError(err_msg)
            return
        
        nrows = int(ceil(result['surrogate_signal'].shape[1]))
        figure, ax = plt.subplots(nrows, sharex=True)
    
        n = np.arange(0,result['surrogate_signal'].shape[0])
        idx = 0 
        for col in result['surrogate_signal'].columns :
            ax[idx].grid(True) # Display a grid
            ax[idx].set_title('Surrogate signal for : ' + col + ' variable')
            ax[idx].plot(n, result['surrogate_signal'][col].values)
            idx += 1
            
        ax[idx-1].set_xlabel('Samples')
            
        return figure
    
    
    def getSynchronizationIndex(self, lambda_i):
        """
         Compute Synchronization Index (SI)
          
        :param lambda_i:
            normalized eigenvalues (depending on the type of SI)
        :type lambda_i: np.array

        :returns: float
            -- Synchronization index 
        """
        
        tmp = [lambda_i[k] * np.log(lambda_i[k]) for k in range(len(lambda_i))]
        
        SI = 1 + sum(tmp) / np.log(len(lambda_i))
        
        return SI
        
    
    
    def AAFT_surrogates(self,Xi):
        """
         Computes amplitude adjusted Fourier Transform (AAFT) method to create a surrogate signal.
         Get starting point / initial conditions for R surrogates
          
        :param Xi:
            signal to surrogate
        :type Xi: np.array

        :returns: np.array
            -- surrogated signal  
        """
        
        Xi_fft = np.fft.rfft(Xi)
        Xi_ampli = np.abs(Xi_fft) # get original amplitude
        
        #  Create sorted Gaussian reference series
        gaussian = np.random.randn(Xi.shape[0])
        gaussian.sort()
        
        #  Rescale data to Gaussian distribution
        ranks = Xi.argsort()
        rescaled_data = np.zeros(Xi.shape[0])
        
        for i in xrange(Xi.shape[0]):
            rescaled_data[i] = gaussian[ranks[i]]

        #  Phase randomize rescaled data
        
        #  Get shapes
        N = Xi.shape[0]
        len_phase = Xi_fft.shape
        
        #  Generate random phases uniformly distributed in the
        #  interval [0, 2*Pi]
        phases = np.random.uniform(low=0, high=2 * np.pi)
        
        #  Add random phases uniformly distributed in the interval [0, 2*Pi]
        Xi_fft *= np.exp(1j * phases)

        #  Calculate IFFT and take the real part, the remaining imaginary part
        #  is due to numerical errors.
        phase_randomized_data = \
            np.ascontiguousarray(np.real(np.fft.irfft(Xi_fft)))

        #  Rescale back to amplitude distribution of original data
        sorted_original = Xi.copy()
        sorted_original.sort()

        ranks = phase_randomized_data.argsort()

        for i in xrange(Xi.shape[0]):
            rescaled_data[i] = sorted_original[ranks[i]]
     
        return rescaled_data
    
        
    def refined_AAFT_surrogate(self, X):
        """
         Computes an Iteratively refined amplitude adjusted Fourier Transform (AAFT) method to create a surrogate signal. 
         
        .. note:: Assume that original signal X is already standardized.
        
        :param X:
            signal to surrogate
        :type X: pd.DataFrame

        :returns: pd.DataFrame
            -- surrogated signal
        :returns: np.array
            -- average eigvalues of surrogate signal among all iterations    
        """
        
        ''' 1- Initialization '''
        X_fft = {}
        X_ampli = {}
        X_sorted = {}
        X_surr = {}
        X_surr_eig = {}
        X_surr_tot_ampli = {}
        for col in X.columns :
            # get real amplitude
            Xi_fft = np.fft.rfft(X[col].values)
            Xi_ampli = np.abs(Xi_fft)
            X_fft.update({col : Xi_fft})
            X_ampli.update({col : Xi_ampli})
            
            # get sorted real values
            sorted_Xi = X.copy()[col].values
            sorted_Xi.sort() 
            X_sorted.update({col : sorted_Xi})
            
            # shuffle original data for surrogate initialization
            Xi_surr = X.copy()[col].values
            np.random.shuffle(Xi_surr) 
            #Xi_surr = self.AAFT_surrogates(Xi)
            X_surr.update({col : Xi_surr})

        # save initial surrogate eigen values
        df_X_surr = pd.DataFrame(X_surr)
        R = np.dot((df_X_surr.values).T, df_X_surr.values) / float(X.index.size) # Correlation matrix
        eig_values_surr, eig_vectors_surr = np.linalg.eig(R) # Eigenvalues decomposition
        eig_values_surr = np.sort(np.real(eig_values_surr)) # sort by increasing order
        X_surr_eig.update({0 : eig_values_surr})

        for p in range(self._surr_nb_iter) :
            X_surr_ampli = {}
            for col in X_surr.keys() :
                Xi_surr = X_surr[col]
                
                ''' 2 - Filtering '''
                Xi_surr_fft = np.fft.rfft(Xi_surr)
                Xi_surr_ampli = np.abs(Xi_surr_fft)
                Xi_surr_phase=0
                if Xi_surr_ampli!=0:
                    Xi_surr_phase = Xi_surr_fft / Xi_surr_ampli
                
                # Save surrogate amplitude 
                X_surr_ampli.update({col : Xi_surr_ampli})
                
                # inverse fft with real amplitude
                s = np.fft.irfft(X_ampli[col] * Xi_surr_phase) 
                
                ''' 3 - Rescaling '''
                ranks = s.argsort().argsort() # get sorted indexes
                for j in range(Xi_surr.shape[0]):
                    Xi_surr[j] = X_sorted[col][ranks[j]] # replace smallest Xi_surr by smallets Xi etc...
                X_surr.update({col : Xi_surr})
                
            ''' 4 - Save surrogates eigen values '''
            df_X_surr = pd.DataFrame(X_surr)
            R = np.dot((df_X_surr.values).T, df_X_surr.values) / float(X.index.size) # Correlation matrix
            eig_values_surr, eig_vectors_surr = np.linalg.eig(R) # Eigenvalues decomposition
            eig_values_surr = np.sort(eig_values_surr) # sort by increasing order
            X_surr_eig.update({(p+1) : eig_values_surr})
            
            # Save surrogate amplitude at each iteration to see if there is a convergence to real amplitude
            X_surr_tot_ampli.update({p : X_surr_ampli})
 
        # Compute average surrogate eigen values
        X_surr_average_eig = np.mean(X_surr_eig.values(), axis=0)
        
        return df_X_surr, X_surr_average_eig
  
  
    def compute(self, signals):
        """
         Computes SSI for multiple monovariate signals (organized as a list).
         If input signals are multivariates, only the first column of the signal is considered
          
        :param signals:
            list of signals, one per person. 
        :type signals: list[pd.DataFrame]

        :returns: dict
            -- Synchronization indexes : S-Estimator (SSI), Genuine Synchronization Index (GSI) and Random Synchronization Index (RSI)
        """
        
        ' Raise error if parameters are not in the correct type '
        try :
            for i in range(len(signals)) :
                if not(isinstance(signals[i], pd.DataFrame)): raise TypeError("Requires signal " + str(i+1) + " to be a pd.DataFrame.")
        except TypeError as err_msg:
            raise TypeError(err_msg)
            return
        
        ' Raise error if DataFrames have not the same size or same indexes '
        try :
            for i in range(0,len(signals)):
                if len(signals[0]) != len(signals[i]) : raise ValueError("All the signals must have the same size. Signal " + str(i+1) + " does not have the same size as first signal.")
                if signals[0].index.tolist() != signals[i].index.tolist() : raise ValueError("All the signals must have the same time indexes. Signal " + str(i+1) + " does not have the same time index as first signal.")
        except ValueError as err_msg:
            raise ValueError(err_msg)
            return

        'Formate signals in one DataFrame for computing'
        # If input signals are multivariates, only the first column is considered
        x = pd.DataFrame()
        for i in range(0,len(signals)): 
            if x.empty :
                x = pd.DataFrame(signals[i].iloc[:,0], signals[i].index)
                x.columns = [signals[i].columns[0]]
            else :
                x[signals[i].columns[0]] = signals[i].iloc[:,0]
        
        ''' Ignore last value if len(x) is odd (avoiding trouble with fft<=>ifft)'''
        if (x.shape[0]%2 != 0):
            x = x.iloc[0:x.shape[0]-1,:]
        
        ''' Standardize '''
        X = Standardize.Standardize(x)
        
        ''' Correlation matrix  '''
        C = np.dot((X.values).T, X.values) / float(x.index.size) # on original signal
        
        ''' Eigenvalues decomposition '''
        eig_values, eig_vectors = np.linalg.eig(C) # on original signal
        eig_values = np.sort(eig_values) # sort by increasing order
        
        ''' Surrogate signal '''
        df_X_surr, X_surr_average_eig = self.refined_AAFT_surrogate(X)
        
        ''' Get Synchronization Indexes '''
        lambda_1 = []
        lambda_2 = []
        lambda_3 = []
        for i in range(X_surr_average_eig.size):
            lambda_1.append( eig_values[i] / sum(eig_values) )
            
            lambda_2.append( (eig_values[i]/X_surr_average_eig[i]) / sum(eig_values/X_surr_average_eig) )
        
            lambda_3.append( X_surr_average_eig[i] / sum(X_surr_average_eig) )
            
        SI = dict()
        SI['SSI'] = self.getSynchronizationIndex(lambda_1)
        SI['GSI'] = self.getSynchronizationIndex(lambda_2)
        SI['RSI'] = self.getSynchronizationIndex(lambda_3)
        SI['surrogate_signal'] = df_X_surr
        
        if self._plot:
            self.plot_result(SI)

        return SI

    @staticmethod
    def getArguments():
        return S_Estimator.argsList.getMethodArgs()

    @staticmethod
    def getArgumentsAsDictionary():
        return S_Estimator.argsList.getArgumentsAsDictionary()
        
        