import sys, os, json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QFileDialog,
    QScrollArea, QMessageBox, QComboBox, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal


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
            
            # Calculate image position and scale
            x_offset = (self.width() - self.pixmap().width()) // 2
            y_offset = (self.height() - self.pixmap().height()) // 2
            scale = self.parent_widget.get_scale()
            
            # Convert click to image coordinates
            img_x = (pos.x() - x_offset) / scale
            img_y = (pos.y() - y_offset) / scale
            
            # Check if click is within image bounds
            if 0 <= img_x <= self.parent_widget.image.width() and \
               0 <= img_y <= self.parent_widget.image.height():
                
                # Check for box selection first
                for i, box in enumerate(self.parent_widget.boxes):
                    x1, y1, x2, y2 = box[:4]
                    # Normalize coordinates
                    x1, x2 = min(x1, x2), max(x1, x2)
                    y1, y2 = min(y1, y2), max(y1, y2)
                    
                    if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                        self.parent_widget.selected_box = i
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
                x1 = max(0, min((rect[0] - x_offset) / scale, self.parent_widget.image.width()))
                y1 = max(0, min((rect[1] - y_offset) / scale, self.parent_widget.image.height()))
                x2 = max(0, min((rect[2] - x_offset) / scale, self.parent_widget.image.width()))
                y2 = max(0, min((rect[3] - y_offset) / scale, self.parent_widget.image.height()))
                
                # Only add if box is large enough
                if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                    # Convert to integers for storage
                    box = [int(x1), int(y1), int(x2), int(y2)]
                    self.parent_widget.add_box(box)
                    
            self.current_rect = None
            self.parent_widget.update_display()


