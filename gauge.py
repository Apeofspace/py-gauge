import tkinter as tk
import tkinter.ttk as ttk

import numpy as np
from PIL import Image, ImageDraw, ImageTk


class Gauge(tk.Frame):

    start_deg = -180
    end_deg = 0
    ss_mult = 3  # supersampling
    cut_bottom = 0.55  # 1 to not cut, 0.4 to cut 60% etc

    def __init__(
        self,
        master,
        minvalue,
        maxvalue,
        variable,
        wedgesize,
        showtext,
        textvariable,
        box_length,
        arc_width,
        bg,
        fg,
        ss_mult,
        **kwargs,
    ):
        super().__init__(master=master, **kwargs)
        self.box = tk.Frame(self, width=box_length, height=box_length * self.cut_bottom)

        self.showtext = showtext or True
        self.var = variable or tk.DoubleVar(value=minvalue)
        self._user_supplied_var = False if textvariable is None else True  # flag that user supplied textvar
        self.textvar = textvariable or tk.StringVar()  # if user hasn't supplied it, display var
        self.wedgesize = wedgesize or 5
        self.arc_width = arc_width or 10
        self.minvalue = minvalue or 0
        self.maxvalue = maxvalue or 100
        self.box_length = box_length or 200
        self.bg = bg or "#e5e5e5"
        self.fg = bg or "#343a40"
        # self.ss_mult = ss_mult or 5

        # trace
        self.var.trace_add("write", self.var_changed_cb)

        # asserts
        assert 0 < self.wedgesize < 100
        assert maxvalue > minvalue

        # draw
        self.meter = tk.Label(self.box)
        self.draw_base()
        self.draw_arc()
        self.meter.place(x=0, y=0)
        self.box.pack()

        # label with text
        if self.showtext:
            self.text_label = tk.Label(
                self.box,
                textvariable=self.textvar,
                width=7,
                font=(
                    "Courier",
                    14 * self.ss_mult,
                ),
            )
            rely = 0.5 / (1 - self.cut_bottom)
            rely = min(rely, 0.9)
            self.var_changed_cb()  # force this callback to update textvar
            self.text_label.place(relx=0.5, rely=rely, anchor="center")

    def var_changed_cb(self, *args):
        if self.showtext:
            if not self._user_supplied_var:
                self.text = f"{self.value:.2f}\N{DEGREE SIGN}"
        self.draw_arc()

    @property
    def text(self):
        return self.textvar.get()

    @text.setter
    def text(self, str):
        self.textvar.set(str)

    @property
    def value(self):
        return self.var.get()

    @value.setter
    def value(self, new_value):
        if self.minvalue <= new_value <= self.maxvalue:
            self.var.set(new_value)
        else:
            raise ValueError("Value outside min and max")

    def draw_base(self):
        # base arc
        self.base = Image.new("RGBA", (self.box_length * self.ss_mult, self.box_length * self.ss_mult))  # will be reduced
        draw = ImageDraw.Draw(self.base)
        draw.arc(
            (0, 0, self.box_length * self.ss_mult - 20, self.box_length * self.ss_mult - 20),
            self.start_deg,
            self.end_deg,
            self.bg,
            self.arc_width * self.ss_mult,
        )

    def draw_arc(self):
        im = self.base.copy()
        draw = ImageDraw.Draw(im)
        # get normalized value from self.start_deg to self.end_deg degrees
        val = self.value
        normalized_val = np.interp(val, (self.minvalue, self.maxvalue), (self.start_deg, self.end_deg))
        ws = self.wedgesize
        # draw wedge
        sidelen = self.box_length
        draw.arc(
            (0, 0, sidelen * self.ss_mult - 20, sidelen * self.ss_mult - 20),
            normalized_val - ws,
            normalized_val + ws,
            self.fg,
            self.arc_width * self.ss_mult,
        )
        # resize image and put it on the label
        self.meterimage = ImageTk.PhotoImage(
            im.resize((sidelen, sidelen), Image.BICUBIC).crop((0, 0, sidelen, sidelen * self.cut_bottom))
        )

        self.meter.configure(image=self.meterimage)


if __name__ == "__main__":
    root = tk.Tk()

    mainframe = tk.Frame(root, padx=20, pady=20)
    mainframe.pack(expand=True, fill="both")

    var = tk.DoubleVar(value=0)
    gauge1 = Gauge(mainframe, -18, 18, var, 2, True, None, 500, 20, None, None, 2)
    gauge1.pack()
    tk.Scale(mainframe, variable=var, from_=(-18), to=18, orient="horizontal", resolution=0.1).pack(fill="x")

    root.mainloop()
