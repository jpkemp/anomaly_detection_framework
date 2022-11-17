'''see https://stackoverflow.com/questions/23831510/abstract-attribute-not-property'''
from abc import ABCMeta

def abstract_attribute(obj=None):
    '''decorator for abstract attributes'''
    if obj is None:
        obj = object()

    obj.__is_abstract_attribute__ = True

    return obj


class AbstractMeta(ABCMeta):
    '''replace __call__ for ABCMeta'''
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        abstract_attributes = {
            name for name in dir(instance)
            if getattr(getattr(instance, name), '__is_abstract_attribute__', False)
        }
        if abstract_attributes:
            failed = ', '.join(abstract_attributes)
            raise NotImplementedError(
                f"Can't instantiate abstract class {cls.__name__} with abstract attributes: {failed}"
            )

        return instance
