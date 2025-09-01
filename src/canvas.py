from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor

class CanvasLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.drawing = False
        self.last_pos = None
        self.current_rect = None
        self.parent_widget = None
        
    def set_parent_widget(self, widget):
        self.parent_widget = widget

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.parent_widget and self.pixmap():
            pos = event.pos()
            # Convert screen coordinates to image coordinates
            scale = self.parent_widget.get_scale()
            x_offset = (self.width() - self.pixmap().width()) // 2
            y_offset = (self.height() - self.pixmap().height()) // 2
            img_x = (pos.x() - x_offset) / scale
            img_y = (pos.y() - y_offset) / scale
            
            # Check if clicking on existing box
            for i, box in enumerate(self.parent_widget.image_handler.boxes):
                x1, y1, x2, y2 = box[:4]
                # Normalize coordinates
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                    self.parent_widget.image_handler.selected_box = i
                    self.parent_widget.update_display()
                    return
            
            # If no box was clicked, start drawing
            self.drawing = True
            self.current_rect = [pos.x(), pos.y(), pos.x(), pos.y()]
            self.parent_widget.selected_box = -1  # Clear selection when drawing

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_rect:
            # Simply update the end point
            self.current_rect[2] = event.pos().x()
            self.current_rect[3] = event.pos().y()
            if self.parent_widget:
                self.parent_widget.update_preview(self.current_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.parent_widget and self.current_rect and self.pixmap():
                # Get the scaling factor
                scale = self.parent_widget.get_scale()
                
                # Get display offset
                x_offset = (self.width() - self.pixmap().width()) // 2
                y_offset = (self.height() - self.pixmap().height()) // 2
                
                # Convert screen coordinates to image coordinates
                rect = self.current_rect
                x1 = max(0, min((rect[0] - x_offset) / scale, self.parent_widget.image_handler.image.width()))
                y1 = max(0, min((rect[1] - y_offset) / scale, self.parent_widget.image_handler.image.height()))
                x2 = max(0, min((rect[2] - x_offset) / scale, self.parent_widget.image_handler.image.width()))
                y2 = max(0, min((rect[3] - y_offset) / scale, self.parent_widget.image_handler.image.height()))
                
                # Only add if box is large enough
                if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                    # Convert to integers for storage
                    box = [int(x1), int(y1), int(x2), int(y2)]
                    self.parent_widget.add_box(box)
                    
            self.current_rect = None
            self.parent_widget.update_display()
