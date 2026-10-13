import math
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


MAX_SAMPLES = 100000


def _generate_signal(waveform, amplitude, phase, analog_frequency, sampling_frequency):
    """Generate one second of continuous and sampled sinusoidal data."""
    values = (amplitude, phase, analog_frequency, sampling_frequency)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("All parameters must be finite numbers.")
    if analog_frequency <= 0:
        raise ValueError("Analog frequency must be greater than zero.")
    if sampling_frequency <= 0:
        raise ValueError("Sampling frequency must be greater than zero.")
    if sampling_frequency <= 2 * analog_frequency:
        raise ValueError(
            "Sampling frequency must be greater than twice the analog frequency "
            f"({2 * analog_frequency:g} Hz) to satisfy the sampling theorem."
        )
    if sampling_frequency > MAX_SAMPLES:
        raise ValueError(
            f"Sampling frequency must not exceed {MAX_SAMPLES:,} Hz."
        )
    if waveform not in ("Sine", "Cosine"):
        raise ValueError(f"Unsupported waveform: {waveform}")

    sample_count = math.ceil(sampling_frequency)
    continuous_count = min(
        max(1000, math.ceil(100 * analog_frequency)),
        MAX_SAMPLES,
    )
    function = math.sin if waveform == "Sine" else math.cos

    def value_at(time):
        return amplitude * function(
            2 * math.pi * analog_frequency * time + phase
        )

    continuous_times = [index / (continuous_count - 1) for index in range(continuous_count)]
    continuous_values = [value_at(time) for time in continuous_times]
    sample_indices = list(range(sample_count))
    sample_times = [index / sampling_frequency for index in sample_indices]
    sample_values = [value_at(time) for time in sample_times]

    return {
        "waveform": waveform,
        "continuous_times": continuous_times,
        "continuous_values": continuous_values,
        "sample_indices": sample_indices,
        "sample_times": sample_times,
        "sample_values": sample_values,
    }


