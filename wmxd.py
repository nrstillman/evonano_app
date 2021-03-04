
import steps.model as smodel
import steps.geom as swm
import steps.rng as srng
import steps.solver as ssolver

import numpy as np
from random import randint
import copy 

import matplotlib.pyplot as plt

def model(tissue):
    """ initialises model using tissue array """

    mdl = smodel.Model()
    unique_p = []
    for cell in tissue:
        [unique_p.append(p) for p in cell.prtcl_names if p not in unique_p]
    
    NP = []
    NPi = []
    NPR = []
    # Create particles and corresponding species
    for p in unique_p:
        # Free NPs
        NP.append(smodel.Spec('N{}'.format(p), mdl))
        # internalised NPs
        NPi.append(smodel.Spec('N{}i'.format(p), mdl))
        # complexes state: NPs bound to a cell receptor
        # NPR.append(smodel.Spec('N{}R'.format(p), mdl))
        
        # receptor state: 'naive' state (no bound NPs)
    R = smodel.Spec('R', mdl)
    NPR = smodel.Spec('NPR', mdl)
    d = {}
    rxn_ = {}
    dfsn_ = {} 
    # Lpop where cell and particle properties are connected to reactions   
    for n,cell in enumerate(tissue):    
        for p_idx, p in enumerate(unique_p):
            tag = str(n) + p
            prtcl = getattr(cell, p)
            d["surfsys{}".format(tag)] = smodel.Surfsys("surfsys{}".format(tag), mdl)
            d["volsys{}".format(tag)] = smodel.Volsys("volsys{}".format(tag), mdl)
            k_diff = prtcl['D']/(float(cell.S)*float(cell.S))

            dfsn_["frwd_{}".format(tag)] = smodel.SReac("frwd_{}".format(tag), d["surfsys{}".format(tag)], 
                ilhs=[NP[p_idx]], orhs=[NP[p_idx]], kcst=k_diff)
            dfsn_["bkwd_{}".format(tag)] = smodel.SReac("bkwd_{}".format(tag), d["surfsys{}".format(tag)], 
                olhs=[NP[p_idx]], irhs=[NP[p_idx]], kcst=k_diff)

             # binding reactions:
            if 'k_a' in prtcl:
                k_bind = prtcl['k_a']
                k_unbind = prtcl['k_d']
                k_intern = prtcl['k_i']
                rxn_["bind_{}".format(tag)] = smodel.Reac("bind_{}".format(tag), d["volsys{}".format(tag)], 
                    lhs=[NP[p_idx], R], rhs=[NPR], kcst=k_bind)
                rxn_["unbind_{}".format(tag)] = smodel.Reac("unbind_{}".format(tag), d["volsys{}".format(tag)], 
                    lhs=[NPR], rhs=[NP[p_idx], R], kcst=k_unbind)
                rxn_["intern_{}".format(tag)] = smodel.Reac("intern_{}".format(tag), d["volsys{}".format(tag)], 
                    lhs=[NPR], rhs=[NPi[p_idx], R], kcst=k_intern)

            # Diffusion 
            dfsn1 = smodel.Diff('dfsn1', d["volsys{}".format(tag)], NP[p_idx], dcst = k_diff)    
            dfsn2 = smodel.Diff('dfsn2', d["volsys{}".format(tag)], NPR, dcst =k_diff)
            dfsn3 = smodel.Diff('dfsn3', d["volsys{}".format(tag)], R, dcst = k_diff)
            dfsn4 = smodel.Diff('dfsn4', d["volsys{}".format(tag)], NPi[p_idx], dcst = k_diff)

    return mdl

