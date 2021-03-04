# -*- coding: utf-8 -*-

import os
import ast
import sys
import numpy as np
import pandas as pd
import time

import json 

from textwrap import dedent

import dash
import dash_html_components as html
import dash_core_components as dcc

import plotly.graph_objs as go

import dash_daq as daq
from dash.dependencies import Input, Output, State

# STEPS simulations within here
import run_sim as sim

DEMO = False

# lock for modifying information about spectrometer
# spec_lock = Lock()
# lock for communicating with spectrometer
# comm_lock = Lock()

# # demo or actual
if ("DASH_PATH_ROUTING" in os.environ) or (
    len(sys.argv) == 2 and sys.argv[1] == "demo"
):
    # spec = doos.DemoSpectrometer(spec_lock, comm_lock)
    DEMO = True
else:
    0
    # spec = doos.PhysicalSpectrometer(spec_lock, comm_lock)

# spec.assign_spec()

app = dash.Dash(__name__)
server = app.server

colors = {
    "background": "#ffffff",
    "primary": "#efefef",
    "secondary": "#efefef",
    "tertiary": "#dfdfdf",
    "grid-colour": "#cccccc",
    "accent": "#2222ff",
}

base_intro = """Summary description here
"""

extend_intro = """ Detailed use description here  """

page_layout = [
    html.Div(
        [
            html.Div(
                [
                    # Hidden div inside the app that stores the simulation value
                    html.Div(
                        id='simulation', style={'display': 'none'}
                        ),
                    html.Img(
                        src=app.get_asset_url("dash-daq-logo.png"), className="logo"
                    ),
                    html.Div(
                        id="controls",
                        title="Input simulator parameters.",
                        children=[],
                    ),
                    html.Div(
                        [
                            html.Div([html.Label("Autoscale Plot")]),
                            html.Div(
                                [
                                    daq.BooleanSwitch(
                                        id="plot-switch", color="#565656", on=False
                                    )
                                ],
                                title="Controls whether to plot",
                            ),
                        ],
                        className="control plot",
                    ),
                    html.Div(
                        [
                            html.Div([html.Label("Diffusion")]),
                            html.Div(
                                [
                                    daq.PrecisionInput(
                                      id='diffusion',
                                      precision=2,
                                      value=1e-12
                                    )  
                                ],
                                title="Adjust NP diffusion",
                            ),
                        ],
                        className="diffusion input",
                    ),
                    html.Div(
                        [
                            html.Div([html.Label("binding")]),
                            html.Div(
                                [
                                    daq.PrecisionInput(
                                      id='binding',
                                      precision=2,
                                      value=1e4
                                    )  
                                ],
                                title="Adjust NP binding strength",
                            ),
                        ],
                        className="binding input",
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Submit",
                                id="submit-button",
                                n_clicks=0,
                                n_clicks_timestamp=0,
                            )
                        ],
                        title="Click to send all of the parameter values to the simulator.",
                        className="submit",
                    ),
                    html.Div(
                        [
                            html.Div([html.Label("cell-slider")]),
                            html.Div(
                                [
                                    dcc.Slider(
                                    id='cell-slider',
                                    min=0,
                                    max=22,
                                    value=2,
                                    step=1
                                )
                                ],
                                title="Choose cell",
                            ),
                        ],
                        className="cell number",
                    ),
                    html.Div(
                        [
                            html.Div([html.Label("window-slider")]),
                            html.Div(
                                [
                                    dcc.Slider(
                                    id='window-slider',
                                    min=0,
                                    max=10000,
                                    value=1000,
                                    step=100
                                )
                                ],
                                title="Moving Average window size",
                            ),
                        ],
                        className="window size",
                    ),                    
                    html.Div(
                        id="submit-status",
                        title="Contains information about the success or failure of your \
                commands.",
                        children=["print?"],
                    ),
                ],
                className="one-third column left__section",
            ),
            html.Div(
                [
                    html.Div(
                        id="graph-container",
                        children=[
                            html.Div(
                                children=[
                                    html.H6(
                                        id="graph-title", children=["EVONANO TEST"]
                                    ),
                                    html.Div(
                                        id="run-sim-button-container",
                                        title="Run the simulator.",
                                        children=[
                                            daq.PowerButton(
                                                id="power-button",
                                                size=50,
                                                color=colors["accent"],
                                                on=True,
                                            )
                                        ],
                                    ),
                                    dcc.Markdown(
                                        dedent(base_intro), id="graph-title-intro"
                                    ),
                                    html.Button(
                                        "Learn More", id="learn-more-btn", n_clicks=0
                                    ),
                                    dcc.Graph(
                                        id="spec-readings",
                                        animate=False,
                                        figure=dict(
                                            data=[],
                                            layout=dict(
                                                height=600,
                                                paper_bgcolor="rgba(0,0,0,0)",
                                                plot_bgcolor="rgba(0,0,0,0)",
                                            ),
                                        ),
                                    ),
                                    dcc.Interval(
                                        id="spec-reading-interval",
                                        interval=2
                                        * 1000,  # change from 1 sec to 2 seconds
                                        n_intervals=0,
                                    ),
                                ]
                            )
                        ],
                    )
                ],
                className="two-thirds column right__section",
            ),
        ]
    )
]

