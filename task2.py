import tkinter as tk


def create_page(parent):
    page = tk.Frame(parent)

    title = tk.Label(page, text="")
    title.pack(pady=20)

    return page