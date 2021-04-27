from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass

class SignalTransform(with_metaclass(ABCMeta, object)):
    # __metaclass__ = ABCMeta

    @abstractmethod
    def interpolate(self, image):
        """ gets the value of the signal at the specific point,
            as the signal is discrete it will be interpolated
        """
        return
