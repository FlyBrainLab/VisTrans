
import numpy as np

from . import config as config
from .geometry.opticaxis import opticaxisFactory, RuleHexArrayMap, OpticAxisRule
from .screen.map.mapimpl import AlbersProjectionMap
from .geometry import hexagon as hx

class Ommatidium(object):

    def __init__(self, parent, element):
        '''
            element: ArrayElement object
        '''
        elev, azim = element.dima, element.dimb
        self._elev = elev
        self._azim = azim
        self.element = element
        self.parent = parent

        # maybe simple dict is sufficient
        self._neurons = {}
        self._neuron_count = {}
        self._next_neuron = {}

    @property
    def uid(self):
        return 'ommatidium_{}'.format(self.element.gid)

    @property
    def optic_axis(self):
        return self._optic_axis

    @optic_axis.setter
    def optic_axis(self, optic_axis):
        self._optic_axis = optic_axis

    @property
    def sphere_pos(self):
        return self._elev, self._azim

    @property
    def is_dummy(self):
        return self.element.is_dummy

    @property
    def gid(self):
        return self.element.gid

    @property
    def num_neurons(self):
        return len(self.get_all_neurons())

    @property
    def equator_type(self):
        return self.element.equator_type

    def add_neurons(self, neuron_list):
        for neuron in neuron_list:
            self._add_photoreceptor(neuron)

    def add_neuron(self, neuron):
        neuron.xpos = self.element.xpos
        neuron.ypos = self.element.ypos
        neuron.elev, neuron.azim = self.sphere_pos
        if neuron.name not in self._neurons:
            neuron.sequence_number = 0
            self._neurons[neuron.name] = [neuron]
            self._neuron_count[neuron.name] = 1
            self._next_neuron[neuron.name] = 0
        else:
            neuron.sequence_number = self._neuron_count[neuron.name]
            self._neurons[neuron.name].append(neuron)
            self._neuron_count[neuron.name] += 1

    def _add_photoreceptor(self, name):
        nid = self.optic_axis.name_to_ind(name)
        neighbordr = self.optic_axis.neighbor_that_send_photor_to(nid)
        neighborid = self.get_neighborid(neighbordr)

        # position on sphere coincides with the
        # surface normal and the desired direction
        if neighborid is None:
            direction = self.sphere_pos
        else:
            direction = self.parent.get_ommatidium(neighborid).sphere_pos
        photor = Photoreceptor(self, name, direction)
        self.add_neuron(photor)

    def get_neighborid(self, neighbor_dr):
        return self.element.get_neighborid(neighbor_dr)

    def get_neuron(self, name, number=None):
        all_neurons_with_the_name = self._neurons.get(name, [])
        if number is None:
            return all_neurons_with_the_name
        elif type(number) in [list, tuple]:
            return [all_neurons_with_the_name[num] for num in number]
        else:
            return all_neurons_with_the_name[int(number)]

    def get_neuron_round_robin(self, name):
        try:
            num = self._next_neuron[name]
            neuron = self._neurons[name][num]
            if num + 1 == self._neuron_count[name]:
                self._next_neuron[name] = 0
            else:
                self._next_neuron[name] = num + 1
            return neuron
        except KeyError:
            return None

    def get_all_neurons(self):
        return [neuron for neurons in self._neurons.values()
                for neuron in neurons if not neuron.is_dummy]

    def is_neighbor_dummy(self, neighbor_num):
        return self.element.get_neighbor([neighbor_num]).is_dummy


class Photoreceptor(object):

    def __init__(self, ommatidium, name, direction):
        '''
            ommatidium: ommatidium object
            direction: tuple of 2 coordinates (elevation, azimuth) or None
                       direction of photoreceptor optical axis
        '''
        self.direction = direction
        self.ommatidium = ommatidium
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, val):
        self._uid = val
    
    @property
    def num(self):
        return self._num

    def add_num(self, num):
        self._num = num

    @property
    def elev(self):
        return self._elev

    @elev.setter
    def elev(self, val):
        self._elev = val

    @property
    def azim(self):
        return self._azim

    @azim.setter
    def azim(self, val):
        self._azim = val

    @property
    def xpos(self):
        return self._xpos

    @property
    def ypos(self):
        return self._ypos

    @xpos.setter
    def xpos(self, val):
        self._xpos = val

    @ypos.setter
    def ypos(self, val):
        self._ypos = val

    @property
    def sphere_pos(self):
        return self.ommatidium.sphere_pos

    def set_parent(self, parent):
        if self.is_dummy:
            self.parent = parent

    def get_projection_gid(self):
        optic_axis = self.ommatidium.optic_axis
        nid = optic_axis.name_to_ind(self.name)
        neighbordr = optic_axis.neighbor_that_send_photor_to(nid)
        return self.ommatidium.get_neighborid(neighbordr)

    @property
    def is_dummy(self):
        return False

