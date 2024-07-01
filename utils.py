import cv2
import pytesseract
import pyautogui
import numpy as np
import re
import os
import time
import sys

# Constants
DEBUG_MODE = True
THRESHOLD = 180
WHITE = 255
RES_PATH = 'res/'
DEBUG_PATH = 'debug/'
LOCATE_ELEMENT_THRESHOLD = 0.7
CUSTOM_TESSERACT_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
QUANTITY_ONE = '1'
QUANTITY_TEN = '10'
QUANTITY_HUNDRED = '100'
SELL_SEARCH_AREA = (1 / 6.5, 1 / 6, 4 / 6, 1 / 6)  # (left, top, right, bottom)
OUI_BUTTON_SEARCH_AREA = (2 / 7, 1 / 2, 3 / 7, 1 / 4)  # (left, top, right, bottom)
FAIL_SAFE_X = 1900
FAIL_SAFE_Y = 10
MOUSE_CHECK_INTERVAL = 0.1

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


def debug_print(message):
    """Prints a debug message if debugging mode is enabled."""
    if DEBUG_MODE:
        print(message)


def locate_element(template_path, image, threshold=LOCATE_ELEMENT_THRESHOLD, global_search_area=SELL_SEARCH_AREA):
    """
    Locate the template image within a larger image.

    Args:
        template_path (str): Path to the template image.
        image (np.ndarray): The image in which to search.
        threshold (float): The threshold for template matching.
        global_search_area (tuple): The search area as a fraction of the image dimensions.

    Returns:
        tuple: The top-left corner and size of the detected template, or (None, None) if not found.
    """
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
    """
    Takes a screenshot of the current screen.

    Returns:
        np.ndarray: The screenshot image.
    """
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def extract_table(roi):
    """
    Extracts a table of numbers from a region of interest (ROI) in an image.

    Args:
        roi (np.ndarray): The region of interest image.

    Returns:
        dict: A dictionary mapping quantities to prices.
    """
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    if DEBUG_MODE:
        cv2.imwrite(f'{RES_PATH}gray.png', gray)

    _, thresh = cv2.threshold(gray, THRESHOLD, WHITE, cv2.THRESH_BINARY_INV)

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
    """
    Detects the price table in the screenshot.

    Args:
        screenshot (np.ndarray): The screenshot image.

    Returns:
        dict: A dictionary mapping quantities to prices.
    """
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
    """
    Detects the quantity selected in the screenshot.

    Args:
        screenshot (np.ndarray): The screenshot image.

    Returns:
        int: The detected quantity, or None if not found.
    """

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
    """
    Automates the process of selling an item.

    Args:
        screenshot (np.ndarray): The screenshot image.
        current_price (int): The price to list the item at.
        quick_sell (bool): Whether to skip the price input field and list the item at the current price.
    """

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

    price = str(current_price - 1)
    if price <= '0':
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
    """
    Finds the current price of the item for the given quantity.

    Args:
        screenshot (np.ndarray): The screenshot image.
        quantity (int): The quantity of the item.

    Returns:
        int: The current price of the item, or None if not found.
    """
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


def fail_safe_shut_down():
    """Monitors the mouse position and shuts down the program if the mouse is in the top right corner."""
    while True:
        x, y = pyautogui.position()
        if x >= FAIL_SAFE_X and y <= FAIL_SAFE_Y:
            debug_print("Mouse moved to top right corner. Shutting down...")
            sys.exit()
        time.sleep(MOUSE_CHECK_INTERVAL)
