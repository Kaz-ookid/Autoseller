import json
import cv2
import keyboard
import pytesseract
import pyautogui
import numpy as np
import re
import os
import time
import pygetwindow as gw
from enum import Enum

# Constants
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
CUSTOM_TESSERACT_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

DEBUG_MODE = False
CONFIG_PATH = 'config.json'
DEFAULT_CONFIG_PATH = 'default_config.json'

THRESHOLD = 180
WHITE = 255
RES_PATH = 'res/'
DEBUG_PATH = 'debug/'
LOCATE_ELEMENT_THRESHOLD = 0.7
QUANTITY_ONE = '1'
QUANTITY_TEN = '10'
QUANTITY_HUNDRED = '100'
SELL_SEARCH_AREA = (1 / 6.5, 1 / 6, 4 / 6, 1 / 6)  # (left, top, right, bottom)
OUI_BUTTON_SEARCH_AREA = (2 / 7, 1 / 2, 3 / 7, 1 / 4)  # (left, top, right, bottom)

DEBUG_MODE_KEY = 'DEBUG_MODE'
SELL_KEY_KEY = 'SELL_KEY'
SELL_ALL_KEY_KEY = 'SELL_ALL_KEY'

QUANTITY_CUES = {
    1: f'{RES_PATH}quantity_1_cue.png',
    10: f'{RES_PATH}quantity_10_cue.png',
    100: f'{RES_PATH}quantity_100_cue.png'
}

ALT_QUANTITY_CUES = {
    1: f'{RES_PATH}quantity_1_cue_prefilled.png',
    10: f'{RES_PATH}quantity_10_cue_prefilled.png',
    100: f'{RES_PATH}quantity_100_cue_prefilled.png'
}

current_sell_key = '*'
current_sell_all_key = '$'
registered_hotkeys = []

DOFUS_FOCUSED = False


def debug_print(message):
    # Prints a debug message if debugging mode is enabled.
    if DEBUG_MODE:
        print(message)


def set_debug_mode(value):
    global DEBUG_MODE
    DEBUG_MODE = value
    debug_print(f"Debug mode set to {DEBUG_MODE}")


def save_config_key(key, value):
    # Saves a single key-value pair to the configuration file.
    config = load_config()
    config[key] = value
    save_config(config)


def load_config():
    # Loads the configuration from a file, checks its integrity, and saves it if it's incomplete.
    # Returns:
    # dict: The loaded and possibly updated configuration.
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as config_file:
            config = json.load(config_file)
            debug_print("Config loaded.")
    else:
        load_and_save_default_config()

    if not check_config_integrity(config):
        load_and_save_default_config()

    return config


def load_and_save_default_config():
    # Loads the default configuration from a file and saves it to the config file.
    with open(DEFAULT_CONFIG_PATH, 'r') as default_config_file:
        config = json.load(default_config_file)
        save_config(config)
        debug_print("Default config loaded and saved.")


def check_config_integrity(config):
    # Checks if the config is complete and updates it with default values if necessary.
    # Args:
    # config (dict): The configuration to check.
    #
    # Returns:
    # bool: True if the configuration was already complete, False if it was updated.
    with open(DEFAULT_CONFIG_PATH, 'r') as default_config_file:
        default_config = json.load(default_config_file)

    updated = False
    for key in default_config:
        if key not in config:
            config[key] = default_config[key]
            updated = True
            debug_print("Config incomplete")

    return not updated


def save_config(config):
    # Saves the configuration to a file.
    # Args:
    # config (dict): The configuration to save.
    with open(CONFIG_PATH, 'w') as config_file:
        json.dump(config, config_file, indent=4)
        debug_print("Config saved.")


