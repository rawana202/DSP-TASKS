import tkinter as tk
import task1 , task2


window = tk.Tk()
window.title("DSP Tasks")
window.geometry("800x600")

#menu bar 
menu = tk.Frame(window)
menu.pack(side="left", fill="y")


#the task gui appears here
content = tk.Frame(window)
content.pack(side="right", fill="both", expand=True)

#tasks files
tasks = [
    task1,task2
]

#page for each task
pages = {}

for number, task in enumerate(tasks, start=1):
    pages[number] = task.create_page(content)


def show_task(number):
    for page in pages.values():
        page.pack_forget()

    pages[number].pack(fill="both", expand=True)


#create 10 buttons
for number in range(1, 11):
    button = tk.Button(
        menu,
        text=f"Task {number}",
        command=lambda n=number: show_task(n)
    )
    button.pack(padx=10, pady=8, fill="x")

window.mainloop()