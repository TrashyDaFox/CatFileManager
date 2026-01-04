import sys
import os

base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_path)

from app.Application import Application

app = Application()
app.run()