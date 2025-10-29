from .idrawableobject import InteractDrawableObject
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen

from enum import Enum
import numpy as np
import math
import cv2

class SelectionPoint(Enum):
    NONE = -1
    MOVE = -2
    TOPLEFT = 0
    TOPRIGHT = 1
    BOTTOMRIGHT = 2
    BOTTOMLEFT = 3
    ROTATE = 4

class RotationRectangle(InteractDrawableObject):
    def __init__(self, center_x=300, center_y=300, width=200, height=100, angle=0):
        super().__init__()
        self._center = QPointF(center_x, center_y)
        self._width = width
        self._height = height
        self._angle = angle  # degrees
        
        self.selectionPoint = SelectionPoint.NONE
        self._last_mouse_pos = QPointF()
        self._is_position_change = False
        self._display = None

        self._color = Qt.blue
        self._handle_color = Qt.green
        self._rotation_handle_color = Qt.red
        
    @property
    def center(self) -> QPointF:
        return self._center
    
    @center.setter
    def center(self, value: QPointF):
        self._center = value
    
    @property
    def width(self) -> float:
        return self._width
    
    @width.setter
    def width(self, value: float):
        self._width = max(10, value)  
    
    @property
    def height(self) -> float:
        return self._height
    
    @height.setter
    def height(self, value: float):
        self._height = max(10, value) 
    
    @property
    def angle(self) -> float:
        return self._angle
    
    @angle.setter
    def angle(self, value: float):
        self._angle = value % 360 
    
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, value):
        self._color = value
    
    @property
    def display(self):
        return self._display
    
    @display.setter
    def display(self, value):
        self._display = value

    def get_corners(self):
        corners = []
        half_w = self._width / 2
        half_h = self._height / 2
        
        local_corners = [
            QPointF(-half_w, -half_h),  # Top-left
            QPointF(half_w, -half_h),   # Top-right
            QPointF(half_w, half_h),    # Bottom-right
            QPointF(-half_w, half_h)    # Bottom-left
        ]
        
        angle_rad = math.radians(self._angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        for corner in local_corners:
            x_rot = corner.x() * cos_a - corner.y() * sin_a
            y_rot = corner.x() * sin_a + corner.y() * cos_a
            corners.append(QPointF(x_rot + self._center.x(), y_rot + self._center.y()))
        
        return corners
    
    def get_rotation_handle_pos(self):
        distance = max(self._width, self._height) / 2 + 20
        angle_rad = math.radians(self._angle)
        
        x = self._center.x() + distance * math.sin(angle_rad)
        y = self._center.y() - distance * math.cos(angle_rad)
        
        return QPointF(x, y)
    
    def findPoint(self, mouse_location):
        if self.is_position_change:
            return self._handle_drag(mouse_location)

        rot_handle = self.get_rotation_handle_pos()
        if (rot_handle - mouse_location).manhattanLength() < self.selection_size:
            self.selectionPoint = SelectionPoint.ROTATE
            self._last_mouse_pos = mouse_location
            self.display.setCursor(Qt.ClosedHandCursor)
            return True

        corners = self.get_corners()
        for i, corner in enumerate(corners):
            if (corner - mouse_location).manhattanLength() < self.selection_size:
                self.selectionPoint = SelectionPoint(i)
                self.display.setCursor(Qt.CrossCursor)
                return True

        if self._is_point_in_rotated_rect(mouse_location):
            self.selectionPoint = SelectionPoint.MOVE
            self._last_mouse_pos = mouse_location
            self.display.setCursor(Qt.SizeAllCursor)
            return True

        self.selectionPoint = SelectionPoint.NONE
        self.display.unsetCursor()
        return False
    
    def _handle_drag(self, mouse_location):
        if self.selectionPoint == SelectionPoint.NONE:
            self.resetSelectPoint()
            return False
        
        delta = mouse_location - self._last_mouse_pos
        
        if self.selectionPoint == SelectionPoint.MOVE:
            self._center += delta
            self._last_mouse_pos = mouse_location
            return True
        
        elif self.selectionPoint == SelectionPoint.ROTATE:
            vec_to_mouse = mouse_location - self._center
            new_angle = math.degrees(math.atan2(vec_to_mouse.x(), -vec_to_mouse.y()))
            self._angle = new_angle
            self._last_mouse_pos = mouse_location
            return True
        
        elif 0 <= self.selectionPoint.value <= 3: 
            corners = self.get_corners()
            opposite_corners = {
                0: 2,  # Top-left <-> Bottom-right
                1: 3,  # Top-right <-> Bottom-left  
                2: 0,  # Bottom-right <-> Top-left
                3: 1   # Bottom-left <-> Top-right
            }
            
            fixed_corner = corners[opposite_corners[self.selectionPoint.value]]
            moving_corner = mouse_location
            
            new_center = (fixed_corner + moving_corner) / 2
            
            angle_rad = math.radians(-self._angle)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            local_vec = moving_corner - new_center
            local_x = local_vec.x() * cos_a - local_vec.y() * sin_a
            local_y = local_vec.x() * sin_a + local_vec.y() * cos_a
            
            new_width = abs(local_x) * 2
            new_height = abs(local_y) * 2
            
            if new_width >= 10 and new_height >= 10: 
                self._width = new_width
                self._height = new_height
                self._center = new_center
            
            return True
        
        return False
    
    def _is_point_in_rotated_rect(self, point):
        angle_rad = math.radians(-self._angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        local_point = point - self._center
        local_x = local_point.x() * cos_a - local_point.y() * sin_a
        local_y = local_point.x() * sin_a + local_point.y() * cos_a
        
        half_w = self._width / 2
        half_h = self._height / 2
        
        return abs(local_x) <= half_w and abs(local_y) <= half_h
    
    def selectPoint(self):
        if self.selectionPoint != SelectionPoint.NONE:
            self.is_position_change = True

    def resetSelectPoint(self):
        self.is_position_change = False
        self.selectionPoint = SelectionPoint.NONE

    def getShapeRegion(self, image: np.ndarray) -> np.ndarray:
        corners = self.get_corners()
        if len(corners) < 3:
            return None
        
        pts = np.array([[p.x(), p.y()] for p in corners], dtype=np.int32)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 255)
        
        result = cv2.bitwise_and(image, image, mask=mask)
        
        x, y, w, h = cv2.boundingRect(pts)
        
        if (x + w <= 0 or x >= image.shape[1] or 
            y + h <= 0 or y >= image.shape[0]):
            return np.array([])
        
        cropped = result[max(0, y):min(y+h, image.shape[0]), 
                        max(0, x):min(x+w, image.shape[1])]
        
        return cropped

    def draw(self, painter):
        pen = QPen(self._color, 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        corners = self.get_corners()
        painter.drawPolygon(*corners)
        
        scale = self.display.transform().m11() if self.display else 1.0
        handle_size = max(4, int(6 / scale))
        
        painter.setPen(QPen(self._handle_color, 1))
        painter.setBrush(self._handle_color)
        for corner in corners:
            painter.drawEllipse(
                corner.x() - handle_size / 2,
                corner.y() - handle_size / 2,
                handle_size,
                handle_size
            )
        
        rot_handle = self.get_rotation_handle_pos()
        painter.setPen(QPen(self._rotation_handle_color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            rot_handle.x() - handle_size,
            rot_handle.y() - handle_size,
            handle_size * 2,
            handle_size * 2
        )
        
        painter.drawLine(self._center, rot_handle)
        
        painter.setPen(QPen(Qt.yellow, 1))
        painter.setBrush(Qt.yellow)
        painter.drawEllipse(
            self._center.x() - handle_size / 3,
            self._center.y() - handle_size / 3,
            handle_size / 1.5,
            handle_size / 1.5
        )
    
    def update(self):
        if self.display:
            self.display.invalidate()