def create_page(parent):
    page = ttk.Frame(parent)
    page.grid_rowconfigure(1, weight=1)
    page.grid_columnconfigure(0, weight=1)

    def generate_signal(waveform):
        try:
            amplitude = float(amplitude_entry.get())
            phase = float(phase_entry.get())
            analog_frequency = float(frequency_entry.get())
            sampling_frequency = float(sampling_entry.get())
            signal = _generate_signal(
                waveform,
                amplitude,
                phase,
                analog_frequency,
                sampling_frequency,
            )
        except ValueError as error:
            status_label.config(text=str(error))
            return

        previous_display = list(displayed_names)
        signal_number = waveform_counts[waveform] + 1
        waveform_counts[waveform] = signal_number
        name = f"{waveform} {signal_number}"
        signals[name] = signal
        signal_names.append(name)
        signal_list.insert(tk.END, name)

        displayed_names[:] = (
            previous_display[:1] + [name] if len(previous_display) == 1 else [name]
        )
        update_list_selection()
        draw_signals()
        status_label.config(
            text=f"Generated {name}. Select up to two signals to compare."
        )

    heading = ttk.Label(
        page, text="Signal Processing", font=("TkDefaultFont", 16, "bold")
    )
    heading.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

    workspace = ttk.Frame(page)
    workspace.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
    workspace.grid_rowconfigure(1, weight=1)
    workspace.grid_columnconfigure(0, weight=1)
    workspace.grid_columnconfigure(2, weight=1)

    parameters = ttk.LabelFrame(workspace, text="Sinusoid parameters")
    parameters.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))

    amplitude_entry = ttk.Entry(parameters, width=10)
    phase_entry = ttk.Entry(parameters, width=10)
    frequency_entry = ttk.Entry(parameters, width=10)
    sampling_entry = ttk.Entry(parameters, width=10)
    parameter_fields = (
        ("Amplitude A", amplitude_entry, "1"),
        ("Phase θ (radians)", phase_entry, "0"),
        ("Analog frequency (Hz)", frequency_entry, "5"),
        ("Sampling frequency (Hz)", sampling_entry, "50"),
    )
    for column, (label, entry, default) in enumerate(parameter_fields):
        ttk.Label(parameters, text=label).grid(
            row=0, column=column, sticky="w", padx=8, pady=(8, 2)
        )
        entry.grid(row=1, column=column, sticky="ew", padx=8, pady=(0, 8))
        entry.insert(0, default)

    generation_panel = ttk.LabelFrame(workspace, text="Signal Generation")
    generation_panel.grid(row=0, column=1, sticky="ns", pady=(0, 10))
    ttk.Button(
        generation_panel,
        text="Sine wave",
        command=lambda: generate_signal("Sine"),
    ).pack(fill="x", padx=8, pady=(8, 4))
    ttk.Button(
        generation_panel,
        text="Cosine wave",
        command=lambda: generate_signal("Cosine"),
    ).pack(fill="x", padx=8, pady=(4, 8))

    signals = {}
    signal_names = []
    displayed_names = []
    waveform_counts = {"Sine": 0, "Cosine": 0}

    signal_panel = ttk.LabelFrame(workspace, text="Generated signals")
    signal_panel.grid(row=1, column=0, sticky="ns", padx=(0, 10))
    signal_panel.grid_rowconfigure(0, weight=1)

    signal_list = tk.Listbox(
        signal_panel,
        selectmode=tk.EXTENDED,
        exportselection=False,
        width=23,
        height=12,
    )
    signal_list.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
    signal_scrollbar = ttk.Scrollbar(
        signal_panel, orient="vertical", command=signal_list.yview
    )
    signal_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
    signal_list.configure(yscrollcommand=signal_scrollbar.set)

    plot_panel = ttk.Frame(workspace)
    plot_panel.grid(row=1, column=1, columnspan=2, sticky="nsew")
    plot_panel.grid_rowconfigure(0, weight=1)
    plot_panel.grid_columnconfigure(0, weight=1)

    figure = Figure(figsize=(6, 4))
    axes = figure.add_subplot(111)
    canvas = FigureCanvasTkAgg(figure, master=plot_panel)
    canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    status_label = ttk.Label(workspace, text="", anchor="w", wraplength=700)
    status_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    representation_var = tk.StringVar(value="Continuous")
    displayed_label = ttk.LabelFrame(plot_panel, text="Display representation")
    displayed_label.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def draw_signals():
        axes.clear()
        representation = representation_var.get()
        for signal_index, name in enumerate(displayed_names):
            signal = signals[name]
            if representation == "Continuous":
                axes.plot(
                    signal["continuous_times"],
                    signal["continuous_values"],
                    label=name,
                )
            else:
                stem = axes.stem(
                    signal["sample_times"],
                    signal["sample_values"],
                    label=name,
                )
                color = f"C{signal_index}"
                stem.markerline.set_color(color)
                stem.stemlines.set_color(color)
        axes.set_title(
            "Signal comparison" if displayed_names else "Generate a signal to begin"
        )
        axes.set_xlabel("Time (seconds)")
        axes.set_ylabel("Amplitude")
        axes.grid(True)
        if displayed_names:
            axes.legend()
        canvas.draw()

    def update_list_selection():
        signal_list.selection_clear(0, tk.END)
        for index, name in enumerate(signal_names):
            if name in displayed_names:
                signal_list.selection_set(index)

    def show_selected():
        names = [
            signal_names[index] for index in signal_list.curselection()
        ]
        if not names:
            status_label.config(text="Select one or two signals to display.")
            return
        if len(names) > 2:
            status_label.config(text="Select no more than two signals at a time.")
            return
        displayed_names[:] = names
        draw_signals()
        status_label.config(
            text=f"Displaying {len(names)} signal{'s' if len(names) != 1 else ''}."
        )

    def remove_selected():
        names = [
            signal_names[index] for index in signal_list.curselection()
        ]
        for name in names:
            del signals[name]
            signal_names.remove(name)
            if name in displayed_names:
                displayed_names.remove(name)
        for name in names:
            signal_list.delete(signal_list.get(0, tk.END).index(name))
        draw_signals()
        status_label.config(
            text=f"Removed {len(names)} signal{'s' if len(names) != 1 else ''}."
            if names
            else "Select signals to remove."
        )

    ttk.Button(signal_panel, text="Display selected", command=show_selected).grid(
        row=1, column=0, sticky="ew", padx=(8, 4), pady=(0, 6)
    )
    ttk.Button(signal_panel, text="Remove selected", command=remove_selected).grid(
        row=1, column=1, sticky="ew", padx=(4, 8), pady=(0, 6)
    )

    ttk.Label(displayed_label, text="View as:").pack(side="left", padx=(8, 4))
    for representation in ("Continuous", "Discrete"):
        ttk.Radiobutton(
            displayed_label,
            text=representation,
            value=representation,
            variable=representation_var,
            command=draw_signals,
        ).pack(side="left", padx=6, pady=4)

    draw_signals()
    return page
