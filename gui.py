import tkinter as tk
from tkinter import messagebox

def start_gui(handle_sell, handle_sell_all):
    """
    Starts the GUI.
    """
    def on_exit():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()

    root = tk.Tk()
    root.title("Dofus AutoSeller")
    root.geometry("300x200")
    root.protocol("WM_DELETE_WINDOW", on_exit)

    # Checkboxes
    debug_var = tk.BooleanVar(value=True)
    tk.Checkbutton(root, text="Debug Mode", variable=debug_var).pack(anchor="w")

    # Hotkey Inputs
    tk.Label(root, text="Hotkeys:").pack(anchor="w")
    tk.Entry(root, width=5, justify='center').pack(anchor="w")

    # Buttons
    tk.Button(root, text="Sell Item", command=handle_sell).pack(anchor="w")
    tk.Button(root, text="Sell All Items", command=handle_sell_all).pack(anchor="w")

    # Start the GUI event loop
    root.mainloop()
