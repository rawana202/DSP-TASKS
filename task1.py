import tkinter as tk
from tkinter import filedialog 


def create_page(parent):
    page = tk.Frame(parent)


    def load_signal():
        file_path = filedialog.askopenfilename(
            title="Choose a signal",
            filetypes=[("Text files", "*.txt")]
        )

        
        if not file_path:
            return
        with open (file_path,"r") as file:
            lines = file.read().splitlines()
            number_of_samples = int(lines[2])

            indices = []
            samples = []

            for line in lines[3:3 + number_of_samples]:
                index, value = line.split(' ')

                indices.append(int(index))
                samples.append(float(value))

            print("Indices:", indices)
            print("Samples:", samples)


        status_label.config(
            text=f"Loaded {len(samples)} samples"
        )



    load_button = tk.Button(
        page,
        text="Load Signal",
        command=load_signal
    )
    load_button.pack(pady=20)

    status_label = tk.Label(page, text="No signal loaded")
    status_label.pack()


    title = tk.Label(page, text="")
    title.pack(pady=20)

    return page