def update_keybinds(new_sell_key, new_sell_all_key):
    # Updates the key bindings for selling items.
    # Args:
    # new_sell_key (str): The new key for selling a single item.
    # new_sell_all_key (str): The new key for selling all items.
    global current_sell_key, current_sell_all_key, registered_hotkeys

    # Unhook only if there are registered hotkeys
    if registered_hotkeys:
        for hotkey in registered_hotkeys:
            keyboard.remove_hotkey(hotkey)

    current_sell_key = new_sell_key
    current_sell_all_key = new_sell_all_key

    # Add the new hotkeys and store their references
    registered_hotkeys = [
        keyboard.add_hotkey(current_sell_key, handle_sell),
        keyboard.add_hotkey(current_sell_all_key, handle_sell_all)
    ]

    save_config_key(SELL_KEY_KEY, current_sell_key)
    save_config_key(SELL_ALL_KEY_KEY, current_sell_all_key)

    debug_print(f"Updated keybinds: Sell -> '{current_sell_key}', Sell All -> '{current_sell_all_key}'")


def unhook_hotkeys():
    # Unhook all registered hotkeys.
    global registered_hotkeys
    if registered_hotkeys:
        for hotkey in registered_hotkeys:
            keyboard.remove_hotkey(hotkey)
        registered_hotkeys = []


def hook_hotkeys():
    # Re-hook the hotkeys.
    global current_sell_key, current_sell_all_key, registered_hotkeys
    registered_hotkeys = [
        keyboard.add_hotkey(current_sell_key, handle_sell),
        keyboard.add_hotkey(current_sell_all_key, handle_sell_all)
    ]


def get_debug_mode():
    config = load_config()
    return config.get(DEBUG_MODE_KEY, True)


def locate_element(template_path, image, threshold=LOCATE_ELEMENT_THRESHOLD, global_search_area=SELL_SEARCH_AREA):
    # Locate the template image within a larger image.
    # Args:
    # template_path (str): Path to the template image.
    # image (np.ndarray): The image in which to search.
    # threshold (float): The threshold for template matching.
    # global_search_area (tuple): The search area as a fraction of the image dimensions.
    #
    # Returns:
    # tuple: The top-left corner and size of the detected template, or (None, None) if not found.
    if not os.path.exists(template_path):
        debug_print(f"Template image not found: {template_path}")
        return None, None

    template = cv2.imread(template_path, 0)
    if template is None:
        debug_print(f"Failed to load template image: {template_path}")
        return None, None

    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = image_gray.shape
    left, top, right, bottom = int(width * global_search_area[0]), int(height * global_search_area[1]), int(
        width * (1 - global_search_area[2])), int(height * (1 - global_search_area[3]))

    if DEBUG_MODE:
        timestamp = int(time.time())
        cv2.imwrite(f'{RES_PATH}{DEBUG_PATH}search_area_' + str(timestamp) + '.png', image[top:bottom, left:right])

    search_area = image_gray[top:bottom, left:right]

    if search_area.shape[0] < template.shape[0] or search_area.shape[1] < template.shape[1]:
        debug_print(
            f"Template image is larger than the search area. Template size: {template.shape}, Search area size: {search_area.shape}")
        return None, None

    result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        return (max_loc[0] + left, max_loc[1] + top), template.shape[::-1]
    else:
        return None, None


def take_screenshot():
    # Takes a screenshot of the current screen.
    #
    # Returns:
    # np.ndarray: The screenshot image.
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def extract_table(roi):
    # Extracts a table of numbers from a region of interest (ROI) in an image.
    #
    # Args:
    # roi (np.ndarray): The region of interest image.
    #
    # Returns:
    # dict: A dictionary mapping quantities to prices.
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    if DEBUG_MODE:
        cv2.imwrite(f'{RES_PATH}gray.png', gray)

    # Adjust the threshold value slightly to improve precision
    adjusted_threshold = 160
    _, thresh = cv2.threshold(gray, adjusted_threshold, WHITE, cv2.THRESH_BINARY_INV)

    if DEBUG_MODE:
        cv2.imwrite(f'{RES_PATH}thresholded.png', thresh)

    extracted_text = pytesseract.image_to_string(thresh, config=CUSTOM_TESSERACT_CONFIG)

    rows = extracted_text.split('\n')
    data_map = {}

    debug_print("\nExtracted text:")
    for row in rows:
        debug_print(row)

    for row in rows:
        numbers = re.findall(r'\d+', row)
        if numbers and numbers[0] in {QUANTITY_ONE, QUANTITY_TEN, QUANTITY_HUNDRED}:
            left_value = int(numbers[0])
            right_value = int(''.join(numbers[1:]))
            data_map[left_value] = right_value

    return data_map


