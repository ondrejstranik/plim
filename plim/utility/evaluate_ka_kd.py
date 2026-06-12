#%% script to evaluate ka, kd

import numpy as np 
import matplotlib.pylab as plt

c = np.array([10,20, 50, 200, 1000])
tau = np.array([318,409,103,30,9.2])
amp = np.array([72.5,71.6, 92,107, 108])

p1 = np.poly1d(np.polyfit(c, 1/tau,1))

p1


fig, ax = plt.subplots()

ax.plot(c,1/tau, 'r*-')

ax.plot(c,p1(c), 'b+-')


plt.show()

# %%
