from .xmlfactorymixin import XmlFactoryMixin


class Bug(XmlFactoryMixin):
    # TODO: where we get tracker and ID ?
    def __str__(self):
        return "{0}:{1}".format(self.tracker, self.id)
