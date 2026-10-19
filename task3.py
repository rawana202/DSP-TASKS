import math
from decimal import Decimal, ROUND_CEILING
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from QuanTest1 import QuantizationTest1
from QuanTest2 import QuantizationTest2

def read_signal(path):
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    for header in (1, 3):
        try:
            count = int(lines[header - 1])
            if count <= 0 or len(lines) != header + count:
                continue
            indices, samples = [], []
            for line in lines[header:]:
                index, value = line.split()
                sample = Decimal(value)
                if not sample.is_finite():
                    raise ValueError()
                indices.append(int(index))
                samples.append(sample)
            return indices, samples
        except (ValueError, IndexError, ArithmeticError):
            continue
    raise ValueError("Invalid signal file. Expected a sample count and index/value pairs.")


def quantize(samples, levels):
    if not samples or levels < 1:
        raise ValueError("Load a signal and enter a positive number of levels.")
    values = [Decimal(str(value)) for value in samples]
    if not all(value.is_finite() for value in values):
        raise ValueError("Samples must be finite numbers.")
    low, high = min(values), max(values)
    delta = (high - low) / levels
    bits = max(1, (levels - 1).bit_length())
    intervals, encoded, quantized, errors = [], [], [], []
    for value in values:
        # A boundary belongs to the lower interval, matching the supplied tests.
        slot = 0 if delta == 0 else int(((value - low) / delta).to_integral_value(rounding=ROUND_CEILING)) - 1
        slot = max(0, min(levels - 1, slot))
        midpoint = low if delta == 0 else low + (Decimal(slot) + Decimal("0.5")) * delta
        intervals.append(slot + 1)
        encoded.append(format(slot, f"0{bits}b"))
        quantized.append(float(midpoint))
        errors.append(float(midpoint - value))
    return intervals, encoded, quantized, errors


def create_page(parent):
    # Imported here so the calculation functions also work without a GUI backend.
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    page = ttk.Frame(parent)
    indices, samples = [], []
    mode = tk.StringVar(value="Bits")
    amount = tk.StringVar(value="3")
    status = tk.StringVar(value="Load a signal to begin.")

    ttk.Label(page, text="Task 3 — Quantization", font=("Segoe UI", 16, "bold")).pack(pady=8)
    controls = ttk.Frame(page)
    controls.pack(fill="x", padx=10)
    ttk.Button(controls, text="Load Signal", command=lambda: load_signal()).pack(side="left", padx=4)
    ttk.Combobox(controls, textvariable=mode, values=["Bits", "Levels"], state="readonly", width=8).pack(side="left", padx=4)
    ttk.Entry(controls, textvariable=amount, width=8).pack(side="left", padx=4)
    run_button = ttk.Button(controls, text="Quantize", command=lambda: run_quantization(), state="disabled")
    run_button.pack(side="left", padx=4)
    ttk.Label(page, textvariable=status, wraplength=580).pack(fill="x", padx=10, pady=5)

    figure = Figure(figsize=(6, 4), constrained_layout=True)
    signal_axes, error_axes = figure.subplots(2, 1)
    canvas = FigureCanvasTkAgg(figure, master=page)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    table_frame = ttk.Frame(page)
    table_frame.pack(fill="x", padx=10, pady=8)
    columns = ("Index", "Original", "Interval", "Encoded", "Quantized", "Error")
    table = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
    for column in columns:
        table.heading(column, text=column)
        table.column(column, width=80, minwidth=45, anchor="center")
    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)

    def reset_axes():
        signal_axes.clear()
        error_axes.clear()
        signal_axes.set_title("Original and quantized signal")
        signal_axes.set_ylabel("Amplitude")
        error_axes.set_title("Error = quantized - original")
        error_axes.set_ylabel("Error")
        error_axes.set_xlabel("Sample index (n)")
        signal_axes.grid(True)
        error_axes.grid(True)

    def load_signal():
        nonlocal indices, samples
        path = filedialog.askopenfilename(title="Choose signal", filetypes=[("Text files", "*.txt")])
        if not path:
            return
        try:
            new_indices, new_samples = read_signal(path)
            if not all(math.isfinite(float(value)) for value in new_samples):
                raise ValueError("Samples are too large to display.")
        except (OSError, ValueError, OverflowError) as error:
            messagebox.showerror("Cannot load signal", str(error), parent=page)
            return
        indices, samples = new_indices, new_samples
        table.delete(*table.get_children())
        reset_axes()
        signal_axes.stem(indices, [float(value) for value in samples], label="Original")
        signal_axes.legend()
        canvas.draw_idle()
        status.set(f"{Path(path).name}: {len(samples)} samples loaded.")
        run_button.configure(state="normal")

    def run_quantization():
        try:
            number = int(amount.get())
            if number < 1:
                raise ValueError("Enter a positive integer.")
            if mode.get() == "Bits":
                if number > 64:
                    raise ValueError("Please use at most 64 bits.")
                levels = 2 ** number
            else:
                levels = number
            intervals, encoded, values, errors = quantize(samples, levels)
        except ValueError as error:
            messagebox.showerror("Check input", str(error), parent=page)
            return
        reset_axes()
        signal_axes.plot(indices, [float(value) for value in samples], "o--", alpha=.6, label="Original")
        signal_axes.stem(indices, values, linefmt="C1-", markerfmt="C1o", basefmt=" ", label="Quantized")
        signal_axes.legend()
        error_axes.stem(indices, errors)
        canvas.draw_idle()
        table.delete(*table.get_children())
        for n, original, interval, code, value, error in zip(indices, samples, intervals, encoded, values, errors):
            table.insert("", "end", values=(n, str(original), interval, code, f"{value:.6g}", f"{error:.6g}"))
        width = len(encoded[0])
        if mode.get() == "Bits":
            width = number
        # For one level the single code is 0; otherwise width is ceil(log2(levels)).
        status.set(f"{levels} levels | {width} bits per sample | Interval numbering starts at 1; encoding starts at 0.")

    reset_axes()
    return page
