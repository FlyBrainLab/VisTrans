
import os
from abc import ABCMeta, abstractmethod, abstractproperty
import contextlib

from future.utils import with_metaclass
import numpy as np
from neurokernel.LPU.utils.simpleio import *

from .input.image2d import image2Dfactory

from .map.mapimpl import pointmapfactory
from .transform.imagetransform import ImageTransform


class Screen(with_metaclass(ABCMeta, object)):
    """ Defines the geometry of screen and generates screen images """

    # __metaclass__ = ABCMeta

    def __init__(self, input_config, dt, retina_index = 0):
        self._dtype = np.double
        self.retina_index = retina_index

        # config attributes
        self._dt = dt
        self._input_type = input_config.inputtype.name

        # grid
        self._setup_screen(input_config.inputconfig)

    @abstractproperty
    def screen_to_image_map(self):
        pass

    @abstractproperty
    def grid(self):
        """ :return: a meshgrid tuple e.g
                [[x1, x2, x3],
                 [x1, x2, x3]],
                [[y1, y1, y1],
                 [y2, y2, y2]]
        """
        pass

    def _setup_screen(self, config):
        """ setup up screen generation or retrieval

        This function setup stage of types of movies to be played
        and can let self.get_screen_intensity_step to
        generate video.

        Parameters
        ----------
        config: vistrans.config.InputConfigure
        """

        self._image2d = image2Dfactory(self._input_type)(config, self._dt,
                                                         self.retina_index)

        # find the mappings of screen points to image
        imagx, imagy = self.screen_to_image_map.map(self.grid[0],
                                                    self.grid[1])

        # given the values on points of a rectangular grid, interpolator
        # can find the values on any point of the plane by approximation
        xmax, ymax = imagx.max(), imagy.max()
        xmin, ymin = imagx.min(), imagy.min()
        self._interpolator = ImageTransform(
            self._image2d.get_grid(xmin, xmax, ymin, ymax), [imagx, imagy])

    def get_screen_intensity_steps(self, num_steps):
        """ generate or read the next num_steps of inputs """
        try:
            images = self._image2d.generate_2dimage(num_steps)
            images = images[:, ::-1, ::-1]
            # values on screen
            screens = self._interpolator.interpolate(images)

        except AttributeError:
            print('Function for file setup probably not called')
            raise

        return screens

    @abstractmethod
    def get_image2d_dim(self):
        """ screen is supposed to map values from
            (-x/2 to x/2) and (-y/2 to y/2)
            where x, y are the values returned
            from this function
        """
        pass

    @abstractmethod
    def generate_video(self, data, coordinates, rng, videofile):
        """
            data: values to be visualized
            coordinates: coordinates of values on screen
                         a tuple of arrays
            rng:         range of values
            videofile:   the file where output will be written
        """
        pass


class SphereScreen(Screen):

    def __init__(self, input_config, dt, retina_index = 0):
        config_screen = input_config.screenconfig

        # number of parallels, meridians is different than
        self._width = config_screen.parallels
        self._height = config_screen.meridians
        self._radius = config_screen.radius
        self._half = config_screen.half

        # TODO allow for classes that accept radius as input and possibly
        # extra arguments or add a manual check for inputs
        self._screen_to_image_map = pointmapfactory(
            config_screen.image_map.name)(self._radius)
        self._generate_grid()
        super(SphereScreen, self).__init__(input_config, dt, retina_index = retina_index)

    def _generate_grid(self):
        # retina should turn from its default location using
        # euler angles
        # width: parallels
        # height: meridians

        elevation_range = np.linspace(-np.pi / 2, np.pi / 2, self._width),
        azimuth_range = np.linspace(0, np.pi, self._height) if self._half else \
            np.linspace(0, 2 * np.pi * (self._height - 2) / self._height,
                        self._height)
        self._grid = np.meshgrid(elevation_range, azimuth_range)

    def get_image2d_dim(self):
        return (self._radius * 2, self._radius * 2)

    @property
    def radius(self):
        return self._radius

    @property
    def grid(self):
        return self._grid

    @property
    def screen_to_image_map(self):
        return self._screen_to_image_map

    def generate_video(self, data, coordinates, rng, videofile):
        from scipy.interpolate import griddata
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib
        matplotlib.use('Agg')
        from matplotlib import cm
        import matplotlib.pyplot as plt
        from matplotlib.animation import FFMpegFileWriter, AVConvFileWriter
        from matplotlib.colors import Normalize

        # Could have multiplied all coordinates with self._radius
        # but the result would not change visually

        # unpacking coordinates of data
        elevpositions, azimpositions = coordinates

        # conversion to cartesian
        x = (-np.cos(azimpositions) * np.cos(elevpositions)).flatten()
        y = (-np.sin(azimpositions) * np.cos(elevpositions)).flatten()
        z = (np.sin(elevpositions)).flatten()

        # constructing screen grid
        U, V = np.mgrid[0:np.pi / 2:complex(0, 60),
                        0:2 * np.pi:complex(0, 60)]
        # conversion to cartesian
        X = np.cos(V) * np.sin(U)
        Y = np.sin(V) * np.sin(U)
        Z = np.cos(U)
        X_flat = X.flatten()
        Y_flat = Y.flatten()
        Z_flat = Z.flatten()

        # initialization
        fig = plt.figure(figsize=plt.figaspect(0.8), dpi=80)
        writer = AVConvFileWriter(fps=5, codec='mpeg4')
        writer.setup(
            fig, videofile, dpi=80,
            frame_prefix=os.path.splitext(videofile)[0] + '_')
        writer.frame_format = 'png'

        step = 10
        plt.hold(False)

        ax = fig.add_subplot('111', projection='3d')
        ax.set_title('Input')

        ax.xaxis.set_ticks([])
        ax.yaxis.set_ticks([])
        ax.zaxis.set_ticks([])

        norm = Normalize(vmin=rng[0], vmax=rng[1], clip=True)

        for i in range(0, len(data), step):
            data_flat = data[i].flatten()
            colors = griddata((x, y, z), data_flat,
                              (X_flat, Y_flat, Z_flat),
                              'nearest').reshape(X.shape)
            # normalize values
            colors = norm(colors).data
            # convert to RGB (equal values of R,G,B = greyscale)
            colors = np.tile(np.reshape(colors, [X.shape[0], X.shape[1], 1]),
                             [1, 1, 4])
            colors[:, :, 3] = 1.0

            ax.clear()
            ax.xaxis.set_ticks([])
            ax.yaxis.set_ticks([])
            ax.zaxis.set_ticks([])
            ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                            facecolors=colors, antialiased=False,
                            shade=False)
            fig.canvas.draw()
            writer.grab_frame()
        writer.finish()


