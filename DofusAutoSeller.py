import time
import pyautogui
import keyboard
import threading
from utils import (
    debug_print,
    take_screenshot,
    detect_quantity,
    find_current_price,
    sell_item,
    fail_safe_shut_down
)
from gui import start_gui

# Start the mouse monitoring thread
mouse_thread = threading.Thread(target=fail_safe_shut_down, daemon=True)
mouse_thread.start()


def handle_sell():
    """
    Handles the sell process when the hotkey is pressed.
    """
    debug_print("\n________________ Selling item ________________")
    debug_print("Key pressed, processing...")

    saved_mouse_pos = pyautogui.position()
    pyautogui.moveTo(1, 1)

    screenshot = take_screenshot()

    quantity = detect_quantity(screenshot)
    current_price = find_current_price(screenshot, quantity)
    sell_item(screenshot, current_price)

    pyautogui.moveTo(saved_mouse_pos)

    debug_print("\nPress '*' to list the item...")
    debug_print("Press 'esc' to exit.")
    debug_print("______________________________________________")


def handle_sell_all():
    """
    Handles the sell process when the hotkey is pressed.
    """
    debug_print("\n________________ Selling item ________________")
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

    debug_print("\nPress '*' to list the item...")
    debug_print("Press 'esc' to exit.")
    debug_print("______________________________________________")


def handle_exit():
    """
    Handles the exit process when the hotkey is pressed.
    """
    debug_print("Exiting script.")
    exit(0)


if __name__ == "__main__":
    start_gui(handle_sell, handle_sell_all)
