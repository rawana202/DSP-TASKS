import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


OPERATIONS = (
    "Add selected signals",
    "Subtract selected signals",
    "Multiply by a constant",
    "Delay / advance",
    "Reverse",
)


def _ordered_selection(signal_names, previous_order, selected_indices):
    selected = {signal_names[index] for index in selected_indices}
    order = [name for name in previous_order if name in selected]
    order.extend(
        signal_names[index]
        for index in selected_indices
        if signal_names[index] not in order
    )
    return order


def _apply_operation(signals, operation, parameter=None):
    """Apply an operation to (indices, samples) signals and return one result."""
    signal_maps = [dict(zip(indices, samples)) for indices, samples in signals]

    if operation == "Add selected signals":
        result = {}
        for signal in signal_maps:
            for index, value in signal.items():
                result[index] = result.get(index, 0) + value
    elif operation == "Subtract selected signals":
        result = dict(signal_maps[0])
        for signal in signal_maps[1:]:
            for index, value in signal.items():
                result[index] = result.get(index, 0) - value
    elif operation == "Multiply by a constant":
        result = {
            index: value * parameter
            for index, value in signal_maps[0].items()
        }
    elif operation == "Delay / advance":
        result = {
            index + parameter: value
            for index, value in signal_maps[0].items()
        }
    elif operation == "Reverse":
        result = {
            -index: value
            for index, value in signal_maps[0].items()
        }
    else:
        raise ValueError(f"Unknown operation: {operation}")

    indices = sorted(result)
    return indices, [result[index] for index in indices]


