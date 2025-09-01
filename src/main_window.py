from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QComboBox, QPushButton, QFileDialog
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen
from .canvas import CanvasLabel
from .image_handler import ImageHandler
import os

class ImageLabeler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_handler = ImageHandler()
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
        self.image_combo.currentIndexChanged.connect(self.on_image_selected)
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
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        # Canvas for drawing
        self.canvas = CanvasLabel()
        self.canvas.set_parent_widget(self)
        self.canvas.setMinimumSize(1, 1)  # Allow the label to shrink
        self.scroll_area.setWidget(self.canvas)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        # Set up image directory
        self.setup_image_directory()
        
    def setup_image_directory(self):
        """Set up the image directory and populate the combo box"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if not dir_path:
            return
            
        image_files = [f for f in os.listdir(dir_path) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        self.image_paths = [os.path.join(dir_path, f) for f in image_files]
        self.image_combo.addItems(['Select Image...'] + image_files)
        
    def on_image_selected(self, index):
        """Handle image selection from combo box"""
        if index <= 0:  # "Select Image..." or no selection
            return
            
        image_path = self.image_paths[index - 1]
        if self.image_handler.load_image(image_path):
            self.update_display()
            
    def get_scale(self):
        """Get current image scale"""
        return self.image_handler.scale
        
    def add_box(self, box):
        """Add a new bounding box"""
        self.image_handler.add_box(box, self.class_combo.currentText())
        self.update_display()
        
    def delete_selected_box(self):
        """Delete the currently selected box"""
        if self.image_handler.delete_box(self.image_handler.selected_box):
            self.image_handler.selected_box = -1
            self.update_display()
            
    def update_preview(self, rect):
        """Update the display with the current drawing preview"""
        self.update_display(preview_rect=rect)
        
    def update_display(self, preview_rect=None):
        """Update the display with current image and boxes"""
        if not self.image_handler.image:
            return
            
        # Get scaled pixmap
        pixmap = self.image_handler.get_scaled_pixmap(self.canvas.size())
        if not pixmap:
            return
            
        # Create a copy to draw on
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw existing boxes
        for i, box in enumerate(self.image_handler.boxes):
            pen = QPen(Qt.red if i == self.image_handler.selected_box else Qt.green, 2)
            painter.setPen(pen)
            
            x1, y1, x2, y2 = [coord * self.image_handler.scale for coord in box[:4]]
            painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))
            
            # Draw label
            if len(box) > 4:
                # Convert coordinates to integers for drawText
                painter.drawText(int(x1), int(y1 - 5), box[4])
        
        # Draw preview rect if available
        if preview_rect:
            painter.setPen(QPen(Qt.blue, 2))
            x1, y1, x2, y2 = preview_rect
            painter.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))
            
        painter.end()
        
        # Set the pixmap
        self.canvas.setPixmap(pixmap)
