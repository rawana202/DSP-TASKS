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

    signals=[]


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
                index, value = line.split()

                indices.append(int(index))
                samples.append(float(value))

            signals.append((indices,samples))
            draw_signal(indices,samples)


    def draw_signal(indices,samples):
            axes.clear()
            axes.stem(indices, samples)
            axes.set_title("Loaded Signal")
            axes.set_xlabel("Sample index (n)")
            axes.set_ylabel("Amplitude")
            axes.grid(True)

            canvas.draw()

    def add_signals():
        if len(signals) < 2:
            print("Load at least two signals")
            return

        result = {}

        for indices, samples in signals:
            for index, value in zip(indices, samples):
                result[index] = result.get(index, 0) + value

        result_indices = sorted(result)
        result_samples = [
            result[index] for index in result_indices
        ]
        draw_signal(result_indices,result_samples)
        return result_indices,result_samples


    def multiply_signal():
        if not signals:
            print("Load a signal first")
            return

        try:
            constant = float(constant_entry.get())
        except ValueError:
            print("Enter a valid number")
            return

        indices, samples = signals[0]

        result_samples = [
            value * constant for value in samples
        ]

        axes.clear()
        axes.stem(indices, result_samples)
        axes.set_title(f"Signal multiplied by {constant}")
        axes.set_xlabel("Sample index (n)")
        axes.set_ylabel("Amplitude")
        axes.grid(True)

        canvas.draw()

    def sub_signals():
        if len(signals) < 2:
            print("Load at least two signals")
            return

        result = {}

        indices, samples = signals[0]

        for index, value in zip(indices, samples):
            result[index] = value

        for indices, samples in signals[1:]:
            for index, value in zip(indices, samples):
                result[index] = result.get(index, 0) - value

        result_indices = sorted(result)
        result_samples = [
            result[index] for index in result_indices
        ]

        draw_signal(result_indices, result_samples)

    def delay_or_advance():
        if len(signals) != 1:
            print("Need exactly one signal")
            return
        try:
            constant = float(shift_entry.get())
        except ValueError:
            print("Enter a valid number")
            return

        indices, samples = signals[0]
        result = {}
        for index, value in zip(indices, samples):
            result[index - float(shift_entry.get())] = value

        result_indices = sorted(result)
        result_samples = [
            result[index] for index in result_indices
        ]
        draw_signal(result_indices, result_samples)

    def reverse_signal():
        if len(signals) != 1:
            print("Need exactly one signal")
            return

        indices, samples = signals[0]
        result = {}
        for index, value in zip(indices, samples):
            result[-index] = value

        result_indices = sorted(result)
        result_samples = [
            result[index] for index in result_indices
        ]
        draw_signal(result_indices, result_samples)


    #load signal button
    load_button = tk.Button(
        page,
        text="Load Signal",
        command=load_signal
    )
    load_button.pack(pady=20)

    add_button = tk.Button(
        page,
        text="Add Signals",
        command=add_signals
    )
    add_button.pack(pady=10)

    multiply_button = tk.Button(
        page,
        text="Multiply Signal",
        command=multiply_signal
    )
    multiply_button.pack(pady=10)

    tk.Label(page, text="Multiplication constant").pack()
    constant_entry = tk.Entry(page)
    constant_entry.pack(pady=5)

    sub_button = tk.Button(
        page,
        text="Subtract Signals",
        command=sub_signals
    )
    sub_button.pack(pady=10)

    shift_button = tk.Button(
        page,
        text="Delay/Advance Signal",
        command=delay_or_advance
    )
    shift_button.pack(pady=10)

    tk.Label(page, text="Shift constant").pack()
    shift_entry = tk.Entry(page)
    shift_entry.pack(pady=5)

    load_button = tk.Button(
        page,
        text="Reverse Signal",
        command=reverse_signal
    )
    load_button.pack(pady=20)

    canvas.get_tk_widget().pack(fill="both", expand=True)
    return page