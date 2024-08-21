import os
import re
import time

import cv2
import keyboard
import numpy as np
import pyautogui
from pytesseract import pytesseract

from utils.config import save_config_key, get_value, load_config
from utils.constants import WHITE, RES_PATH, DEBUG_PATH, \
    LOCATE_ELEMENT_THRESHOLD, QUANTITY_ONE, QUANTITY_TEN, QUANTITY_HUNDRED, WHITE_PIXEL_THRESHOLD, \
    CUSTOM_TESSERACT_CONFIG, DEBUG_MODE_TOGGLE_KEY, SELL_JSON_KEY, \
    SELL_ALL_JSON_KEY, ALL_SCREEN_SEARCH_AREA, LOCATE_TITLE_THRESHOLD, DEBUG_SCREEN_WITH_TEMPLATE_PATH, \
    DEBUG_FOUND_ELEMENTS_PATH
from utils.data_classes import SellProcessType, Coordinates
from utils.debug_utils import debug_print
from utils.helpers import get_game_window_size, is_game_window_open_and_focused

current_keybindings = load_config()
registered_hotkeys = []

element_coordinates = {}


def reset_element_coordinates():
    global element_coordinates
    element_coordinates = {}
    debug_print("Element coordinates have been reset.")


def locate_element(template_path, image, threshold=LOCATE_ELEMENT_THRESHOLD, global_search_area=ALL_SCREEN_SEARCH_AREA):
    if not os.path.exists(template_path):
        debug_print(f"Template image not found: {template_path}")
        return None, None

    template = cv2.imread(template_path)
    if template is None:
        debug_print(f"Failed to load template image: {template_path}")
        return None, None

    template_original_height, template_original_width = template.shape[:2]

    current_width, current_height = get_game_window_size()
    if current_width is None or current_height is None:
        return None, None

    original_width = 2560
    original_height = 1440

    scale_factor = min(current_width / original_width, current_height / original_height)
    max_scaling_attempts = 5  # Number of attempts to resize the template
    scaling_increment = 1.05  # Increment scale by 5% each attempt

    image_rgb = image  # Assuming the input 'image' is already in BGR format
    height, width = image_rgb.shape[:2]
    left, top, right, bottom = int(width * global_search_area[0]), int(height * global_search_area[1]), int(
        width * (1 - global_search_area[2])), int(height * (1 - global_search_area[3]))

    search_area = image_rgb[top:bottom, left:right]

    for attempt in range(max_scaling_attempts):
        new_width = int(template_original_width * scale_factor)
        new_height = int(template_original_height * scale_factor)
        template_resized = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_AREA)

        if get_value(DEBUG_MODE_TOGGLE_KEY):
            debug_screenshot_with_template(search_area, template_resized)

        if search_area.shape[0] < template_resized.shape[0] or search_area.shape[1] < template_resized.shape[1]:
            debug_print(
                f"Template image is larger than the search area. Template size: {template_resized.shape}, Search area size: {search_area.shape}")
            return None, None

        # Perform template matching
        result = cv2.matchTemplate(search_area, template_resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            found_x, found_y = max_loc[0] + left, max_loc[1] + top
            element_width, element_height = template_resized.shape[1], template_resized.shape[0]

            if get_value(DEBUG_MODE_TOGGLE_KEY):
                save_found_element(image, found_x, found_y, element_width, element_height)

            return (found_x, found_y), (element_width, element_height)

        # Increase the scale factor for the next attempt
        scale_factor *= scaling_increment

    debug_print("Element not found after all scaling attempts.")
    return None, None


def save_found_element(image, x, y, width, height):
    """Save the found element as an image for debugging purposes."""
    found_element = image[y:y+height, x:x+width]
    debug_path = f'{RES_PATH}{DEBUG_PATH}{DEBUG_FOUND_ELEMENTS_PATH}'
    os.makedirs(debug_path, exist_ok=True)
    debug_file_path = os.path.join(debug_path, f'found_element_{int(time.time())}.png')
    cv2.imwrite(debug_file_path, found_element)


def debug_screenshot_with_template(screen_image, template_image):
    """Save a screenshot with the template pasted in the middle for debugging."""
    screen_height, screen_width = screen_image.shape[:2]
    template_height, template_width = template_image.shape[:2]

    # Determine the center position to paste the template
    center_x = (screen_width - template_width) // 2
    center_y = (screen_height - template_height) // 2

    # Paste the template onto the screen image
    screen_image_with_template = screen_image.copy()
    screen_image_with_template[center_y:center_y + template_height, center_x:center_x + template_width] = template_image

    # Save the debug image
    debug_path = f'{RES_PATH}{DEBUG_PATH}{DEBUG_SCREEN_WITH_TEMPLATE_PATH}'
    os.makedirs(debug_path, exist_ok=True)
    debug_file_path = os.path.join(debug_path, f'debug_screenshot_with_template_{int(time.time())}.png')
    cv2.imwrite(debug_file_path, screen_image_with_template)



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

    price_loc, elem_size = get_element_coordinates('price_table', price_table_header_cue_path, screenshot)
    if price_loc is None:
        debug_print("Price table not found.")
        return None

    x_top_r, y_top_r = price_loc[0] + elem_size[0], price_loc[1] + elem_size[1]
    x_bot_l, y_bot_l = price_loc[0], price_loc[1] + elem_size[1]

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
        return x, y, 2*w, h

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

    number_str = re.findall(r'\d+', extracted_text).pop() if extracted_text else None

    # Check if the extracted text is a valid quantity
    if number_str in {QUANTITY_ONE, QUANTITY_TEN, QUANTITY_HUNDRED}:
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
    if not is_game_window_open_and_focused():
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
