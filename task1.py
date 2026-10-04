import tkinter as tk
from tkinter import filedialog 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def create_page(parent):
    page = tk.Frame(parent)

    #2-The ability to display a signal using any visualization library.
    figure = Figure(figsize=(6, 4))
    axes = figure.add_subplot(111)

    axes.set_xlabel("Sample index (n)")
    axes.set_ylabel("Amplitude")

    canvas = FigureCanvasTkAgg(figure, master=page)


    #1-Apply a function which can read a signal from txt file in this format. 
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



            axes.clear()
            axes.stem(indices, samples)
            axes.set_title("Loaded Signal")
            axes.set_xlabel("Sample index (n)")
            axes.set_ylabel("Amplitude")
            axes.grid(True)

            canvas.draw()



    #load signal button
    load_button = tk.Button(
        page,
        text="Load Signal",
        command=load_signal
    )
    load_button.pack(pady=20)


    canvas.get_tk_widget().pack(fill="both", expand=True)
    return page