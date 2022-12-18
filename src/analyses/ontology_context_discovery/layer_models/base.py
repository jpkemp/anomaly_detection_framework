from abc import ABC, abstractmethod
from src.core.base.abstract_attributes import abstract_attribute, AbstractMeta
class NoModelError(Exception):
    '''Exception for when no model can be created from the data'''

class AbstractLayerModel(ABC, metaclass=AbstractMeta):
    @staticmethod
    @abstractmethod
    def create_role_data(test_case, log, label, subheadings):
        pass
