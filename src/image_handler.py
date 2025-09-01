import json
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class ImageHandler:
    def __init__(self):
        self.current_image_path = None
        self.image = None
        self.boxes = []  # Format: [x1, y1, x2, y2, label]
        self.selected_box = -1
        self.scale = 1.0
        
    def load_image(self, image_path):
        """Load an image and return success status"""
        if not image_path:
            return False
            
        self.image = QImage(image_path)
        if self.image.isNull():
            return False
            
        self.current_image_path = image_path
        self.load_annotations()
        return True
    
    def load_annotations(self):
        """Load annotations for the current image"""
        self.boxes = []
        try:
            with open('annotations.json', 'r') as f:
                annotations = json.load(f)
                if self.current_image_path in annotations:
                    self.boxes = annotations[self.current_image_path]
        except (FileNotFoundError, json.JSONDecodeError):
            pass
            
    def save_annotations(self):
        """Save current annotations to file"""
        try:
            try:
                with open('annotations.json', 'r') as f:
                    annotations = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                annotations = {}
                
            annotations[self.current_image_path] = self.boxes
            
            with open('annotations.json', 'w') as f:
                json.dump(annotations, f, indent=2)
        except Exception as e:
            print(f"Error saving annotations: {e}")
            
    def add_box(self, box, label):
        """Add a new bounding box with label"""
        box.append(label)
        self.boxes.append(box)
        self.save_annotations()
        
    def delete_box(self, index):
        """Delete a box by index"""
        if 0 <= index < len(self.boxes):
            self.boxes.pop(index)
            self.save_annotations()
            return True
        return False
        
    def get_scaled_pixmap(self, canvas_size):
        """Get a scaled pixmap for display"""
        if not self.image:
            return None
            
        # Create base pixmap
        pixmap = QPixmap.fromImage(self.image)
        
        # Only scale down if the image is larger than the viewport
        if self.image.width() > canvas_size.width() or self.image.height() > canvas_size.height():
            # Calculate scale to fit image in viewport while maintaining aspect ratio
            scale_w = canvas_size.width() / self.image.width()
            scale_h = canvas_size.height() / self.image.height()
            self.scale = min(scale_w, scale_h)
            
            # Scale the pixmap
            scaled_width = int(self.image.width() * self.scale)
            scaled_height = int(self.image.height() * self.scale)
            return pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # Image is smaller than viewport, display at original size
            self.scale = 1.0
            return pixmap