app.layout = html.Div(id="main", children=page_layout)


############################
# Callbacks
############################


@app.callback(
    [Output("graph-title-intro", "children"), Output("learn-more-btn", "children")],
    [Input("learn-more-btn", "n_clicks")],
)
def display_info_box(btn_click):
    if (btn_click % 2) == 1:
        return dedent(extend_intro), "Close"
    else:
        return dedent(base_intro), "Learn More"


# disable/enable the update button depending on whether options have changed
@app.callback(
    Output("submit-button", "style"),
    [Input("submit-button", "n_clicks_timestamp")],
)
def update_button_disable_enable(*args):
    now = time.time() * 1000
    disabled = {
        "color": colors["accent"],
        "backgroundColor": colors["background"],
        "cursor": "not-allowed",
    }
    enabled = {
        "color": colors["background"],
        "backgroundColor": colors["accent"],
        "cursor": "pointer",
    }

    # if the button was recently clicked (less than a second ago), then
    # it's safe to say that the callback was triggered by the button; so
    # we have to "disable" it
    if int(now) - int(args[-1]) < 500 and int(args[-1]) > 0:
        return disabled
    else:
        return enabled


# spec model
# @app.callback(Output("graph-title", "children"), [Input("power-button", "on")])
# def update_spec_model(_):
#     return "model" 

