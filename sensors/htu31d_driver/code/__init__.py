# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Jose D. Montoya
# @File    : __init__.py
# @Description : HTU31D driver package exports
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== Imports =========================================

from .htu31d import HTU31D

__all__ = ("HTU31D",)

# ======================================== Global variables =========================================

# ======================================== Functions =========================================

# ======================================== Custom classes =========================================

# ======================================== Initialization configuration =========================================

# ======================================== Main program ===========================================
