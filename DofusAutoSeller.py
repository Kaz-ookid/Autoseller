import pyautogui
import keyboard
from utils import (
    debug_print,
    take_screenshot,
    detect_quantity,
    find_current_price,
    sell_item
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

current_sell_key = '*'
current_sell_all_key = '$'
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def handle_sell():
    """
    Handles the sell process when the hotkey is pressed.
    """
    debug_print(f"\n________________ Selling item with key {current_sell_key} ________________")
    debug_print("Key pressed, processing...")

    saved_mouse_pos = pyautogui.position()
    pyautogui.moveTo(1, 1)

    screenshot = take_screenshot()

    quantity = detect_quantity(screenshot)
    current_price = find_current_price(screenshot, quantity)
    sell_item(screenshot, current_price)

    pyautogui.moveTo(saved_mouse_pos)

    debug_print(f"\nPress '{current_sell_key}' to list the item...")
    debug_print("Press 'esc' to exit.")
    debug_print("______________________________________________")


def handle_sell_all():
    """
    Handles the sell process when the hotkey is pressed.
    """
    debug_print(f"\n________________ Selling item with key {current_sell_all_key} ________________")
    debug_print("Key pressed, processing...")

    saved_mouse_pos = pyautogui.position()
    pyautogui.moveTo(1, 1)

    screenshot = take_screenshot()

    quantity = detect_quantity(screenshot)
    quantity_has_changed = True

    last_price = {1: None, 10: None, 100: None}
    current_price = find_current_price(screenshot, quantity)

    while quantity is not None:
        if not quantity_has_changed:
            sell_item(screenshot, last_price[quantity], quick_sell=True)
        else:
            current_price = find_current_price(screenshot, quantity)
            sell_item(screenshot, current_price)
            last_price[quantity] = current_price

        screenshot = take_screenshot()
        new_quantity = detect_quantity(screenshot)

        if new_quantity is None:
            break

        if new_quantity != quantity:
            quantity = new_quantity
            quantity_has_changed = True
        else:
            quantity_has_changed = False

    pyautogui.moveTo(saved_mouse_pos)

    debug_print(f"\nPress '{current_sell_all_key}' to list the item...")
    debug_print("Press 'esc' to exit.")
    debug_print("______________________________________________")


def handle_exit():
    """
    Handles the exit process when the hotkey is pressed.
    """
    debug_print("Exiting script.")
    exit(0)


def update_keybinds(new_sell_key, new_sell_all_key):
    global current_sell_key, current_sell_all_key
    current_sell_key = new_sell_key
    current_sell_all_key = new_sell_all_key

    keyboard.unhook_all_hotkeys()
    keyboard.add_hotkey(current_sell_key, handle_sell)
    keyboard.add_hotkey(current_sell_all_key, handle_sell_all)

    debug_print(f"Updated keybinds: Sell -> '{current_sell_key}', Sell All -> '{current_sell_all_key}'")


def setup_hotkeys():
    keyboard.add_hotkey(current_sell_key, handle_sell)
    keyboard.add_hotkey(current_sell_all_key, handle_sell_all)


if __name__ == "__main__":
    setup_hotkeys()
    start_gui(update_keybinds)