class CylinderScreen(Screen):

    def __init__(self, input_config, dt, retina_index = 0):
        config_screen = input_config.screenconfig

        self._radius = config_screen.radius
        # cylinder length
        # (height is more appropriate name but is used elsewhere)
        self._length = config_screen.height

        self._height = config_screen.columns
        self._width = config_screen.parallels

        # parameter corresponds to the length of the image
        # TODO allow to be specified
        self._screen_to_image_map = pointmapfactory(
            config_screen.image_map)(self._length)
        self._generate_grid()
        super(CylinderScreen, self).__init__(input_config, dt, retina_index = retina_index)

    def _generate_grid(self):
        C = self._height  # number of columns
        P = self._width   # number of parallels
        H = self._length  # length (or height) of cylinder -> this is y
        self._grid = np.meshgrid(
            np.linspace(-H / 2, H / 2, P),
            np.linspace(0, np.pi, C))

    def get_image2d_dim(self):
        # the first parameter must be the same as
        # cylinder length (or height) above,
        # the second should match the parameter of image_map
        # TODO have a more explicit connection
        return (self.height, self._length)

    @property
    def grid(self):
        return self._grid

    @property
    def screen_to_image_map(self):
        return self._screen_to_image_map

    @property
    def radius(self):
        return self._radius

    @property
    def height(self):
        return self._length

    def generate_video(self, data, coordinates, rng, videofile):
        from scipy.interpolate import griddata
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib
        matplotlib.use('Agg')
        from matplotlib import cm
        import matplotlib.pyplot as plt
        from matplotlib.animation import FFMpegFileWriter, AVConvFileWriter
        from matplotlib.colors import Normalize

        radius = self._radius

        # unpacking coordinates of data
        zpositions, thetapositions = coordinates
        # conversion to cartesian
        x = radius * np.cos(thetapositions).flatten()
        y = radius * np.sin(thetapositions).flatten()
        z = zpositions.flatten()

        # constructing screen grid
        Z, Theta = np.mgrid[z.min():z.max():complex(0, 60),
                            0:2 * np.pi:complex(0, 60)]

        # conversion to cartesian
        X = radius * np.cos(Theta)
        Y = radius * np.sin(Theta)
        X_flat = X.flatten()
        Y_flat = Y.flatten()
        Z_flat = Z.flatten()

        # initialization
        fig = plt.figure(figsize=plt.figaspect(0.8), dpi=80)
        writer = AVConvFileWriter(fps=5, codec='mpeg4')
        writer.setup(
            fig, videofile, dpi=80,
            frame_prefix=os.path.splitext(videofile)[0] + '_')
        writer.frame_format = 'png'

        step = 100
        plt.hold(False)

        ax = fig.add_subplot('111', projection='3d')
        ax.set_title('Input')

        ax.xaxis.set_ticks([])
        ax.yaxis.set_ticks([])
        ax.zaxis.set_ticks([])

        norm = Normalize(vmin=rng[0], vmax=rng[1], clip=True)

        for i in range(0, len(data), step):
            data_flat = data[i].flatten()
            colors = griddata((x, y, z), data_flat,
                              (X_flat, Y_flat, Z_flat),
                              'nearest').reshape(X.shape)
            # normalize values
            colors = norm(colors).data
            # convert to RGB (equal values of R,G,B = greyscale)
            colors = np.tile(np.reshape(colors, [X.shape[0], X.shape[1], 1]),
                             [1, 1, 4])
            colors[:, :, 3] = 1.0

            ax.clear()
            ax.xaxis.set_ticks([])
            ax.yaxis.set_ticks([])
            ax.zaxis.set_ticks([])
            ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                            facecolors=colors, antialiased=False,
                            shade=False)
            fig.canvas.draw()
            writer.grab_frame()
        writer.finish()


def screenfactory(screen_type):
    # I think this implementation will find only
    # the classes defined in this file
    all_screen_cls = Screen.__subclasses__()
    all_screen_names = [cls.__name__ for cls in all_screen_cls]
    try:
        screen_cls = all_screen_cls[all_screen_names.index(screen_type)]
    except ValueError:
        print('Invalid Screen subclass name:{}'.format(screen_type))
        return None
    return screen_cls


def main():
    # TODO
    pass

if __name__ == "__main__":
    main()
