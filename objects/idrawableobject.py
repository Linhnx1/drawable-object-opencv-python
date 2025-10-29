from abc import abstractmethod
from typing import Callable
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QObject

Drawing = Callable[[QPainter], None]

class InteractDrawableObject(QObject):
    def __init__(self):
        super(InteractDrawableObject, self).__init__()
        self._display = None
        self._is_position_change = False

    @property
    @abstractmethod
    def display(self) -> QGraphicsView:
        pass

    @display.setter
    @abstractmethod
    def display(self, value: QGraphicsView):
        pass

    @property
    def selection_size(self) -> int:
        return 10
    
    @property
    def is_position_change(self) -> bool:
        return self._is_position_change

    @is_position_change.setter
    def is_position_change(self, value: bool):
        self._is_position_change = value

    @abstractmethod
    def findPoint(self, mouse_location) -> bool:
        pass

    @abstractmethod
    def selectPoint(self):
        pass

    @abstractmethod
    def resetSelectPoint(self):
        pass

    @abstractmethod
    def draw(self, painter: QPainter):
        painter.pen().setCosmetic(True)
        pass

    @abstractmethod
    def getShapeRegion(self, image):
        pass
    
    def update(self):
        if self.display:
            self.display.invalidate()