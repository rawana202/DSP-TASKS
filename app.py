import tkinter as tk

window = tk.Tk()
window.title("DSP Tasks")
window.geometry("800x600")


def open_task1():
    home_frame.pack_forget()
    task1_frame.pack(fill="both", expand=True)

home_frame = tk.Frame(window)
home_frame.pack(fill="both", expand=True)

task1_button = tk.Button(
    home_frame,
    text="Task 1",
    command=open_task1
)
task1_button.pack(pady=20)


task1_frame = tk.Frame(window)

task1_label = tk.Label(
    task1_frame,
    text="Welcome to Task 1"
)
task1_label.pack(pady=20)


window.mainloop()