def detect_prices(screenshot):
    # Detects the price table in the screenshot.
    #
    # Args:
    # screenshot (np.ndarray): The screenshot image.
    #
    # Returns:
    # dict: A dictionary mapping quantities to prices.
    price_table_header_cue_path = f'{RES_PATH}price_table_cue.png'
    price_table_header_cue_dim = cv2.imread(price_table_header_cue_path, 0).shape

    price_loc, _ = locate_element(price_table_header_cue_path, screenshot)
    if price_loc is None:
        debug_print("Price table not found.")
        return None

    x_top_r, y_top_r = price_loc[0] + price_table_header_cue_dim[1], price_loc[1] + price_table_header_cue_dim[0]
    x_bot_l, y_bot_l = price_loc[0], price_loc[1] + price_table_header_cue_dim[0]

    height, width, _ = screenshot.shape

    rows_detected = 0
    last_row_was_white = False
    while rows_detected < 3 and y_bot_l < height - 1:
        y_bot_l += 1
        horizontal_line = screenshot[y_bot_l, x_bot_l:x_top_r]
        is_white_row = np.any(horizontal_line > THRESHOLD)

        if not is_white_row and last_row_was_white:
            rows_detected += 1

        last_row_was_white = is_white_row

    y_bot_l += 10
    y_bot_l = min(y_bot_l, height - 1)

    top_right_coord = (x_top_r, y_top_r)
    bot_left_coord = (x_bot_l, y_bot_l)

    roi = screenshot[y_top_r:bot_left_coord[1], bot_left_coord[0]:top_right_coord[0]]

    if DEBUG_MODE:
        cv2.imwrite(f'{RES_PATH}roi.png', roi)

    price_map = extract_table(roi)

    debug_print("Price table:")
    for key, value in price_map.items():
        debug_print(f"{key}: {value}")

    return price_map


def detect_quantity(screenshot):
    # Detects the quantity selected in the screenshot.
    #
    # Args:
    # screenshot (np.ndarray): The screenshot image.
    #
    # Returns:
    # int: The detected quantity, or None if not found.

    for quantity, cue_path in QUANTITY_CUES.items():
        loc, _ = locate_element(cue_path, screenshot, 0.98)
        if loc is not None:
            debug_print(f"Quantity {quantity} detected.")
            return quantity

    for quantity, cue_path in ALT_QUANTITY_CUES.items():
        loc, _ = locate_element(cue_path, screenshot, 0.98)
        if loc is not None:
            debug_print(f"Quantity {quantity} detected.")
            return quantity

    debug_print("\nQuantity not detected.")
    return None


def sell_item(screenshot, current_price, quick_sell=False):
    # Automates the process of selling an item.
    #
    # Args:
    # screenshot (np.ndarray): The screenshot image.
    # current_price (int): The price to list the item at.
    # quick_sell (bool): Whether to skip the price input field and list the item at the current price.

    if quick_sell:
        debug_print("Quick sell for price : " + str(current_price))
        pyautogui.press('enter')
        return

    price_input_cue_path = f'{RES_PATH}price_input_cue.png'
    price_input_loc, size = locate_element(price_input_cue_path, screenshot)
    if price_input_loc is None:
        debug_print("Price input field not found.")
        return

    if current_price is None:
        debug_print("Invalid price detected.")
        return

    click_x = price_input_loc[0] + size[0] + 50
    click_y = price_input_loc[1] + size[1] // 2

    price_value = current_price - 1
    price = str(price_value)
    if price_value <= 0:
        debug_print("Invalid price detected.")
        return

    pyautogui.click(click_x, click_y)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    pyautogui.typewrite(price)

    time.sleep(0.01)

    click_sell(screenshot, price=price)


