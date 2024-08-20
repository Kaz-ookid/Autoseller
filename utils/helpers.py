from fractions import Fraction


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