class ImageLabeler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Image Labeling Tool')
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Top toolbar with controls
        toolbar = QHBoxLayout()
        
        # Image selection combo
        self.image_combo = QComboBox()
        self.image_combo.currentIndexChanged.connect(lambda idx: self.next_image(idx - self.current_index))
        toolbar.addWidget(self.image_combo)
        
        # Class selection combo
        self.class_combo = QComboBox()
        self.class_combo.addItems(['person', 'car', 'bicycle', 'motorcycle', 'bus', 'truck'])
        toolbar.addWidget(self.class_combo)
        
        # Delete button
        self.delete_btn = QPushButton("Delete Box")
        self.delete_btn.clicked.connect(self.delete_selected_box)
        toolbar.addWidget(self.delete_btn)
        
        layout.addLayout(toolbar)
        
        # Scroll area for the image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Canvas for drawing
        self.canvas = CanvasLabel()
        self.canvas.set_parent_widget(self)
        scroll_area.setWidget(self.canvas)
        
        # Initialize variables
        self.current_image_path = None
        self.image = None
        self.current_index = 0
        self.boxes = []  # Format: [x1, y1, x2, y2, label]
        self.selected_box = -1
        self.scale = 1.0
        
        self.setGeometry(100, 100, 800, 600)
        self.setup_shortcuts()
        
        # Load images
        self.load_images()
        
    def setup_shortcuts(self):
        # Keyboard shortcuts
        self.shortcuts = {
            Qt.Key_Delete: self.delete_selected_box,
            Qt.Key_S: self.save_annotations,
            Qt.Key_Right: lambda: self.next_image(1),
            Qt.Key_Left: lambda: self.next_image(-1)
        }

    def keyPressEvent(self, event):
        if event.key() in self.shortcuts:
            self.shortcuts[event.key()]()
            
    def load_images(self):
        # Ask for image directory
        self.image_dir = QFileDialog.getExistingDirectory(self, "Select Image Directory")
 
        if not self.image_dir:
            sys.exit()
            
        # Get list of image files
        self.image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            self.image_files.extend(
                [f for f in os.listdir(self.image_dir) if f.lower().endswith(ext)]
            )
        self.image_files.sort()  # Sort files alphabetically
        
        if not self.image_files:
            QMessageBox.critical(self, "Error", "No images found in selected directory")
            sys.exit()
        
        # Update the combo box
        self.image_combo.clear()
        self.image_combo.addItems(self.image_files)
            
        self.current_index = 0
        self.load_current_image()
        
    def load_current_image(self):
        if 0 <= self.current_index < len(self.image_files):
            image_path = os.path.join(self.image_dir, self.image_files[self.current_index])
            self.current_image_path = image_path
            
            # Load image
            self.image = QImage(image_path)
            if self.image.isNull():
                QMessageBox.critical(self, "Error", f"Cannot load image: {image_path}")
                return
                
            # Load annotations if they exist
            self.boxes = []
            annotation_file = os.path.join(
                self.image_dir, 
                os.path.splitext(self.image_files[self.current_index])[0] + '.json'
            )
            if os.path.exists(annotation_file):
                with open(annotation_file, 'r') as f:
                    self.boxes = json.load(f)
                    
            self.update_display()
            self.setWindowTitle(f'Image Labeling Tool - {self.image_files[self.current_index]}')
            
    def get_scale(self):
        if not self.image or not self.canvas.pixmap():
            return 1.0
        return self.canvas.pixmap().width() / self.image.width()
        
    def update_preview(self, rect):
        if not self.image or not self.canvas.pixmap():
            return
            
        # Create a copy of the display
        pixmap = QPixmap.fromImage(self.image).scaled(
            self.canvas.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        if not pixmap:
            return
            
        # Calculate offset
        x_offset = (self.canvas.width() - pixmap.width()) // 2
        y_offset = (self.canvas.height() - pixmap.height()) // 2
            
        # Draw existing boxes
        painter = QPainter(pixmap)
        scale = pixmap.width() / self.image.width()
        
        # Draw existing boxes
        for i, box in enumerate(self.boxes):
            x1, y1, x2, y2 = [coord * scale for coord in box[:4]]
            painter.setPen(QPen(Qt.green if i != self.selected_box else Qt.red, 2))
            painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))
        
        # Draw the preview rectangle after adjusting for offset
        x1 = rect[0] - x_offset
        y1 = rect[1] - y_offset
        x2 = rect[2] - x_offset
        y2 = rect[3] - y_offset
        
        # Keep preview within image bounds
        x1 = max(0, min(x1, pixmap.width()))
        y1 = max(0, min(y1, pixmap.height()))
        x2 = max(0, min(x2, pixmap.width()))
        y2 = max(0, min(y2, pixmap.height()))
        
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))
        painter.end()
        
        self.canvas.setPixmap(pixmap)
        
    def update_display(self):
        if not self.image:
            return
            
        # Get canvas size
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        
        # Calculate scaled dimensions maintaining aspect ratio
        img_aspect = self.image.width() / self.image.height()
        canvas_aspect = canvas_width / canvas_height
        
        if canvas_aspect > img_aspect:
            # Canvas is wider than needed
            target_height = canvas_height
            target_width = int(target_height * img_aspect)
        else:
            # Canvas is taller than needed
            target_width = canvas_width
            target_height = int(target_width / img_aspect)
            
        # Scale image
        scaled_pixmap = QPixmap.fromImage(self.image).scaled(
            target_width,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        if not scaled_pixmap:
            return
            
        # Draw boxes
        painter = QPainter(scaled_pixmap)
        scale = scaled_pixmap.width() / self.image.width()  # Calculate scale directly
        
        for i, box in enumerate(self.boxes):
            x1, y1, x2, y2 = box[:4]
            # Normalize coordinates
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Scale to display coordinates
            dx1 = x1 * scale
            dy1 = y1 * scale
            dx2 = x2 * scale
            dy2 = y2 * scale
            
            painter.setPen(QPen(Qt.green if i != self.selected_box else Qt.red, 2))
            painter.drawRect(QRectF(dx1, dy1, dx2 - dx1, dy2 - dy1))
            
        painter.end()
        self.canvas.setPixmap(scaled_pixmap)
        
    def add_box(self, rect):
        # Normalize rectangle coordinates (ensure x1 < x2 and y1 < y2)
        x1, y1, x2, y2 = rect
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        # Get the current selected class
        class_idx = self.class_combo.currentIndex()
        
        # Add the box with the selected class
        self.boxes.append([x1, y1, x2, y2, class_idx])
        self.update_display()
        self.save_annotations()
        
    def delete_selected_box(self):
        if self.selected_box >= 0:
            self.boxes.pop(self.selected_box)
            self.selected_box = -1
            self.update_display()
            self.save_annotations()
            
    def save_annotations(self):
        if self.current_image_path:
            annotation_file = os.path.splitext(self.current_image_path)[0] + '.json'
            with open(annotation_file, 'w') as f:
                json.dump(self.boxes, f)
                
    def next_image(self, delta):
        if self.image_files:
            self.current_index = (self.current_index + delta) % len(self.image_files)
            self.load_current_image()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()


def main():
    app = QApplication(sys.argv)
    window = ImageLabeler()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