def create_page(parent):
    page = tk.Frame(parent)
    page.grid_rowconfigure(1, weight=1)
    page.grid_columnconfigure(0, weight=1)

    signals = {}
    signal_names = []
    selection_order = []
    current_output = None
    parameter_entry = None
    saved_output_count = 0

    heading = ttk.Label(page, text="Signal Workbench", font=("TkDefaultFont", 16, "bold"))
    heading.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

    workspace = ttk.Frame(page)
    workspace.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
    workspace.grid_rowconfigure(0, weight=1)
    workspace.grid_columnconfigure(1, weight=1)

    library = ttk.LabelFrame(workspace, text="Signals")
    library.grid(row=0, column=0, sticky="ns", padx=(0, 10))
    library.grid_rowconfigure(0, weight=1)

    signal_list = tk.Listbox(
        library,
        selectmode=tk.EXTENDED,
        exportselection=False,
        width=25,
        height=12,
    )
    signal_list.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
    signal_scrollbar = ttk.Scrollbar(
        library, orient="vertical", command=signal_list.yview
    )
    signal_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
    signal_list.configure(yscrollcommand=signal_scrollbar.set)
    ttk.Label(library, text="Ctrl/Shift-click to select multiple").grid(
        row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8)
    )
    ttk.Label(library, text="Operation order (first to last)").grid(
        row=4, column=0, columnspan=2, sticky="w", padx=8
    )
    ordered_list = tk.Listbox(library, exportselection=False, width=25, height=5)
    ordered_list.grid(
        row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 4)
    )
    order_buttons = ttk.Frame(library)
    order_buttons.grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
    ttk.Button(
        order_buttons,
        text="Move up",
        command=lambda: move_ordered_signal(-1),
    ).pack(side="left", expand=True, fill="x", padx=(0, 3))
    ttk.Button(
        order_buttons,
        text="Move down",
        command=lambda: move_ordered_signal(1),
    ).pack(side="left", expand=True, fill="x", padx=(3, 0))

    def selected_names():
        return list(selection_order)

    def refresh_ordered_selection():
        ordered_list.delete(0, tk.END)
        for name in selection_order:
            ordered_list.insert(tk.END, name)

    def sync_selection_order(_event=None):
        selection_order[:] = _ordered_selection(
            signal_names,
            selection_order,
            signal_list.curselection(),
        )
        refresh_ordered_selection()
        update_status()

    def set_status(message):
        status_label.config(text=message)

    def update_status(_event=None):
        count = len(selected_names())
        operation = operation_var.get()
        if operation in ("Add selected signals", "Subtract selected signals"):
            requirement = "Select at least 2 signals."
            if operation == "Subtract selected signals":
                requirement += " First in the ordered selection minus the rest."
        else:
            requirement = "Select exactly 1 signal."
        set_status(f"{count} selected. {requirement}")

    def insert_signal(name, signal):
        unique_name = name
        suffix = 2
        while unique_name in signals:
            unique_name = f"{name} ({suffix})"
            suffix += 1
        signals[unique_name] = (list(signal[0]), list(signal[1]))
        signal_names.append(unique_name)
        signal_list.insert(tk.END, unique_name)
        return unique_name

    def load_signal():
        file_path = filedialog.askopenfilename(
            title="Choose a signal",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as signal_file:
                lines = signal_file.read().splitlines()
            number_of_samples = int(lines[2])
            if number_of_samples < 0 or len(lines) < 3 + number_of_samples:
                raise ValueError("The sample count does not match the file contents.")

            indices = []
            samples = []
            for line_number, line in enumerate(
                lines[3 : 3 + number_of_samples], start=4
            ):
                parts = line.split()
                if len(parts) != 2:
                    raise ValueError(
                        f"Expected an index and value on line {line_number}."
                    )
                indices.append(int(parts[0]))
                samples.append(float(parts[1]))
        except (OSError, ValueError, IndexError) as error:
            messagebox.showerror("Could not load signal", str(error), parent=page)
            return

        name = os.path.splitext(os.path.basename(file_path))[0]
        insert_signal(name, (indices, samples))
        update_status()

    def remove_selected():
        indices_to_remove = list(signal_list.curselection())
        for index in reversed(indices_to_remove):
            name = signal_names.pop(index)
            del signals[name]
            signal_list.delete(index)
            if name in selection_order:
                selection_order.remove(name)
        refresh_ordered_selection()
        update_status()

    def deselect_signals():
        for index in signal_list.curselection():
            signal_list.selection_clear(index)
        selection_order.clear()
        refresh_ordered_selection()
        update_status()

    def move_ordered_signal(direction):
        selected = ordered_list.curselection()
        if not selected:
            set_status("Select a signal in the ordered list, then move it.")
            return
        index = selected[0]
        destination = index + direction
        if destination < 0 or destination >= len(selection_order):
            return
        selection_order[index], selection_order[destination] = (
            selection_order[destination],
            selection_order[index],
        )
        refresh_ordered_selection()
        ordered_list.selection_set(destination)
        ordered_list.activate(destination)
        update_status()

    ttk.Button(library, text="Load signal", command=load_signal).grid(
        row=1, column=0, sticky="ew", padx=(8, 4), pady=(0, 6)
    )
    ttk.Button(library, text="Remove selected", command=remove_selected).grid(
        row=1, column=1, sticky="ew", padx=(4, 8), pady=(0, 6)
    )
    ttk.Button(library, text="Deselect", command=deselect_signals).grid(
        row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8)
    )
    signal_list.bind("<<ListboxSelect>>", sync_selection_order)

    work_area = ttk.Frame(workspace)
    work_area.grid(row=0, column=1, sticky="nsew")
    work_area.grid_rowconfigure(2, weight=1)
    work_area.grid_columnconfigure(0, weight=1)

    controls = ttk.LabelFrame(work_area, text="Operation")
    controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    controls.grid_columnconfigure(1, weight=1)

    ttk.Label(controls, text="Choose operation").grid(
        row=0, column=0, sticky="w", padx=8, pady=8
    )
    operation_var = tk.StringVar(value=OPERATIONS[0])
    operation_menu = ttk.Combobox(
        controls,
        textvariable=operation_var,
        values=OPERATIONS,
        state="readonly",
    )
    operation_menu.grid(row=0, column=1, sticky="ew", padx=8, pady=8)

    parameter_frame = ttk.Frame(controls)
    parameter_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
    parameter_frame.grid_columnconfigure(1, weight=1)

    def update_operation_controls(_event=None):
        nonlocal parameter_entry
        for child in parameter_frame.winfo_children():
            child.destroy()
        parameter_entry = None

        if operation_var.get() == "Multiply by a constant":
            label = "Multiplier"
        elif operation_var.get() == "Delay / advance":
            label = "Shift (positive delays)"
        else:
            label = None

        if label is not None:
            ttk.Label(parameter_frame, text=label).grid(
                row=0, column=0, sticky="w", padx=8, pady=(0, 8)
            )
            parameter_entry = ttk.Entry(parameter_frame)
            parameter_entry.grid(
                row=0, column=1, sticky="ew", padx=8, pady=(0, 8)
            )
        update_status()

    operation_menu.bind("<<ComboboxSelected>>", update_operation_controls)

    status_label = ttk.Label(work_area, text="", anchor="w")
    status_label.grid(row=1, column=0, sticky="ew", pady=(0, 6))

    figure = Figure(figsize=(6, 4))
    axes = figure.add_subplot(111)
    axes.set_title("Output signal")
    axes.set_xlabel("Sample index (n)")
    axes.set_ylabel("Amplitude")
    axes.grid(True)
    canvas = FigureCanvasTkAgg(figure, master=work_area)
    canvas.get_tk_widget().grid(row=2, column=0, sticky="nsew")

    save_frame = ttk.LabelFrame(work_area, text="Save current output to Signals")
    save_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
    save_frame.grid_columnconfigure(0, weight=1)
    save_name_entry = ttk.Entry(save_frame)
    save_name_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
    save_name_entry.insert(0, "Output")

    def save_output():
        if current_output is None:
            set_status("Run an operation before saving an output.")
            return
        name = save_name_entry.get().strip()
        if not name:
            set_status("Enter a name for the output signal.")
            return
        saved_name = insert_signal(name, current_output)
        save_name_entry.delete(0, tk.END)
        save_name_entry.insert(0, "Output")
        set_status(f'Saved as "{saved_name}". Select it to use it in another operation.')

    ttk.Button(save_frame, text="Save output", command=save_output).grid(
        row=0, column=1, padx=(0, 8), pady=8
    )

    def run_operation():
        nonlocal current_output, saved_output_count
        names = selected_names()
        operation = operation_var.get()

        if operation in ("Add selected signals", "Subtract selected signals"):
            if len(names) < 2:
                set_status("Select at least 2 signals for this operation.")
                return
        elif len(names) != 1:
            set_status("Select exactly 1 signal for this operation.")
            return

        parameter = None
        if parameter_entry is not None:
            try:
                parameter = float(parameter_entry.get())
            except ValueError:
                set_status("Enter a valid number for this operation.")
                return

        try:
            result = _apply_operation(
                [signals[name] for name in names],
                operation,
                parameter,
            )
        except (KeyError, ValueError) as error:
            set_status(f"Could not apply operation: {error}")
            return

        current_output = result
        saved_output_count += 1
        axes.clear()
        axes.stem(result[0], result[1])
        axes.set_title(f"Output: {operation}")
        axes.set_xlabel("Sample index (n)")
        axes.set_ylabel("Amplitude")
        axes.grid(True)
        canvas.draw()
        save_name_entry.delete(0, tk.END)
        save_name_entry.insert(0, f"Output {saved_output_count}")
        set_status(f"{operation} complete. Save the output to reuse it as a signal.")

    ttk.Button(controls, text="Apply operation", command=run_operation).grid(
        row=2, column=0, columnspan=2, pady=(0, 8)
    )

    update_operation_controls()
    return page