class Retina(object):

    def __init__(self, retina_config):

        transform = AlbersProjectionMap(retina_config.radius, 
                                        retina_config.eulerangles).invmap
        self.hex_array = hx.HexagonArray(num_rings = retina_config.rings,
                                radius = retina_config.radius,
                                transform = transform,
                                numbering_order = retina_config.numbering_order)

        self.optic_axis_top = opticaxisFactory('SuperpositionTop')()
        self.optic_axis_bottom = opticaxisFactory('SuperpositionBottom')()
        #self.rulemap_top = RuleHexArrayMap(self.opticaxis_top, hex_array)
        #self.rulemap_bottom = RuleHexArrayMap(self.opticaxis_bottom, hex_array)


        self.neuropil_name = retina_config.neuropil_name
        self._ommatidia = [Ommatidium(self, el)
                           for el in self.hex_array.elements]
        for omma in self._ommatidia:
            gid = omma.gid
            pos = self.hex_array.get_position_for_element(gid)
            if pos[1] >= 0:  # y position
                omma.optic_axis = self.optic_axis_top
            else:
                omma.optic_axis = self.optic_axis_bottom

        # update photoreceptors
        for omma in self._ommatidia:
            omma.add_neurons(retina_config.photoreceptors)

        # in degrees
        self.interommatidial_angle = self._get_interommatidial_angle()

        # in degrees
        self.acceptance_angle = self.interommatidial_angle * retina_config.acceptance_factor

    @property
    def ommatidia(self):
        return self._ommatidia

    def _set_properties_for_ommatidia(self):
        for omma in self._ommatidia:
            gid = omma.gid
            pos = self.hex_array.get_position_for_element(gid)
            if pos[1] >= 0:  # y position
                omma.optic_axis = self.optic_axis_top
            else:
                omma.optic_axis = self.optic_axis_bottom

    def _get_interommatidial_angle(self):
        ''' Returns angle in degrees '''
        elev1, azim1 = self.ommatidia[0].sphere_pos
        try:
            elev2, azim2 = self.ommatidia[1].sphere_pos
        except IndexError:
            # when there is only one element
            # assume interommatidial angle is 90
            return 90

        x1 = np.sin(elev1) * np.cos(azim1)
        y1 = np.sin(elev1) * np.sin(azim1)
        z1 = np.cos(elev1)
        x2 = np.sin(elev2) * np.cos(azim2)
        y2 = np.sin(elev2) * np.sin(azim2)
        z2 = np.cos(elev2)
        angle = np.arccos(x1 * x2 + y1 * y2 + z1 * z2)
        return float(angle * 180 / np.pi)

    def get_all_photoreceptors(self):
        return [photor for ommatidium in self.ommatidia
                for photor in ommatidium.get_all_neurons()]

    def get_angle(self):
        return self.acceptance_angle

    def get_all_photoreceptors_dir(self):
        allphotors = self.get_all_photoreceptors()
        elevazim = np.array([photor.sphere_pos for photor in allphotors])
        dirs = np.array([photor.direction for photor in allphotors])

        return elevazim[:, 0], elevazim[:, 1], dirs[:, 0], dirs[:, 1]

    def get_ommatidia_pos(self):
        positions = np.array([omm.sphere_pos for omm in self.ommatidia])
        return positions[:, 0], positions[:, 1]

    def get_neighborid(self, oid, neighbor_dr):
        ''' Get id of neighbor of `oid` ommatidium in a
            specific direction
        '''
        return self._ommatidia[oid].get_neighborid(neighbor_dr)

    def index(self, ommid, name):
        return list(self._ommatidia[ommid].neurons.keys()).index(name)

    @property
    def radius(self):
        return self.hex_array.radius

    def get_ommatidium(self, gid):
        return self._ommatidia[gid]

    @property
    def num_neurons(self):
        return sum([n.num_neurons for n in self._ommatidia])
    
    @property
    def num_ommatidia(self):
        return self.hex_array.num_elements


def main():

    from retina.screen.map.mapimpl import AlbersProjectionMap
    import retina.geometry.hexagon as hex
    from retina.configreader import ConfigReader
    import retina.retina as ret
    import networkx as nx
    config = ConfigReader('retlam_default.cfg', '../template_spec.cfg').conf
    transform = AlbersProjectionMap(config['General']['radius'], config[
                                    'General']['eulerangles']).invmap
    hexarray = hex.HexagonArray(num_rings=14, radius=config['General'][
                                'radius'], transform=transform)
    a = ret.RetinaArray(hexarray, config)
    G = a.generate_neuroarch_gexf()
    nx.write_gexf(G, 'retina_neuroarch.gexf.gz')

if __name__ == "__main__":
    main()
