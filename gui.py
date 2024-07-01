import tkinter as tk
from tkinter import messagebox
from utils import set_debug_mode, debug_print, save_config_key, load_config, \
    DEBUG_MODE_KEY, SELL_KEY_KEY, SELL_ALL_KEY_KEY, update_keybinds, setup_hotkeys


def start_gui():
    """
    Starts the GUI.
    """

    def on_exit():
        debug_print("Exiting script.")
        root.destroy()

    def update_keybinds_wrapper():
        sell_key = sell_key_entry.get()
        sell_all_key = sell_all_key_entry.get()
        if sell_key and sell_all_key:
            update_keybinds(sell_key, sell_all_key)
            save_config_key(SELL_KEY_KEY, sell_key)
            save_config_key(SELL_ALL_KEY_KEY, sell_all_key)
        else:
            messagebox.showwarning("Invalid Input", "Please enter valid keybinds.")

    def toggle_debug_mode():
        set_debug_mode(debug_var.get())
        save_config_key(DEBUG_MODE_KEY, debug_var.get())

    # Load configuration
    config = load_config()

    root = tk.Tk()
    root.title("Dofus AutoSeller")
    root.geometry("300x200")
    root.protocol("WM_DELETE_WINDOW", on_exit)

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

    tk.Button(root, text="Update Keybinds", command=update_keybinds_wrapper).pack(anchor="w")

    hotkeys_map = {
        SELL_KEY_KEY: sell_key_entry,
        SELL_ALL_KEY_KEY: sell_all_key_entry
    }

    setup_hotkeys(hotkeys_map)

    # Start the GUI event loop
    root.mainloop()