def click_sell(screenshot, price='0'):
    was_alt = False
    sell_button_cue_path = f'{RES_PATH}sell_button_cue.png'
    sell_button_loc, size = locate_element(sell_button_cue_path, screenshot)
    if sell_button_loc is None:
        debug_print("Sell button not found.")

        pyautogui.press('enter')
        was_alt = True
        oui_screenshot = take_screenshot()
        tries = 0

        while sell_button_loc is None:
            oui_button_cue_path = f'{RES_PATH}oui_button_cue.png'
            sell_button_loc, size = locate_element(oui_button_cue_path, oui_screenshot, 0.9, OUI_BUTTON_SEARCH_AREA)
            if sell_button_loc is None:
                tries += 1
            if tries > 10:
                debug_print("Confirm sell button not found.")
                return
            time.sleep(0.01)
            oui_screenshot = take_screenshot()

    click_x = sell_button_loc[0] + size[0] // 2
    click_y = sell_button_loc[1] + size[1] // 2

    pyautogui.click(click_x, click_y)

    if was_alt:
        debug_print("Item price modified to adjusted price: " + price)
    else:
        debug_print("Item listed at adjusted price : " + price)


def find_current_price(screenshot, quantity):
    # Finds the current price of the item for the given quantity.
    #
    # Args:
    # screenshot (np.ndarray): The screenshot image.
    # quantity (int): The quantity of the item.
    #
    # Returns:
    # int: The current price of the item, or None if not found.
    if quantity is None:
        debug_print("Invalid quantity detected.")
        return None

    price_map = detect_prices(screenshot)
    if price_map is None:
        debug_print("Price detection failed.")
        return None

    current_price = price_map.get(quantity, None)
    if current_price is None:
        debug_print("Price not found for the given quantity.")
        return None

    return current_price


class ProcessType(Enum):
    SINGLE = "single"
    ALL = "all"


def handle_sell():
    # Handles the sell process when the hotkey is pressed.
    execute_sell_process(single_sell_process, ProcessType.SINGLE)


def handle_sell_all():
    # Handles the sell process when the hotkey is pressed.
    execute_sell_process(sell_all_process, ProcessType.ALL)


def execute_sell_process(process_function, process_type):
    # Executes the sell process.
    #
    # Args:
    # process_function (function): The function to execute the unique part of the sell process.
    # process_type (ProcessType): The type of sell process.
    refresh_focus_status()
    if not DOFUS_FOCUSED:
        debug_print(f"Dofus window is not focused. Aborting {process_type.value} sell action.")
        return

    debug_print(f"\n________________ Selling item with {process_type.value} key ________________")
    debug_print("Key pressed, processing...")

    saved_mouse_pos = pyautogui.position()
    pyautogui.moveTo(1, 1)

    screenshot = take_screenshot()
    process_function(screenshot)

    pyautogui.moveTo(saved_mouse_pos)

    debug_print(f"\nPress '{current_sell_key}' to list the item...")
    debug_print("Press 'esc' to exit.")
    debug_print("______________________________________________")


def single_sell_process(screenshot):
    # Executes the unique part of the single sell process.
    #
    # Args:
    # screenshot (np.ndarray): The screenshot image.
    quantity = detect_quantity(screenshot)
    current_price = find_current_price(screenshot, quantity)
    sell_item(screenshot, current_price)


def sell_all_process(screenshot):
    # Executes the unique part of the sell all process.
    #
    # Args:
    # screenshot (np.ndarray): The screenshot image.
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


def refresh_focus_status():
    global DOFUS_FOCUSED
    DOFUS_FOCUSED = is_game_window_open_and_focused()


def is_game_window_open_and_focused():
    game_windows = [w for w in gw.getWindowsWithTitle('- Dofus') if w.visible]
    focused_window = gw.getActiveWindow()
    if focused_window and any(focused_window.title == w.title for w in game_windows):
        debug_print(f"Game window {focused_window.title} is focused.")
        return True
    debug_print("Game window is either not open or not focused.")
    return False


def setup_hotkeys(hotkeys_map):
    update_keybinds(hotkeys_map[SELL_KEY_KEY].get(), hotkeys_map[SELL_ALL_KEY_KEY].get())


def check_game_window_focus(root):
    refresh_focus_status()
    root.after(15000, check_game_window_focus, root)
