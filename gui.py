import os
import tkinter as tk
import uuid

from PIL import ImageTk, Image

from logic import update_keybinds, KEYBINDS_FUNCTIONS
from utils.config import save_config_key, load_config, get_value
from utils.constants import DEBUG_MODE_TOGGLE_KEY
from utils.data_classes import MessageType
from utils.debug_utils import debug_print
from utils.debug_utils import set_debug_mode


def start_gui():
    def on_exit():
        debug_print("Exiting script.")
        root.destroy()

    def update_keybinds_wrapper(initial_setup=False):
        hotkeys_map = []
        changes_detected = False

        for action_key, function in KEYBINDS_FUNCTIONS.items():
            entry_widget = keybind_entries[action_key]
            new_keybind = entry_widget.get()
            current_keybind = get_value(action_key)

            if new_keybind and (initial_setup or new_keybind != current_keybind):
                hotkeys_map.append((action_key, new_keybind, function))
                changes_detected = True

        if changes_detected or initial_setup:
            update_keybinds(hotkeys_map, initial_setup)
            send_info_message("Keybinds updated successfully.", MessageType.SUCCESS)
        elif not changes_detected:
            send_info_message("Keybinds have not changed.", MessageType.WARNING)
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
        save_config_key(DEBUG_MODE_TOGGLE_KEY, debug_var.get())

    config = load_config()

    root = tk.Tk()
    root.title("Dofus AutoSeller")
    root.geometry("300x200")
    root.protocol("WM_DELETE_WINDOW", on_exit)

    icon_path = r'res/logo/DAS_icon.ico'
    root.iconbitmap(False, icon_path)

    current_message = tk.StringVar(value="")

    debug_var = tk.BooleanVar(value=config.get(DEBUG_MODE_TOGGLE_KEY, True))
    tk.Checkbutton(root, text="Debug Mode", variable=debug_var, command=toggle_debug_mode).pack(anchor="w")

    keybind_entries = {}

    for key in KEYBINDS_FUNCTIONS.keys():
        tk.Label(root, text=f"{key.replace('_', ' ').title()}:").pack(anchor="w")
        entry = tk.Entry(root, width=5, justify='center')
        entry.insert(0, config.get(key, ''))
        entry.pack(anchor="w")
        keybind_entries[key] = entry

    tk.Button(root, text="Save", command=update_keybinds_wrapper).pack(anchor="w")

    info_message = tk.Label(root, fg="green", text="")
    info_message.pack(anchor="w")

    # Call wrapper to set initial keybindings
    update_keybinds_wrapper(initial_setup=True)
    set_debug_mode(debug_var.get())

    root.mainloop()
