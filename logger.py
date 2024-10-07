import sys
import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class PrintLogger(object):  # create file like object

    def __init__(self, window):  # pass reference to text widget
        self.redir = tk.IntVar()
        self.frame = tk.Frame(window)
        tk.Grid.columnconfigure(self.frame, [0], weight=1)
        self.textbox = ScrolledText(self.frame, height=10,font=("consolas", "8", "normal"))
        self.textbox.grid(column=0,row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.checkbox = tk.Checkbutton(self.frame, text='Redirect Console',variable=self.redir, onvalue=1, offvalue=0, command=self.print_selection)
        self.checkbox.grid(column=0, row=1)

        self.redir.set(1)
        self.print_selection()

    def write(self, text):
        self.textbox.configure(state="normal")  # make field editable
        if len(text)>1:
            timeStamp = datetime.datetime.now()
            textStamp = timeStamp.strftime("%H:%M:%S")
            self.textbox.insert("end", "[{}] ".format(textStamp))
        self.textbox.insert("end", text)  # write text to textbox
        self.textbox.see("end")  # scroll to end
        self.textbox.configure(state="disabled")  # make field readonly

    def flush(self):  # needed for file like object
        pass

    def print_selection(self):
        if self.redir.get() == 1:
            self.redirect_logging()
        else:
            self.reset_logging()
        print("Console Path Updated")

    def reset_logging(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def redirect_logging(self):
        logger = self.textbox
        sys.stdout = self
        sys.stderr = self
