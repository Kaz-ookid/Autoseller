![Logo Banner](res/logo/DAS_banner.png)

# Dofus AutoSeller

 This script automates the process of selling items in the Dofus game. It captures the screen, detects the price table, determines the appropriate quantity, and automates the interaction with the game's selling interface.

 ## Features
 - Automatically lists items at a price -1 kamas cheaper than the lowest listed item to ensure yours appears first.
 - Automatically lists a whole stack of an item at -1 kamas for each quantity pack (100, 10, 1) to ensure the whole stack is sold.
 - Automatically updates the price of items already listed in the "Hotel des Ventes" (HdV).
 - A lot of quality of life features are coming soon.

 ## Prerequisites
 - Python 3.x
 - Required Python packages (install using `pip install -r requirements.txt`)

 ## Installation

 ### Clone the Repository
 ```bash
 git clone <repository_url>
 cd <repository_directory>
 ```

 ### Install Python Dependencies
Within the DofusAutoSell directory, run:
 ```bash
 pip install -r requirements.txt
 ```

 ## Configuration

### Tesseract-OCR
1. Set the path to the Tesseract-OCR executable in the `utils.py` file:
    ```python
    TESSERACT_CMD = r'<path_to_tesseract_executable>'
    ```
    For example (usually you can find it there):
    ```python
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```
2. If you encounter any problem, ensure the Tesseract-OCR executable is in your system's PATH.

   

### Ressources
 Ensure the necessary image cues are placed in the 'res' directory. It should contain the following files:
- `oui_button_cue.png` - Image cue for detecting the "Yes" button.
- `price_input_cue.png` - Image cue for detecting the price input field.
- `price_table_cue.png` - Image cue for detecting the price table.
- `quantity_1_cue.png` - Image cue for detecting the quantity 1.
- `quantity_1_cue_prefilled.png` - Image cue for detecting the quantity 1 when quantity 1 is prefilled.
- `quantity_10_cue.png` - Image cue for detecting the quantity 10.
- `quantity_10_cue_prefilled.png` - Image cue for detecting the quantity 10 when quantity 10 is prefilled.
- `quantity_100_cue.png` - Image cue for detecting the quantity 100.
- `quantity_100_cue_prefilled.png` - Image cue for detecting the quantity 100 when quantity 100 is prefilled.
- `sell_button_cue.png` - Image cue for detecting the "Sell" button.
- `sell_button_alt_cue.png` - Image cue for detecting the "Sell" button when the item is already listed.

a debug folder is provided, where screenshots will be saved if you enable debug mode in the GUI.

 ### Running the Script
 1. Run the script:
    ```bash
    python DofusAutoSeller.py
    ```
 2. The GUI will start, where you can configure your keybinds and toggle debug mode. (more features are coming soon)

 ## Usage
1. The Hotkeys will only work when the Dofus window is in focus.
2. Head to an "Hotel des Ventes" in Dofus.
3. Select an item in your inventory. 
4. Press `*` (by default) to sell the selected quantity to -1 kamas cheaper than the listed items to ensure yours appears first. 
5. Press `$` (by default) to sell the whole stack of the item, starting from the selected quantity to the lowest to sell everything (100, then 10, then 1 until gone). 
6. If you have items already listed in HdV, after selecting them you can press `*` to modify the price and list it back to update the price to -1. It works for updating multiple of the same item in the same quantity packs.
7. Avoid moving your mouse during the sell process. Your mouse will come back to its original position after the process is done.

## File Structure
````
├── DofusAutoSeller.py
├── gui.py
├── logic.py
├── res/
│   ├── debug/
├── utils/
│   ├── config.py
│   ├── constants.py
│   ├── data_classes.py
│   └── debug_utils.py
├── LICENSE
├── README.md
├── config.json
├── default_config.json
└── requirements.txt

````

## Contributing
Feel free to open issues or submit pull requests for any improvements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
