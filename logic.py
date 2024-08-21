import os
import re
import time

import cv2
import keyboard
import numpy as np
import pyautogui
import pygetwindow as gw
from pytesseract import pytesseract

from utils.config import save_config_key, get_value, load_config
from utils.constants import WHITE, RES_PATH, DEBUG_PATH, \
    LOCATE_ELEMENT_THRESHOLD, QUANTITY_ONE, QUANTITY_TEN, QUANTITY_HUNDRED, WHITE_PIXEL_THRESHOLD, \
    CUSTOM_TESSERACT_CONFIG, DEBUG_MODE_TOGGLE_KEY, SELL_JSON_KEY, \
    SELL_ALL_JSON_KEY, ALL_SCREEN_SEARCH_AREA
from utils.data_classes import SellProcessType, Coordinates
from utils.debug_utils import debug_print

current_keybindings = load_config()
registered_hotkeys = []

DOFUS_FOCUSED = False
element_coordinates = {}


def locate_element(template_path, image, threshold=LOCATE_ELEMENT_THRESHOLD, global_search_area=ALL_SCREEN_SEARCH_AREA):
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

    if get_value(DEBUG_MODE_TOGGLE_KEY):
        timestamp = int(time.time())
        cv2.imwrite(
            f'{RES_PATH}{DEBUG_PATH}search_area_' + str(timestamp) + '_' + str(np.random.randint(0, 10000)) + '.png',
            image[top:bottom, left:right])

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
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def extract_text(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    if get_value(DEBUG_MODE_TOGGLE_KEY):
        cv2.imwrite(f'{RES_PATH}{DEBUG_PATH}gray.png', gray)

    adjusted_threshold = 140
    _, thresh = cv2.threshold(gray, adjusted_threshold, WHITE, cv2.THRESH_BINARY_INV)

    if get_value(DEBUG_MODE_TOGGLE_KEY):
        cv2.imwrite(f'{RES_PATH}{DEBUG_PATH}thresholded.png', thresh)

    return pytesseract.image_to_string(thresh, config=CUSTOM_TESSERACT_CONFIG)


def extract_table(roi):
    extracted_text = extract_text(roi)

    rows = extracted_text.split('\n')
    data_map = {}

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
    price_table_header_cue_path = f'{RES_PATH}price_table_cue.png'
    price_table_header_cue_dim = cv2.imread(price_table_header_cue_path, 0).shape

    price_loc, _ = get_element_coordinates('price_table', price_table_header_cue_path, screenshot)
    if price_loc is None:
        debug_print("Price table not found.")
        return None

    x_top_r, y_top_r = price_loc[0] + price_table_header_cue_dim[1], price_loc[1] + price_table_header_cue_dim[0]
    x_bot_l, y_bot_l = price_loc[0], price_loc[1] + price_table_header_cue_dim[0]

    height, width, _ = screenshot.shape

    rows_detected = 0
    max_height = 0
    last_row_was_white = False
    while rows_detected < 3 and y_bot_l < height - 1:
        y_bot_l += 1
        horizontal_line = screenshot[y_bot_l, x_bot_l:x_top_r]
        is_white_row = np.any(horizontal_line > WHITE_PIXEL_THRESHOLD)

        if not is_white_row and last_row_was_white:
            rows_detected += 1

        last_row_was_white = is_white_row

        if max_height == 0:
            if rows_detected == 1:
                # debug_print("y_bot_l: " + str(y_bot_l))
                # debug_print("y_top_r: " + str(y_top_r))
                max_height = (y_bot_l - y_top_r) * 5 + y_top_r
                # debug_print("max_height: " + str(max_height))

        if max_height != 0 and y_bot_l > max_height:
            break

    y_bot_l += 10  # margin
    y_bot_l = min(y_bot_l, height - 1)

    top_right_coord = (x_top_r, y_top_r)
    bot_left_coord = (x_bot_l, y_bot_l)

    roi = screenshot[y_top_r:bot_left_coord[1], bot_left_coord[0]:top_right_coord[0]]

    if get_value(DEBUG_MODE_TOGGLE_KEY):
        cv2.imwrite(f'{RES_PATH}{DEBUG_PATH}roi.png', roi)

    price_map = extract_table(roi)

    debug_print("Price table:")
    for key, value in price_map.items():
        debug_print(f"{key}: {value}")

    return price_map


def detect_quantity(screenshot):
    quantity_title_cue_path = f'{RES_PATH}quantity_title_cue.png'

    def position_offset(x, y, w, h):
        roi_x = x + w  # Right edge of the title box
        roi_y = y
        return roi_x, roi_y, w, h

    # Locate the quantity number by applying the offset to the title's position
    quantity_loc, size = get_element_coordinates(
        'quantity_title',
        quantity_title_cue_path,
        screenshot,
        offset_function=lambda x, y, w, h: position_offset(x, y, w, h),
    )

    if quantity_loc is None:
        debug_print("Quantity title not found, thus quantity number not detected.")
        return None

    # Use the cached position of the quantity number directly
    roi_x, roi_y = quantity_loc
    roi_w, roi_h = size[0], size[1]

    # Define the region of interest (ROI) for the quantity number
    roi = screenshot[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]

    if get_value(DEBUG_MODE_TOGGLE_KEY):
        cv2.imwrite(f'{RES_PATH}{DEBUG_PATH}quantity_roi.png', roi)

    # Extract the text from the ROI
    extracted_text = extract_text(roi).strip()

    # Check if the extracted text is a valid quantity
    if extracted_text in {QUANTITY_ONE, QUANTITY_TEN, QUANTITY_HUNDRED}:
        quantity = int(extracted_text)
        debug_print(f"Quantity {quantity} detected.")
        return quantity

    debug_print("Quantity not detected.")
    return None


def get_element_coordinates(key, cue_path, screenshot, threshold=LOCATE_ELEMENT_THRESHOLD,
                            search_area=ALL_SCREEN_SEARCH_AREA, offset_function=None):
    if key in element_coordinates:
        debug_print(f"Using cached coordinates for {key}.")
        elem = element_coordinates[key]
        return (elem.x, elem.y), elem.size

    loc, size = locate_element(cue_path, screenshot, threshold, search_area)
    if loc is not None:
        x, y = loc
        if offset_function:
            x, y, w, h = offset_function(x, y, size[0], size[1])
            loc = (x, y)
            size = (w, h)
        element_coordinates[key] = Coordinates(x, y, size[0], size[1])
        debug_print(f"Coordinates for {key} found: {element_coordinates[key]}")
    return loc, size


def sell_item(screenshot, current_price, quick_sell=False):
    if quick_sell:
        debug_print("Quick sell for price : " + str(current_price))
        pyautogui.press('enter')
        time.sleep(0.16)
        return

    price_input_cue_path = f'{RES_PATH}price_input_cue.png'

    # Search for the price input location once and store it
    price_input_loc, size = get_element_coordinates('price_input', price_input_cue_path, screenshot)

    if price_input_loc is None:
        debug_print("Price input field not found.")
        return

    if current_price is None or current_price <= 0:
        debug_print("Invalid price detected. Operation aborted.")
        return

    click_x = price_input_loc[0] + size[0] + 50
    click_y = price_input_loc[1] + size[1] // 2

    price_value = current_price - 1
    price = str(price_value)

    pyautogui.click(click_x, click_y)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    pyautogui.typewrite(price)

    time.sleep(0.01)

    click_sell(screenshot, price=price)


def click_sell(screenshot, price='0'):
    was_alt = False
    sell_button_cue_path = f'{RES_PATH}sell_button_cue.png'
    sell_button_loc, size = get_element_coordinates('sell_button', sell_button_cue_path, screenshot)
    if sell_button_loc is None:
        debug_print("Sell button not found.")

        pyautogui.press('enter')
        was_alt = True
        oui_screenshot = take_screenshot()

        tries = 0

        while sell_button_loc is None:
            oui_button_cue_path = f'{RES_PATH}oui_button_cue.png'
            sell_button_loc, size = locate_element(oui_button_cue_path, oui_screenshot, 0.9)
            if sell_button_loc is None:
                tries += 1
            if tries > 5:
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


def handle_sell():
    execute_sell_process(single_sell_process, SellProcessType.SINGLE)


def handle_sell_all():
    execute_sell_process(sell_all_process, SellProcessType.ALL)


def execute_sell_process(process_function, process_type):
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

    debug_print(f"\nPress key to list the item...")
    debug_print("______________________________________________")


def single_sell_process(screenshot):
    quantity = detect_quantity(screenshot)
    if quantity is not None:
        current_price = find_current_price(screenshot, quantity)
        if current_price is not None:
            sell_item(screenshot, current_price)
            return
    debug_print("Operation aborted.")
    return


def sell_all_process(screenshot):
    quantity = detect_quantity(screenshot)
    if quantity is None:
        debug_print("Operation aborted.")
        return
    quantity_has_changed = True

    last_price = {1: None, 10: None, 100: None}

    while quantity is not None:
        if not quantity_has_changed:
            sell_item(screenshot, last_price[quantity], quick_sell=True)
        else:
            current_price = find_current_price(screenshot, quantity)
            if current_price is None:
                debug_print("Operation aborted.")
                break
            sell_item(screenshot, current_price)
            last_price[quantity] = current_price

        screenshot = take_screenshot()
        new_quantity = detect_quantity(screenshot)

        if new_quantity is None:
            debug_print("Operation aborted.")
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
    return False


def update_keybinds(hotkeys_map, initial_setup=False):
    if not initial_setup:
        for action, key, function in hotkeys_map:
            current_key = get_value(action)
            if current_key:
                keyboard.remove_hotkey(current_key)

    for action, key, function in hotkeys_map:
        keyboard.add_hotkey(key, function)
        save_config_key(action, key)

    debug_print(f"Updated keybinds: {[(action, key) for action, key, _ in hotkeys_map]}")


KEYBINDS_FUNCTIONS = {
    SELL_JSON_KEY: handle_sell,
    SELL_ALL_JSON_KEY: handle_sell_all,
}
