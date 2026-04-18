import tkinter as tk

from src.gui.app import AmazonScraperGUI
from src.utils.logger import setup_global_logger


def main():
    setup_global_logger()
    root = tk.Tk()
    app = AmazonScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()