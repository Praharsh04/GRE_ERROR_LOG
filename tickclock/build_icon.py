import sys
import os
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication
from PIL import Image

def build_icon():
    app = QApplication(sys.argv)
    
    # 1. Load SVG to QImage
    renderer = QSvgRenderer("assets/logo.svg")
    img = QImage(256, 256, QImage.Format_ARGB32)
    img.fill(0) # Transparent background
    
    painter = QPainter(img)
    renderer.render(painter)
    painter.end()
    
    # 2. Save as PNG
    png_path = "assets/logo.png"
    img.save(png_path)
    
    # 3. Convert PNG to ICO using Pillow
    icon_path = "assets/logo.ico"
    with Image.open(png_path) as img_pil:
        img_pil.save(icon_path, format="ICO", sizes=[(256, 256)])

    print(f"Icon successfully generated at {icon_path}")

if __name__ == "__main__":
    build_icon()
