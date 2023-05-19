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

import numpy as np
import pandas as pd

def ConvertContinueToBinary(signal, threshold = 0, maximize = True):
    """
    It converts a continue signal (in pandas DataFrame format) into a binany signal according to a rule defined by a threshold and a type of filter. 
    
    :param signal:
        input signal
    :type signal: pd.DataFrame
    
    :param threshold:
        value of the threshold. Default: 0
    :type threshold: float
    
    :param maximize:
        is True if the conversion is done for values higher than the threshold. Default: True
    :type maximize: bool

    :returns: pd.DataFrame 
            -- binarized signal
    """
    
    bool_data = signal.copy()
    
    if(maximize == True):
        for col in range(bool_data.columns.size) :
            for line in range(bool_data.index.size) :
                if bool_data.iat[line, col] > threshold :
                    bool_data.iat[line, col] = 1
                else :
                    bool_data.iat[line, col]  = 0
    else :
        for col in range(bool_data.columns.size) :
            for line in range(bool_data.index.size) :
                if bool_data.iat[line, col] > threshold :
                    bool_data.iat[line, col] = 0
                else :
                    bool_data.iat[line, col]  = 1
    
    return bool_data
