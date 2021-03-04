#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import time
import pickle, sys
import os.path, csv
import json
import random

import setup

import argparse
from itertools import repeat
from multiprocessing import Pool, TimeoutError, cpu_count

def save_output(resi, strings):
    sim_str, time_take, filename = strings[0], strings[1], strings[2]
    file_name = 'result_%s_time_%.2g' % (sim_str, time_taken)

    with open('output/'+ sim_str+'/'+ file_name + '.pickle', 'wb') as f:
        pickle.dump(resi, f)
    return 0

def load_settings(*args):

    path = "data/config.xml"
    sim_opt = setup.get_sim_data(path)
    if len(args) > 0: 
        data = args[0]
        # print("Input data is %s" % data)
        setup.update_config(data, path)
        
    cell_data = setup.get_cell_data(path)
    return sim_opt, cell_data

def run_sim(input_data):
    sim_opt, cell_data, fitness_constraint = input_data
    if sim_opt == 0:
        return 0
    
    path = "data/config.xml"
    # prepare tissue data

    tissue = np.array([0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])
    section = 0
    tissue_map  = {0: 'VC', 1 : 'CC'}

    # prepare cell data
    data = cell_data

    for n in range(len(tissue_map)):
        data[n]['N_cell'] = sum((tissue == n)*1)
    
    cells = setup.make_cells(data)

    tissue = setup.make_tissue(tissue, cells, tissue_map)

    # prepare simulation
    scenario = __import__(sim_opt['opt'].scenario)
    mdl = scenario.model(tissue)
    geom = scenario.geom(tissue, sim_opt)

    # run simulation
    start = time.time()
    treated_tissue, resi = scenario.solver(mdl, geom, tissue, sim_opt)
    end = time.time()
    time_taken = end - start
    
    fitness, message = setup.calc_fitness(tissue,treated_tissue, fitness_constraint)
    message = f'\r{message}\nTissue section {section} w/ fitness {fitness:g}'
    return resi, fitness, message

def main(data):
    
    try:
        stop
        sim_opt = load_settings(data)
        N_runs = int(sim_opt['opt'].N_runs)
        sim_opts = repeat(sim_opt, N_runs)
        if sim_opt['opt'].multi_core == '1':
            with Pool(N_runs) as p:
                f = p.map(run_sim, sim_opts)
        else:
            f = run_sim(sim_opt)
    
    except OSError as err:
        print(f"Main function called: {err}\n Currently set-up for parallel only.")

    return np.mean(f)

def multimain(sim_opt):
    
    sim_opt = load_settings(data)
    f = run_sim(sim_opt)
    return f

if __name__ == "__main__":
    tic = time.perf_counter()
    if len(sys.argv) == 3:

        data=json.loads(sys.argv[2])
        sim_opt = load_settings(data)

    else:
        fitness_constraint = 0
        sim_opt, cell_data = load_settings()
        input_opts = (sim_opt,cell_data,fitness_constraint)

    if sim_opt['opt'].multi_core == '1':
        N_runs = int(sim_opt['opt'].N_runs)
        sim_opts = repeat(input_opts, N_runs)

        with Pool(N_runs) as p:
            f = p.map(run_sim, sim_opts)
    else:    
        f = run_sim(input_opts)
