from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import keyboard
import numpy as np
import threading
import datetime
import cv2

class ImageViewer(QGraphicsView):
    mouseClicked = pyqtSignal(QPointF)
    mouseMoving = pyqtSignal(QPointF)
    mouseReleased = pyqtSignal(QPointF)
    clicked = pyqtSignal(str)
    def __init__(self, parent=None, name = None):
        super(ImageViewer, self).__init__(parent)
        self.name = name
        self.initBegin()

        self._empty = True
        self._zoom = 0 
        # Item
        self._pixmapImage = QGraphicsPixmapItem()
        self.image = None
        # Scenes
        self._scene = QGraphicsScene()
        self._scene.addItem(self._pixmapImage)

        self.setScene(self._scene)

        self.popMenu = QMenu(self)
        self.saveAction = QAction('Save Image', self)
        self.fitInViewAction = QAction('Fit In View', self)
        self.popMenu.addAction(self.saveAction)
        self.popMenu.addAction(self.fitInViewAction)
        self.saveAction.triggered.connect(lambda: self.save_pixmapImage())
        self.fitInViewAction.triggered.connect(lambda: self.fitInView())
        self.isDrag = False

        self._autoFit = True
        self._isDrawCenter = False
        self.zoomRatio = 1

        self.isPositionSelected = False
        self.currentObject = None
        self._transform2D = np.eye(3, dtype=np.float32)
        self.locker = threading.Lock()

    def initBegin(self):
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 88)))
        self.setFrameShape(QFrame.NoFrame)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.HighQualityAntialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)

    @property
    def autoFit(self): return self._autoFit
    @autoFit.setter
    def autoFit(self, value): 
        self._autoFit = value if self._autoFit != value else self._autoFit
    
    @property
    def isDrawCenter(self): return self._isDrawCenter
    @isDrawCenter.setter
    def isDrawCenter(self, value): 
        self._isDrawCenter = value if self._isDrawCenter != value else self._isDrawCenter
        self.invalidate()
        
    def save_pixmapImage(self):
        try:
            if self._empty is False:
                dt_format = datetime.datetime.now().timestamp()
                QPixmap.save(self._pixmapImage.pixmap(), f"save_image_{dt_format}.png", "JPG")
        except Exception as e:
            print(e)

    def _save_image_result(self, path):
        pixmap = QPixmap(self.viewport().size())
        self.viewport().render(pixmap)
        pixmap.save(path)

    def hasImage(self):
        return not self._empty

    def setImage(self, image=None):
        with self.locker:
            if image is not None:
                self._empty = False
                self._pixmapImage.setPixmap(QPixmap.fromImage(image))
                if self.autoFit:
                    self.fitInView()
                self.invalidate()
            else:
                self._empty = True
                self._pixmapImage.setPixmap(QPixmap())

    def fitInView(self, scale=True):
        rect = QRectF(self._pixmapImage.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasImage():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            big_margin = 5000 
            self.setSceneRect(self.sceneRect().adjusted(-big_margin, -big_margin, big_margin, big_margin))
            self.centerOn(rect.center())
            self._zoom = 0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom < 0:
            self.scale(factor, factor)
        else:
            self._zoom = 0
        self.zoomRatio = factor
                
    def clearImage(self):
        self._pixmapImage.setPixmap(QPixmap())

    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        if self._pixmapImage is None: return
        if keyboard.is_pressed('ctrl'):
            self.isDrag = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        emit_point = self.mapToScene(event.pos())
        self.mouseClicked.emit(emit_point)
        if event.buttons() & Qt.RightButton:
            self.popMenu.exec_(self.mapToGlobal(event.pos()))
        super(ImageViewer, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pixmapImage is None: return
        emit_point =self.mapToScene(event.pos())
        self.mouseMoving.emit(emit_point)
        self.viewport().update()
        super(ImageViewer, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pixmapImage is None: return
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        emit_point = self.mapToScene(event.pos())
        self.mouseReleased.emit(emit_point)
        super(ImageViewer, self).mouseMoveEvent(event)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setTransform(self.viewportTransform())
        if self.transform().m11()<0.01: return
                  
    def invalidate(self):
        self.viewport().update()

class MainTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Image Viewer")
        central_widget = QWidget()
        mainLayout = QHBoxLayout(central_widget)
        self.view = ImageViewer()
        self.view.mouseMoving.connect(lambda location: self.mouse_location(location))
        self.btn_load_image = QPushButton("Load Image")
        self.btn_load_image.clicked.connect(self.load_image_from_file)
        mainLayout.addWidget(self.btn_load_image)
        mainLayout.addWidget(self.view, stretch=1)
        self.setCentralWidget(central_widget)

    def load_image_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image File",
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )
        
        if file_path:
            image = self.convert_to_qImage(file_path)
            self.view.setImage(image)
    
    def convert_to_qImage(self, image_path):
        opencv_image = cv2.imread(image_path, 0) #0 = gray scale
        qimage = QImage(opencv_image.data, 
                       opencv_image.shape[1], 
                       opencv_image.shape[0], 
                       opencv_image.strides[0], 
                       QImage.Format_Indexed8) # convert to 8bit image use for gray, binary
        return qimage

    def mouse_location(self, pos):
        self.statusBar().showMessage("X:{0:.3f}, Y:{1:.3f}".format(pos.x(), pos.y()))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainTestWindow()
    window.show()
    sys.exit(app.exec_())
