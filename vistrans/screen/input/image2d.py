
import os
from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass
import numpy as np
from neurokernel.LPU.utils.simpleio import *


class Image2D(with_metaclass(ABCMeta, object)):
    # __metaclass__ = ABCMeta

    def __init__(self, config, dt, retina_index = 0):
        self.dt = dt
        self.dtype = np.double

        self.shape = tuple(config.shape)
        self.retina_index = retina_index

    def get_grid(self, xmin, xmax, ymin, ymax):
        return [np.linspace(xmin, xmax, self.shape[0]),
                np.linspace(ymin, ymax, self.shape[1])]

    def generate_2dimage(self, num_steps):
        im_v = np.empty((num_steps,) + self.shape, dtype=self.dtype)
        for i in range(num_steps):
            im_v[i] = self._generate_2dimage_step(self._internal_step)
            self._internal_step += 1

        return im_v

    # only resets internal step for now
    def reset(self):
        self._internal_step = 0

    @abstractmethod
    def _generate_2dimage_step(self, step):
        pass


class BaseImage():

    baseparams = ['speed', 'levels']

    def __init__(self, **kwargs):
        self.set_base_parameters(**kwargs)

    def set_base_parameters(self, config):
        self.speed = config.speed
        self.levels = (config.levels.min, config.levels.max)


# Classes in alphabetic order
class Ball(Image2D, BaseImage):

    def __init__(self, config, dt, retina_index = 0):
        Image2D.__init__(self, config, dt, retina_index = retina_index)

        self.set_parameters(config)

    def set_parameters(self, config):
        self.set_base_parameters(config)
        self.white_back = config.white_back

        rel_position = config.center
        shape = self.shape

        # add more options later if needed
        if rel_position == 'center':
            self.center = (shape[1] / 2, shape[0] / 2)
        else:
            # default center at the center of the image
            self.center = (shape[1] / 2, shape[0] / 2)

        self.x, self.y = np.meshgrid(np.arange(float(shape[1])),
                                     np.arange(float(shape[0])))
        self.reset()

    def _generate_2dimage_step(self, step):
        dt = self.dt
        levels = self.levels
        center = self.center
        speed = self.speed
        white_back = self.white_back

        im = (1 if white_back else -1) * np.sign(
            np.sqrt((self.x - center[0])**2 + (self.y - center[1])**2)
            - step * dt * speed).astype(np.double)

        return im * ((levels[1] - levels[0]) / 2) + (levels[1] + levels[0]) / 2


class Bar(Image2D, BaseImage):

    def __init__(self, config, dt, retina_index = 0):
        Image2D.__init__(self, config, dt, retina_index = retina_index)

        #input_config = self.get_input_config(config)
        self.set_parameters(config)

    def set_parameters(self, config):
        self.set_base_parameters(config)
        self.dir = config.direction
        self.bar_width = config.bar_width
        self.double = config.double
        self.reset()

    def _generate_2dimage_step(self, step):
        shape = self.shape

        im = np.ones(shape, dtype=self.dtype) * self.levels[0]
        if self.dir == 'v':  # vertical movement
            st1 = int(np.mod(step * self.speed * self.dt, shape[0]))
            en1 = min(int(st1 + self.bar_width), shape[0])
            im[st1:en1, :] = self.levels[1]
            if self.double:
                st2 = min(int(en1 + self.bar_width), shape[0])
                en2 = min(int(st2 + self.bar_width), shape[0])
                im[st2:en2, :] = self.levels[1]
        elif self.dir == 'h':  # horizontal movement
            st1 = int(np.mod(step * self.speed * self.dt, shape[1]))
            en1 = min(int(st1 + self.bar_width), shape[1])
            im[:, st1:en1] = self.levels[1]
            if self.double:
                st2 = min(int(en1 + self.bar_width), shape[1])
                en2 = min(int(st2 + self.bar_width), shape[1])
                im[:, st2:en2] = self.levels[1]
        else:
            raise ValueError('Invalid value for direction {}'
                             .format(self.dir))
        return im


