# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# from traxx/__init__.py import app as WSGI application
from traxx import app as application
