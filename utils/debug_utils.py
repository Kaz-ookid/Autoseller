DEBUG_MODE = False


def debug_print(message):
    # Prints a debug message if debugging mode is enabled.
    if DEBUG_MODE:
        print(message)


def set_debug_mode(value):
    global DEBUG_MODE
    debug_print(f"Debug mode set to {value}")
    DEBUG_MODE = value
    debug_print(f"Debug mode set to {value}")