class FlickerStep(Image2D):

    def __init__(self, config, dt, retina_index = 0):
        super(FlickerStep, self).__init__(config, dt, retina_index = retina_index)

        #input_config = self.get_input_config(config)
        self.set_parameters(config)

    def set_parameters(self, config):
        self.frequency = config.frequency
        self.levels = (config.levels.min, config.levels.max)
        self.count = 0
        self.reset()

    def _generate_2dimage_step(self, step):
        shape = self.shape

        im = np.ones(shape, dtype=self.dtype) * self.levels[self.count]
        if step >= int(1. / self.frequency / 2 / self.dt):
            self.reset()
            self.count = (self.count + 1) % len(self.levels)

        return im


class Gratings(Image2D):

    def __init__(self, config, dt, retina_index = 0):
        super(Gratings, self).__init__(config, dt, retina_index = retina_index)

        #input_config = self.get_input_config(config)
        self.set_parameters(config)

    def set_parameters(self, config):
        self.x_freq = config.x_freq
        self.y_freq = config.y_freq
        self.x_speed = config.x_speed
        self.y_speed = config.y_speed
        self.sinusoidal = config.sinusoidal
        self.levels = (config.levels.min, config.levels.max)
        self.reset()

    def _generate_2dimage_step(self, step):
        dt = self.dt
        levels = self.levels
        shape = self.shape
        x_freq = self.x_freq
        y_freq = self.y_freq
        x_speed = self.x_speed
        y_speed = self.y_speed
        sinusoidal = self.sinusoidal

        x, y = np.meshgrid(np.arange(float(shape[1])),
                           np.arange(float(shape[0])))

        if sinusoidal:
            sinfunc = lambda w: ((np.sin(w) + 1) / 2) * (levels[1] - levels[0]) \
                + levels[0]
        else:
            sinfunc = lambda w: np.sign(np.cos(w)) * ((levels[1] - levels[0]) / 2) \
                + (levels[1] + levels[0]) / 2

        return sinfunc(x_freq * 2 * np.pi * (x - x_speed * step * dt) +
                       y_freq * 2 * np.pi * (y - y_speed * step * dt))

    def get_config(self):
        return self.get_config_from_params(['x_freq', 'y_freq', 'x_speed',
                                            'y_speed', 'sinusoidal', 'levels'])


class Natural(Image2D):

    def __init__(self, config, dt, retina_index = 0):
        super(Natural, self).__init__(config, dt, retina_index = retina_index)

        #input_config = self.get_input_config(config)
        self.set_parameters(config)

    def set_parameters(self, config):
        np.random.seed(config.seed)

        #self.store_coords = config.store_coords
        # self.coord_file_name = os.path.join(self.folder,
        #                                     '{}{}{}.h5'.format(
        #                                         config['coord_file'],
        #                                         self.retina_index,
        #                                         self.suffix))
        self.image_file = config.image_file
        self.scale = config.scale
        self.speed = config.speed
        self.image = self.readimage()
        self.image *= self.scale / self.image.max()

        # start from the middle of the image
        self.imagex = self.image.shape[0] / 2
        self.imagey = self.image.shape[1] / 2
        self.vx = np.random.randn(1) * self.speed
        self.vy = np.random.randn(1) * self.speed
        self.margin = 10
        self.file_open = False

        self.reset()

    def readimage(self):
        from scipy.io import loadmat
        try:
            mat = loadmat(self.image_file)
        except AttributeError:
            print('Tried to read image before setting the file variable')
            raise
        except IOError:
            if self.image_file is None:
                print('Image file not specified')
            raise
        try:
            return np.array(mat['im'])
        except KeyError:
            print('No variable "im" in given mat file')
            print('Available variables (and meta-data): {}'
                  .format(list(mat.keys())))
            raise

    def generate_2dimage(self, num_steps):
        # photons are stored with unit photons/sec
        dt = self.dt
        shape = self.shape
        vx = self.vx
        vy = self.vy
        image = self.image
        imagex = self.imagex
        imagey = self.imagey
        margin = self.margin

        xy = np.zeros((num_steps, 2), np.int32)

        h_im, w_im = image.shape

        im_v = np.empty((num_steps,) + shape, dtype=self.dtype)
        for i in range(num_steps):
            imagex = imagex + vx * dt
            imagey = imagey + vy * dt

            # change direction if bound is reached
            imagex_max = imagex + shape[0]
            if imagex_max + margin > h_im:
                imagex = h_im - margin - shape[0]
                vx = -vx

            if imagex - margin <= 0:
                imagex = margin
                vx = -vx

            imagey_max = imagey + shape[0]
            if imagey_max + margin > w_im:
                imagey = w_im - margin - shape[1]
                vy = -vy

            if imagey - margin <= 0:
                imagey = margin
                vy = -vy

            # decimal indices are allowed and decimal part is ignored
            im_v[i] = image[int(np.round(imagex)):int(np.round(imagex)) + shape[0],
                            int(np.round(imagey)):int(np.round(imagey)) + shape[1]]
            xy[i, :] = (imagex, imagey)  # convert to int

            # change speed/direction every about 1/dt steps
            if np.random.rand() < dt:
                vx = np.random.randn(1) * self.speed

            if np.random.rand() < dt:
                vy = np.random.randn(1) * self.speed

        self.imagex = imagex
        self.imagey = imagey
        self.vx = vx
        self.vy = vy

        return im_v

    # Not used, class overrides generate_2dimage
    # and this function is not supposed to be called
    def _generate_2dimage_step(self, step):
        pass


