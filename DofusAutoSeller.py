import pyautogui
import keyboard
from utils import (
    debug_print,
    take_screenshot,
    detect_quantity,
    find_current_price,
    sell_item, load_config
)
from gui import start_gui

"""
Dofus AutoSeller Script
Author: Maxime @ Kaz
Date: June 2024

Description:
This script automates the process of selling items in the Dofus game. It captures the screen, detects the price table, 
determines the appropriate quantity, and automates the interaction with the game's selling interface.

Features:
Visual detection of price and quantity
Robust error handling and input validation
Configurable debugging mode for detailed output
Image preprocessing for accurate OCR
Constants for configuration and paths

Usage:
Ensure the necessary image cues are placed in the 'res' directory.
Run the script, select an item and press the '*' key to trigger the selling process.
"""





if __name__ == "__main__":
    start_gui()
