import math
from decimal import Decimal
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from task3 import read_signal

def moving_average(indices, samples, window_size):
    if not isinstance(window_size, int) or isinstance(window_size, bool) or window_size < 1:
        raise ValueError("Window size must be a positive integer.")
    if window_size > len(samples):
        raise ValueError("Window size cannot exceed the number of samples.")

    output_indices, output_samples = [], []
    for start in range(len(samples) - window_size + 1):
        end = start + window_size
        window_indices = indices[start:end]
        output_indices.append(window_indices[0])
        output_samples.append(sum(samples[start:end], Decimal(0)) / window_size)
    return output_indices, output_samples


def first_derivative(indices, samples):
    output_indices, output_samples = [], []
    for position in range(1, len(samples)):
        output_indices.append(indices[position])
        output_samples.append(samples[position] - samples[position - 1])
    return output_indices, output_samples


def second_derivative(indices, samples):
    output_indices, output_samples = [], []
    for position in range(1, len(samples) - 1):
        output_indices.append(indices[position])
        output_samples.append(
            samples[position + 1] - 2 * samples[position] + samples[position - 1]
        )
    return output_indices, output_samples


def convolve(first_indices, first_samples, second_indices, second_samples):
    output = {}
    for first_index, first_sample in zip(first_indices, first_samples):
        for second_index, second_sample in zip(second_indices, second_samples):
            output_index = first_index + second_index
            output[output_index] = (
                output.get(output_index, Decimal(0)) + first_sample * second_sample
            )
    output_indices = sorted(output)
    return output_indices, [output[index] for index in output_indices]


def create_page(parent):
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    page = ttk.Frame(parent)
    signals = [None, None]
    signal_names = ["Signal 1", "Signal 2"]
    operation = tk.StringVar(value="Moving average")
    window_size = tk.StringVar(value="3")
    status = tk.StringVar(value="Load a signal to begin.")

    ttk.Label(page, text="Task 4 — Signal Operations", font=("Segoe UI", 16, "bold")).pack(
        pady=8
    )
    controls = ttk.Frame(page)
    controls.pack(fill="x", padx=10)

    def load_signal(slot):
        path = filedialog.askopenfilename(
            title=f"Choose {signal_names[slot].lower()}",
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            return
        try:
            indices, samples = read_signal(path)
            if not all(math.isfinite(float(value)) for value in samples):
                raise ValueError("Samples are too large to display.")
        except (OSError, ValueError, OverflowError) as error:
            messagebox.showerror("Cannot load signal", str(error), parent=page)
            return
        signals[slot] = (indices, samples)
        signal_names[slot] = Path(path).name
        load_buttons[slot].configure(text=f"{slot + 1}: {Path(path).name}")
        status.set(f"Loaded {Path(path).name} ({len(samples)} samples).")

    load_buttons = []
    for slot in range(2):
        button = ttk.Button(controls, text=f"Load Signal {slot + 1}")
        button.configure(command=lambda index=slot: load_signal(index))
        button.pack(side="left", padx=4)
        load_buttons.append(button)

    ttk.Combobox(
        controls,
        textvariable=operation,
        values=("Moving average", "First derivative", "Second derivative", "Convolution"),
        state="readonly",
        width=19,
    ).pack(side="left", padx=4)
    ttk.Label(controls, text="Window size").pack(side="left", padx=(6, 2))
    ttk.Entry(controls, textvariable=window_size, width=6).pack(side="left", padx=2)

    figure = Figure(figsize=(6, 3.5), constrained_layout=True)
    axes = figure.add_subplot(111)
    canvas = FigureCanvasTkAgg(figure, master=page)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

    table_frame = ttk.Frame(page)
    table_frame.pack(fill="x", padx=10, pady=5)
    table = ttk.Treeview(table_frame, columns=("Index", "Value"), show="headings", height=6)
    table.heading("Index", text="Index (n)")
    table.heading("Value", text="Output")
    table.column("Index", width=100, anchor="center")
    table.column("Value", width=180, anchor="center")
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    table.pack(side="left", fill="x", expand=True)
    ttk.Label(page, textvariable=status, wraplength=700).pack(fill="x", padx=10, pady=5)

    def run_operation():
        selected_operation = operation.get()
        try:
            if selected_operation == "Convolution":
                if signals[0] is None or signals[1] is None:
                    raise ValueError("Load both signals before convolving.")
                output_indices, output_samples = convolve(*signals[0], *signals[1])
                title = "Linear convolution"
            else:
                if signals[0] is None:
                    raise ValueError("Load Signal 1 before processing.")
                indices, samples = signals[0]
                if selected_operation == "Moving average":
                    size = int(window_size.get())
                    output_indices, output_samples = moving_average(indices, samples, size)
                    title = f"Moving average (window size {size})"
                elif selected_operation == "First derivative":
                    output_indices, output_samples = first_derivative(indices, samples)
                    title = "First derivative"
                else:
                    output_indices, output_samples = second_derivative(indices, samples)
                    title = "Second derivative"
            if not all(math.isfinite(float(value)) for value in output_samples):
                raise ValueError("Output values are too large to display.")
        except (ValueError, OverflowError) as error:
            messagebox.showerror("Cannot process signal", str(error), parent=page)
            return

        axes.clear()
        axes.set_title(title)
        axes.set_xlabel("Sample index (n)")
        axes.set_ylabel("Amplitude")
        axes.grid(True)
        if output_indices:
            axes.stem(output_indices, [float(value) for value in output_samples])
        canvas.draw_idle()

        table.delete(*table.get_children())
        for index, value in zip(output_indices, output_samples):
            table.insert("", "end", values=(index, f"{value:.8g}"))
        status.set(
            f"{title}: {len(output_samples)} output sample"
            f"{'' if len(output_samples) == 1 else 's'}."
            if output_samples
            else f"{title}: no valid output samples for the loaded indices."
        )

    ttk.Button(controls, text="Run", command=run_operation).pack(side="left", padx=4)
    return page