def image2Dfactory(input_type):
    # I think this implementation will find only the classes defined in this
    # file
    all_image2d_cls = Image2D.__subclasses__()
    all_image2d_names = [cls.__name__ for cls in all_image2d_cls]
    try:
        image2d_cls = all_image2d_cls[all_image2d_names.index(input_type)]
    except ValueError:
        print('Invalid Image2D subclass name: {}'.format(input_type))
        print('Valid names: {}'.format(all_image2d_names))
        return None

    return image2d_cls


def savefig(values, ylabel, imagefile):
    '''
        Generates a graph from the given values and saves it in a file
    '''
    import pylab
    import matplotlib.pyplot as plt

    plt.hold(False)
    plt.plot(values)
    plt.ylabel(ylabel)

    pylab.savefig(imagefile)


def savemp4(images, videofile, step=10):
    '''
        Generates a frame every 10(default) images and saves all
        of them to a video file

        parameters:
            images: a numpy array where each row corresponds to an image
            videofile: file to store video
            step: every that number of images will be stored in the file
                  the rest will be ignored (e.g if step is 10
                  and images are 50, only images 1,11,21,31,41 will be stored)
    '''
    from matplotlib import cm
    from matplotlib.animation import FFMpegFileWriter, AVConvFileWriter
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=plt.figaspect(1.0))

    writer = FFMpegFileWriter(fps=5, codec='mpeg4')
    writer.setup(
        fig, videofile, dpi=80,
        frame_prefix=os.path.splitext(videofile)[0] + '_')
    writer.frame_format = 'png'

    plt.hold(False)

    ax = fig.add_subplot(111)

    plt.subplots_adjust(left=0, right=1.0)
    for i in range(0, len(images), step):
        ax.imshow(images[i], cmap=cm.Greys_r,
                  vmin=images.min(), vmax=images.max())
        fig.canvas.draw()
        writer.grab_frame()

    writer.finish()


def main():
    from neurokernel.tools.timing import Timer
    from retina.configreader import ConfigReader

    def test_image2D(imtype, write_video, write_image, write_screen, config):
        steps = config['General']['steps']
        config['General']['intype'] = imtype
        image2Dgen = image2Dfactory(imtype)(config)

        with Timer('generation of {} example input(steps {})'
                   .format(imtype, steps)):
            images = image2Dgen.generate_2dimage(num_steps=steps)

        if write_video:
            with Timer('writing video file'):
                savemp4(images, '{}_input.mp4'.format(imtype.lower()))

        if write_image:
            with Timer('writing image file'):
                savefig(np.log10(images[:, 1, 1] + 1e-10),
                        'logarithm of {}'.format(imtype),
                        'temp_{}.png'.format(imtype))

        if write_screen:
            print('Images: \n{}'.format(images))

    def get_config():
        conf_name = os.path.join('retina', 'config',
                                 'template.cfg')
        conf_specname = os.path.join('retina', 'config',
                                     'template_spec.cfg')
        return ConfigReader(conf_name, conf_specname).conf
    np.set_printoptions(precision=3)

    test_suite = ['Ball', 'Bar', 'FlickerStep', 'Natural']

    write_video = True
    write_image = False
    write_screen = False
    config = get_config()

    for cls in test_suite:
        test_image2D(cls, write_video, write_image, write_screen, config)

''' run as `python -m retina.model.image2d` '''
if __name__ == '__main__':
    main()