# send user-selected options to simulator
@app.callback(
    [Output("submit-status", "children"), Output("simulation","children")],
    [Input("submit-button", "n_clicks"),  
    Input("diffusion", "value"), Input("binding", "value")
    ],
    # state=[State(ctrl.component_attr["id"], ctrl.val_string()) for ctrl in controls]
    # + [State("power-button", "on")],
)
def update_simulation(n_clicks, *args):
    # don't return anything if the device is off
    if not args[-1]:
        return [
            'No arguments'
        ]


    D = args[0]
    ka = args[1]

    VCParam = {'P0':{"k_a" :ka, "D" :D}}
                 # ,'P1':{"k_a" :0, "D" :inputParams[4],"NP0" :NP1t}}

    CCParam = {'P0':{"k_a" : ka}}
                 # ,'P1':{"k_a" :inputParams[5],"k_d" :1e-4,"D" :inputParams[4], "NP_max" : 10000000}}
    # CSCParam = {'P0':{"k_a" :inputParams[1],"k_d" :1e-4,"D" :inputParams[0], "NP_max" : 10000000}}
    #              ,'P1':{"k_a" :inputParams[5],"k_d" :1e-4,"D" :inputParams[4], "NP_max" : NP1c}}
    # HCParam = {'P0':{"k_a" : 0,"k_d" :1e-4,"D" :inputParams[0]}
    #              ,'P1':{"k_a" :0,"k_d" :1e-4,"D" :inputParams[4]}}

    print(stepsParams)

    stepsParams = {"cell":{"VC": VCParam, "CC": CCParam}}
    # dictionary of commands; component id and associated value
    # commands = {controls[i].component_attr["id"]: args[i] for i in range(len(controls))}

    # failed, succeeded = spec.send_control_values(commands)
    if n_clicks > 0:
        s,c =  sim.load_settings()

        data = (s,c,1)
        sim_output,f,m = sim.run_sim(data)

        shared_data = json.dumps(sim_output.tolist())

    else:
        m = ['No simulations run']
        sim_output = []
        shared_data = json.dumps([])

    # if len(failed) > 0:
    #     summary.append(
    #         "The following parameters were not \
    #     successfully updated: "
    #     )
    #     summary.append(html.Br())
    #     summary.append(html.Br())

    #     for f in failed:
    #         # get the name as opposed to the id of each control
    #         # for readability
    #         [ctrlName] = [c.ctrl_name for c in controls if c.component_attr["id"] == f]
    #         summary.append(ctrlName.upper() + ": " + failed[f])
    #         summary.append(html.Br())

    #     summary.append(html.Br())
    #     summary.append(html.Hr())
    #     summary.append(html.Br())
    #     summary.append(html.Br())

    # if len(succeeded) > 0:
    #     summary.append("The following parameters were successfully updated: ")
    #     summary.append(html.Br())
    #     summary.append(html.Br())

    #     for s in succeeded:
    #         [ctrlName] = [c.ctrl_name for c in controls if c.component_attr["id"] == s]
    #         summary.append(ctrlName.upper() + ": " + succeeded[s])
    #         summary.append(html.Br())

    return html.Div(m), shared_data


# update the plot
@app.callback(
    Output("spec-readings", "figure"),
    state=[State("power-button", "on"), State("plot-switch", "on")],
    inputs=[Input("simulation", "children"),Input("cell-slider", "value"), Input("window-slider", "value")],
)
def update_plot(sim_out, NCell, window_len,power_on, plot_on):


    if sim_out is not None:
        sim_out = ast.literal_eval(sim_out)
        N = len(sim_out)
        if N > 0:
            sim_out = np.array(sim_out, dtype=float)
    else:
        N = 0

    random_x = np.linspace(0, 48, N)

    print(power_on,plot_on,NCell)
    if plot_on:
        # Create traces
        traces = [go.Scatter(
            x = random_x,
            y = np.convolve(sim_out[:,NCell,0], np.ones(window_len)/window_len, mode='valid'),
            mode = 'markers',
            name = 'NP',
        ),
        go.Scatter(
            x = random_x,
            y = np.convolve(sim_out[:,NCell,2], np.ones(window_len)/window_len, mode='valid'),
            mode = 'markers',
            name = 'NPR',
        ), 
        go.Scatter(
            x = random_x,
            y = np.convolve(sim_out[:,NCell,3], np.ones(window_len)/window_len, mode='valid'),
            mode = 'markers',
            name = 'NPi',
        )]

        layout = go.Layout(
            height=600,
            font={"family": "Helvetica Neue, sans-serif", "size": 12},
            margin=dict(l=40, r=40, t=40, b=40, pad=10),
            titlefont={
                "family": "Helvetica, sans-serif",
                "color": colors["primary"],
                "size": 26,
            },
            # xaxis=random_x,
            # yaxis=np.convolve(sim_out[:,NCell,0], np.ones(window_len)/window_len, mode='valid'),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
    else:
        traces = []
        layout = go.Layout(
            height=600,
            font={"family": "Helvetica Neue, sans-serif", "size": 12},
            margin=dict(l=40, r=40, t=40, b=40, pad=10),
            titlefont={
                "family": "Helvetica, sans-serif",
                "color": colors["primary"],
                "size": 26,
            },
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

    return {"data": traces, "layout": layout}


if __name__ == "__main__":
    app.run_server(debug=True)
