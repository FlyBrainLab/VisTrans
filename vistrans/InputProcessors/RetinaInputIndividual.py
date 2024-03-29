#!/usr/bin/env python

from collections import OrderedDict

import numpy as np
from neurokernel.LPU.InputProcessors.BaseInputProcessor import BaseInputProcessor

from . import classmapper as cls_map
from ..config import Input




class RetinaInputIndividual(BaseInputProcessor):

    def __init__(self, input_config, photoreceptors, dt, radius,
                 input_file = None, input_interval = 1):
        """
        config: see retina configuration template

        photoreceptors: dictionary from
                            networkx.MultiDigraph.nodes(data=True),
                            i.e., the key is the rid
                            and the value is a dictionary containing parameters
                            of the photoreceptor
        """
        if isinstance(input_config, Input):
            self.config = input_config
        elif isinstance(input_config, dict):
            self.config = Input.from_dict(input_config)
        else:
            raise TypeError('input_config is either a Input dataclass or a dict generated by Input.to)_dict()')

        self.screen_type = self.config.screentype
        self.filtermethod = 'gpu'
        screen_cls = cls_map.get_screen_cls(self.screen_type.name)#getattr(scr, self.screen_type.name)
        self.screen = screen_cls(self.config, dt)
        self.pr_list = OrderedDict(photoreceptors)
        self.retina_radius = radius
        self.num_photoreceptors = len(photoreceptors)
        
        uids = list(self.pr_list.keys())

        super(RetinaInputIndividual, self).__init__(
                [('photon', uids)], mode=0,
                input_file = input_file, input_interval = input_interval)

    def pre_run(self):
        self.generate_receptive_fields()

    def generate_receptive_fields(self):
        pr_list = self.pr_list
        screen = self.screen
        screen_type = self.screen_type
        filtermethod = self.filtermethod

        mapdr_cls = cls_map.get_mapdr_cls(screen_type.name)
        projection_map = mapdr_cls(self.retina_radius, screen.radius)

        pos_elev = np.array([float(a['params']['elev_3d']) for a in pr_list.values()])
        pos_azim = np.array([float(a['params']['azim_3d']) for a in pr_list.values()])
        dir_elev = np.array([float(a['params']['optic_axis_elev']) for a in pr_list.values()])
        dir_azim = np.array([float(a['params']['optic_axis_azim']) for a in pr_list.values()])

        rf_params = projection_map.map(pos_elev, pos_azim, dir_elev, dir_azim)
        if np.isnan(np.sum(rf_params)):
            print('Warning, Nan entry in array of receptive field centers')

        if filtermethod == 'gpu':
            vrf_cls = cls_map.get_vrf_cls(screen_type.name)
        else:
            vrf_cls = cls_map.get_vrf_no_gpu_cls(screen_type.name)
        rfs = vrf_cls(screen.grid)
        rfs.load_parameters(refa=rf_params[0], refb=rf_params[1],
                            acceptance_angle = float(list(pr_list.values())[0]['params']['acceptance_angle']),
                            radius=screen.radius)

        rfs.generate_filters()
        self.rfs = rfs

    def update_input(self):
        im = self.screen.get_screen_intensity_steps(1)
        inputs = self.rfs.filter_image_use(im).get().reshape((1, -1))
        self.variables['photon']['input'][:] = inputs

    def is_input_available(self):
        return True
