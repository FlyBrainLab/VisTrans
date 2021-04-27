
import os
import pathlib

import flybrainlab.query as fbl_query
import flybrainlab.circuit as circuit
import pandas as pd
import numpy as np
from tqdm import tqdm

from .retina import Retina

def load_retina(client, retina_config):
    ret = Retina(retina_config)
    db = fbl_query.NeuroArch_Mirror(client)
    species = db.add_Species('Drosophila melanogaster',
                             stage = 'adult',
                             sex = 'female',
                             synonyms = ['fruit fly',
                                         'common fruit fly',
                                         'vinegar fly'])
    data_source = db.add_DataSource(
        'VisTrans', version = '1.0', url = '',
        description = 'Created by VisTrans Library',
        species = list(species.keys())[0]
    )

    db.select_DataSource(list(data_source.keys())[0])
    ret_neuropil = db.add_Neuropil(ret.neuropil_name)

    ommatidia = {}
    for ommatidium in tqdm(ret.ommatidia):
        ct = db.add_Circuit('Ommatidium {}'.format(ommatidium.gid),
                            'Ommatidium',
                            neuropil = ret.neuropil_name)
        for neuron in ommatidium.get_all_neurons():
            uname = "{}-{}".format(neuron.name, neuron.ommatidium.gid)
            name = neuron.name
            referenceId = uname
            neurotransmitter = 'histamine'

            morphology = {'x': [ret.radius*np.sin(neuron.azim) * np.sin(neuron.elev)],
                          'y': [ret.radius*np.sin(neuron.azim) * np.cos(neuron.elev)],
                          'z': [ret.radius*np.cos(neuron.azim)],
                          'r': [ret.hex_array.get_distance_between_element()/2],
                          'parent': [-1],
                          'identifier': [1],
                          'sample': [1],
                          'type': 'swc'
                          }

            db.add_Neuron(uname,
                          name,
                          referenceId = referenceId,
                          morphology = morphology,
                          neurotransmitters = neurotransmitter,
                          circuit = list(ct.keys())[0])
    
    res = client.executeNLPquery('show all')
    c = circuit.ExecutableCircuit(client, res, 'retina', '1.0')
    c.initialize_diagram_config(no_send = True)
    
    for rid, v in res.neurons.items():
        neuron = ret.get_ommatidium(
            int(v['uname'].split('-')[1])).get_neuron(v['name'])[0]
        direction = neuron.direction
        params = {'name': 'PhotoreceptorModel',
                  'elev_3d': float(neuron.elev),
                  'azim_3d': float(neuron.azim),
                  'optic_axis_elev': float(direction[0]),
                  'optic_axis_azim': float(direction[1]),
                  'acceptance_angle': ret.acceptance_angle,
                  'num_microvilli': retina_config.num_microvilli}
        states = {'V': -82.}
        c.update_model(v['uname'], params = params, states = states, no_send = True)
    
    folder = pathlib.Path(__file__).parent.absolute()
    ommatidia_diagram = os.path.join(folder, 'img/ommatidium.svg')
    retina_diagram = os.path.join(folder, 'img/retina.svg')
    ommatidia_submodule = os.path.join(folder, 'submodules/ommatidium.js')
    retina_submodule = os.path.join(folder, 'submodules/retina.js')
    c.load_diagram(ommatidia_diagram, name = 'ommatidium', display = False)
    c.load_submodule(ommatidia_submodule, name = 'ommatidium', exec = False)
    c.load_diagram(retina_diagram, primary = True, name = 'retina', display = False)
    c.load_submodule(retina_submodule, primary = True, name = 'retina', exec = False)
    c.display_diagram()
    c.flush_model()

