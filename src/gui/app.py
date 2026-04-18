import tkinter as tk
from tkinter import messagebox
import logging
import threading
import os

from src.utils.config_parser import load_config
from src.core.orchestrator import Orchestrator

class AmazonScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Amazon Intelligence Pro")
        self.root.geometry("460x420")
        self.logger = logging.getLogger(__name__)

        # Ensure all data directories exist on startup
        self._initialize_environment()

        self.config = load_config()
        self.orchestrator = Orchestrator(self.config)

        self._setup_widgets()

    def _initialize_environment(self):
        """Creates required directories to prevent FileNotFoundError."""
        required_dirs = ['data/processed', 'data/exports', 'config']
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)
            self.logger.info(f"Directory verified: {directory}")

    def _setup_widgets(self):
        """Builds a professional UI layout."""
        # Keyword Search Section
        tk.Label(self.root, text="Search Keyword:", font=("Arial", 11, "bold")).pack(pady=(20, 5))
        self.keyword_entry = tk.Entry(self.root, width=35, font=("Arial", 12))
        self.keyword_entry.pack(pady=5)

        # Pagination Control
        tk.Label(self.root, text="Pages to Scrape (1-50):", font=("Arial", 10)).pack(pady=(12, 2))
        self.page_spinbox = tk.Spinbox(self.root, from_=1, to=50, width=6, font=("Arial", 12))
        self.page_spinbox.pack(pady=5)
        self.page_spinbox.delete(0, tk.END)
        self.page_spinbox.insert(0, "5")

        # Price Range Frame
        price_frame = tk.Frame(self.root)
        price_frame.pack(pady=15)

        tk.Label(price_frame, text="Min (TL):").grid(row=0, column=0, padx=5)
        self.min_p_entry = tk.Entry(price_frame, width=12)
        self.min_p_entry.insert(0, "0")
        self.min_p_entry.grid(row=0, column=1, padx=5)

        tk.Label(price_frame, text="Max (TL):").grid(row=0, column=2, padx=5)
        self.max_p_entry = tk.Entry(price_frame, width=12)
        self.max_p_entry.insert(0, "500.000")
        self.max_p_entry.grid(row=0, column=3, padx=5)

        # Event Binding for Smart Formatting
        self.min_p_entry.bind('<KeyRelease>', self.format_price_input)
        self.max_p_entry.bind('<KeyRelease>', self.format_price_input)

        # Execution Button
        self.start_btn = tk.Button(
            self.root, text="🚀 Launch Intelligence Engine",
            command=self.start_scraping_thread,
            bg="#2E86C1", fg="white", font=("Arial", 11, "bold"),
            padx=20, pady=10
        )
        self.start_btn.pack(pady=20)

        # Status Display
        self.status_label = tk.Label(self.root, text="System ready for analysis", fg="gray")
        self.status_label.pack(side=tk.BOTTOM, pady=15)

    def format_price_input(self, event):
        """Formats price with dots while intelligently managing cursor position."""
        if event.keysym in ('Left', 'Right', 'Up', 'Down', 'BackSpace', 'Delete'):
            return

        widget = event.widget
        current_pos = widget.index(tk.INSERT)
        raw_content = widget.get().replace('.', '')

        if raw_content.isdigit():
            formatted = "{:,}".format(int(raw_content)).replace(',', '.')
            widget.delete(0, tk.END)
            widget.insert(0, formatted)
            
            # Calculate new cursor position to prevent jumping to the end
            new_pos = current_pos + (len(formatted) - len(widget.get()))
            widget.icursor(new_pos if new_pos >= 0 else tk.END)

    def start_scraping_thread(self):
        """Input validation and background thread dispatch."""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("Input Error", "Keyword is required!")
            return

        try:
            # Parse inputs
            pages = int(self.page_spinbox.get())
            min_p = float(self.min_p_entry.get().replace('.', ''))
            max_p = float(self.max_p_entry.get().replace('.', ''))

            # Basic logic checks
            if min_p > max_p:
                messagebox.showerror("Logic Error", "Min Price cannot exceed Max Price.")
                return

            # UI Feedback
            self.start_btn.config(state=tk.DISABLED)
            self.status_label.config(text=f"Analyzing '{keyword}'... Please wait.", fg="#2E86C1")

            # Threaded execution
            threading.Thread(
                target=self.run_orchestrator,
                args=(keyword, pages, min_p, max_p),
                daemon=True
            ).start()

        except ValueError:
            messagebox.showwarning("Format Error", "Please provide valid numerical inputs.")

    def run_orchestrator(self, keyword, pages, min_p, max_p):
        """Background task handler with thread-safe UI callbacks."""
        try:
            results = self.orchestrator.run(keyword, pages=pages, min_p=min_p, max_p=max_p)
            self.root.after(0, lambda: self._handle_completion(results, keyword))
        except Exception as e:
            self.logger.error(f"Execution Error: {e}")
            self.root.after(0, lambda: messagebox.showerror("System Error", str(e)))
        finally:
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))

    def _handle_completion(self, results, keyword):
        """Finalize UI after successful run."""
        if results:
            self.status_label.config(text=f"Mission successful: {len(results)} items analyzed.", fg="green")
            messagebox.showinfo("Success", f"Market analysis for '{keyword}' is complete!")
        else:
            self.status_label.config(text="No data found for this range.", fg="orange")
            messagebox.showwarning("No Results", "Try broadening your price filters.")