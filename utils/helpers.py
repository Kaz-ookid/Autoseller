from utils.debug_utils import debug_print
import pygetwindow as gw

DOFUS_FOCUSED = False


def to_search_area(corners, screen_size):
    """
    Convert bounding box coordinates to fractions of the screen size.

    Args:
    corners (tuple): A tuple containing the coordinates of the bounding box in the format (left, top, right, bottom).
    screen_size (tuple): The size of the screen in the format (screen_width, screen_height).

    Returns:
    tuple: A tuple containing the search area as fractions of the screen size in the format (left, top, right, bottom).
    """
    left, top, right, bottom = corners
    screen_width, screen_height = screen_size

    return (
        left / screen_width,
        top / screen_height,
        1 - (right / screen_width),
        1 - (bottom / screen_height)
    )


def get_game_window_size():
    game_window = [w for w in gw.getWindowsWithTitle('- Dofus') if w.visible]
    if game_window:
        window = game_window[0]
        debug_print(f"Game window size: {window.width}x{window.height}")
        return window.width, window.height
    else:
        debug_print("Dofus game window not found.")
        return None, None


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

