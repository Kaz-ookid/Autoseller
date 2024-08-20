import pytesseract

TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
CUSTOM_TESSERACT_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

CONFIG_PATH = 'config.json'
DEFAULT_CONFIG_PATH = 'default_config.json'

WHITE_PIXEL_THRESHOLD = 180
WHITE = 255
RES_PATH = 'res/'
DEBUG_PATH = 'debug/'
LOCATE_ELEMENT_THRESHOLD = 0.7
QUANTITY_ONE = '1'
QUANTITY_TEN = '10'
QUANTITY_HUNDRED = '100'
SELL_SEARCH_AREA = (1 / 6.5, 1 / 6, 0.7, 1 / 6)  # (left, top, right, bottom)
OUI_BUTTON_SEARCH_AREA = (2 / 7, 1 / 2, 3 / 7, 1 / 4)
INPUTS_SEARCH_AREA = (1 / 6.5, 1/6, 0.7, 1 / 2)
PRICES_SEARCH_AREA = (1 / 6.5, 0.45, 0.7, 1 / 6)

DEBUG_MODE_TOGGLE_KEY = 'DEBUG_MODE'
SELL_JSON_KEY = 'SELL_KEY'
SELL_ALL_JSON_KEY = 'SELL_ALL_KEY'

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