def geom(tissue, sim_opt):
    """ generate the well-mixed champber containing cells from tissue array """
    geom = swm.Geom()
    # Create the vessel compartment
    c_ = {}
    m_ = {}
    for p in tissue[0].prtcl_names:    
        tag= '0'+ p
        c_["cell_{}".format(tag)] = swm.Comp("cell_{}".format(tag), geom, vol=float(tissue[0].S)**3)
        c_["cell_{}".format(tag)].addVolsys("volsys{}".format(tag))

    for n,cell in enumerate(tissue[1:]): 
        n +=1
        for p in cell.prtcl_names:
            S = float(cell.S)
            tag = str(n) + p
            prev_tag = str(n-1) + p 
            c_["cell_{}".format(tag)] = swm.Comp("cell_{}".format(tag), geom, vol=S**3)
            c_["cell_{}".format(tag)].addVolsys("volsys{}".format(tag))
            m_["memb_{}".format(tag)] = swm.Patch("memb_{}".format(tag), geom, c_["cell_{}".format(tag)], c_["cell_{}".format(prev_tag)])
            m_["memb_{}".format(tag)].addSurfsys("surfsys{}".format(tag))
            m_["memb_{}".format(tag)].setArea(S**2)
    return geom

def solver(mdl, geom, tissue, sim_opt):
    """ run the simulation using sim_options and model and geometry (above) """
    treated_tissue = copy.deepcopy(tissue) 
    reactants = ['NP','NPi', 'NPR', 'R']
    NT = int(sim_opt['general'].NT)
    t_final = int(sim_opt['general'].t_final)
    N_VC, unique_p = 0, []
    for cell in treated_tissue:
        if cell.type == 'VC':
            N_VC +=1 
        [unique_p.append(p) for p in cell.prtcl_names if p not in unique_p]
    
    r = srng.create('mt19937', 512)
    seed = randint(1, 10000)
    r.initialize(seed)
    sim = ssolver.Wmdirect(mdl, geom, r)
    tpnt = np.linspace(0.0, t_final,NT)
    resi = np.zeros([NT, len(treated_tissue)*len(unique_p),len(reactants)])
    for n,cell in enumerate(treated_tissue):
        for p in cell.prtcl_names:
            tag = str(n) + p
            prtcl = getattr(cell, p)
            if hasattr(cell,'NR'):
                sim.setCompCount("cell_{}".format(tag), 'R', float(cell.NR))
            if 'NP0' in prtcl:                     
                if  prtcl['T'] == 1:
                    sim.setCompCount("cell_{}".format(tag), 'N{}'.format(p), prtcl['NP0'])
                else:    
                    sim.setCompCount("cell_{}".format(tag), 'N{}'.format(p), prtcl['NP0'])
                    sim.setCompClamped("cell_{}".format(tag), 'N{}'.format(p), True)

    printProgressBar(0, NT, prefix = 'Progress:', suffix = 'Complete', length = 40)                
    for t in range(NT):
        sim.run(tpnt[t])
        printProgressBar(t, NT, prefix = 'Progress:', suffix = 'Complete', length = 40)
        n = 0
        for nc,cell in enumerate(treated_tissue):
            for p_idx, p in enumerate(cell.prtcl_names):
                tag = str(nc) + p
                prtcl = getattr(cell, p)
                if hasattr(cell,'NR'):
                    resi[t, n, 0] = sim.getCompCount("cell_{}".format(tag), 'N{}'.format(p))   
                    resi[t, n, 1] = sim.getCompCount("cell_{}".format(tag), 'R')                                    
                    resi[t, n, 2] = sim.getCompCount("cell_{}".format(tag), 'NPR')                                    
                    resi[t, n, 3] = sim.getCompCount("cell_{}".format(tag), 'N{}i'.format(p))                                    
                else: 
                    resi[t, n, 0] = sim.getCompCount("cell_{}".format(tag), 'N{}'.format(p))                                    
                if 'T' in prtcl:
                    if (tpnt[t] > prtcl['T']) or (prtcl['T'] == 1):
                        sim.setCompClamped("cell_{}".format(tag), 'N{}'.format(p), False)
                if ('NP_max' in prtcl) and (resi[t, n, 3] > prtcl['NP_max']):
                    cell.type = 'dead'
                n += 1
    return treated_tissue, resi

    

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()