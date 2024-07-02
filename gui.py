import tkinter as tk
import uuid

from logic import update_keybinds, setup_hotkeys
from utils.config import save_config_key, load_config, get_value
from utils.constants import SELL_KEY_KEY, SELL_ALL_KEY_KEY, DEBUG_MODE_KEY
from utils.debug_utils import debug_print

from utils.data_classes import MessageType
from utils.debug_utils import set_debug_mode


def start_gui():
    # Starts the GUI.
    def on_exit():
        debug_print("Exiting script.")
        root.destroy()

    def update_keybinds_wrapper():
        sell_key = sell_key_entry.get()
        sell_all_key = sell_all_key_entry.get()

        if sell_key == get_value(SELL_KEY_KEY) and sell_all_key == get_value(SELL_ALL_KEY_KEY):
            send_info_message("Keybinds have not changed.", MessageType.WARNING)
        elif sell_key and sell_all_key and sell_all_key != sell_key:
            update_keybinds(sell_key, sell_all_key)
            save_config_key(SELL_KEY_KEY, sell_key)
            save_config_key(SELL_ALL_KEY_KEY, sell_all_key)
            send_info_message("Keybinds updated successfully.", MessageType.SUCCESS)
        else:
            send_info_message("Invalid Input: Please enter valid keybinds.", MessageType.WARNING)

    def send_info_message(message, message_type):
        colors = {
            MessageType.SUCCESS: "green",
            MessageType.WARNING: "orange",
            MessageType.ERROR: "red"
        }
        message_id = str(uuid.uuid4())
        current_message.set(message_id)
        info_message.config(text=message, fg=colors.get(message_type, "black"))
        root.after(2000, clear_info_message, message_id)

    def clear_info_message(message_id):
        if current_message.get() == message_id:
            info_message.config(text="")

    def toggle_debug_mode():
        set_debug_mode(debug_var.get())
        save_config_key(DEBUG_MODE_KEY, debug_var.get())

    # Load configuration once
    config = load_config()

    root = tk.Tk()
    root.title("Dofus AutoSeller")
    root.geometry("300x200")
    root.protocol("WM_DELETE_WINDOW", on_exit)

    current_message = tk.StringVar(value="")

    # Checkboxes
    debug_var = tk.BooleanVar(value=config.get(DEBUG_MODE_KEY, True))
    tk.Checkbutton(root, text="Debug Mode", variable=debug_var, command=toggle_debug_mode).pack(anchor="w")

    # Hotkey Inputs
    tk.Label(root, text="Sell Key:").pack(anchor="w")
    sell_key_entry = tk.Entry(root, width=5, justify='center')
    sell_key_entry.insert(0, config.get(SELL_KEY_KEY, '*'))
    sell_key_entry.pack(anchor="w")

    tk.Label(root, text="Sell All Key:").pack(anchor="w")
    sell_all_key_entry = tk.Entry(root, width=5, justify='center')
    sell_all_key_entry.insert(0, config.get(SELL_ALL_KEY_KEY, '$'))
    sell_all_key_entry.pack(anchor="w")

    tk.Button(root, text="Save", command=update_keybinds_wrapper).pack(anchor="w")

    info_message = tk.Label(root, fg="green", text="")
    info_message.pack(anchor="w")

    hotkeys_map = {
        SELL_KEY_KEY: sell_key_entry,
        SELL_ALL_KEY_KEY: sell_all_key_entry
    }

    setup_hotkeys(hotkeys_map)
    set_debug_mode(debug_var.get())


    root.mainloop()
