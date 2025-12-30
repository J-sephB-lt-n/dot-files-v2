#!/usr/bin/env python3
"""
Display a resizable, modal popup message using tkinter.

Example usage:
$ popup_msg -m 'Hello World'

Place this script (without .py) in /usr/local/bin/ to make this script globally available
(might also need `sudo chmod +x /usr/local/bin/popup_msg`
"""

import argparse
import tkinter as tk


def popup(message: str, title: str, width: int, height: int) -> None:
    """
    Show a modal popup window.

    Args:
        message: Message text to display.
        title:   Window title.
        width:   Window width in pixels.
        height:  Window height in pixels.
    """
    root = tk.Tk()
    root.title(title)
    root.geometry(f"{width}x{height}")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")

    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(expand=True, fill="both")

    label = tk.Label(
        frame,
        text=message,
        wraplength=width - 40,
        font=("TkDefaultFont", 14),
        justify="center",
    )
    label.pack(expand=True)

    btn = tk.Button(frame, text="OK", command=root.destroy)
    btn.pack(pady=(15, 0))

    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Show a popup message")
    parser.add_argument("-m", "--message", required=True, help="Message to display")
    parser.add_argument("-t", "--title", default="Reminder", help="Popup title")
    parser.add_argument("--width", type=int, default=600, help="Window width (px)")
    parser.add_argument("--height", type=int, default=300, help="Window height (px)")

    args = parser.parse_args()
    popup(args.message, args.title, args.width, args.height)


if __name__ == "__main__":
    main()
