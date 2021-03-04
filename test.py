import plotly
import plotly.graph_objs as go

import numpy as np
import pandas as pd
# Create sim data using run_sim
import run_sim as sim


N = 10000
random_x = np.linspace(0, 1, N)

D = 1e-12
ka = 1e5
kd = 1e-4
ki = 1e-5
NP0 = 10
NPmax = 100
T = 48*3600

VCParam = {'P0':{"k_a" :ka, "D" :D,"NP0" :NP0, "T" : T}}
             # ,'P1':{"k_a" :0, "D" :inputParams[4],"NP0" :NP1t}}

CCParam = {'P0':{"k_a" : ka,"k_d" : kd,"D" : D, "NP_max" : NPmax}}
             # ,'P1':{"k_a" :inputParams[5],"k_d" :1e-4,"D" :inputParams[4], "NP_max" : 10000000}}
# CSCParam = {'P0':{"k_a" :inputParams[1],"k_d" :1e-4,"D" :inputParams[0], "NP_max" : 10000000}}
#              ,'P1':{"k_a" :inputParams[5],"k_d" :1e-4,"D" :inputParams[4], "NP_max" : NP1c}}
# HCParam = {'P0':{"k_a" : 0,"k_d" :1e-4,"D" :inputParams[0]}
#              ,'P1':{"k_a" :0,"k_d" :1e-4,"D" :inputParams[4]}}

stepsParams = {"cell":{"VC": VCParam, "CC": CCParam}}

s,c =  sim.load_settings(stepsParams)

data = (s,c,1)
r,f,m = sim.run_sim(data)



lable_one = [f'cell {i}' for i in range(21)] 
lable_two = ['NP','NPi', 'NPR', 'R']
cols = pd.MultiIndex.from_product([lable_one, lable_two])

df = pd.DataFrame(r.T.reshape(len(lable_one), len(lable_two), N), columns=cols)
print(df)

# window_len = 1000
# # Create traces
# trace0 = go.Scatter(
#     x = random_x,
#     y = np.convolve(r[:,1,0], np.ones(window_len)/window_len, mode='valid'),
#     mode = 'markers',
#     name = 'markers'
# )

# trace1 = go.Scatter(
#     x = random_x,
#     y =  np.convolve(r[:,2,0], np.ones(window_len)/window_len, mode='valid'),
#     mode = 'lines+markers',
#     name = 'lines+markers'
# )

# trace2 = go.Scatter(
#     x = random_x,
#     y =  np.convolve(r[:,3,0], np.ones(window_len)/window_len, mode='valid'),
#     mode = 'lines',
#     name = 'lines'
# )

# data = [trace0, trace1, trace2]
# plotly.offline.plot(data, filename='testing_output.html')
