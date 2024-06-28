import tkinter as tk
import tkinter.ttk as ttk

import numpy as np
from PIL import Image, ImageDraw, ImageTk


class Gauge(tk.Frame):

    start_deg = -188
    end_deg = 8
    ss_mult = 3  # supersampling
    cut_bottom = 0.65  # 1 to not cut, 0.4 to cut 60% etc
    # cut_bottom = 1  # 1 to not cut, 0.4 to cut 60% etc
    offset = 40

    def __init__(
        self,
        master,
        minvalue,
        maxvalue,
        variable,
        wedgesize,
        showtext,
        font,
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
        self.font = font or "Courier"
        self.fontsize = 14 * self.ss_mult

        # trace
        self.var.trace_add("write", self.var_changed_cb)

        # asserts
        assert 0 < self.wedgesize < 100
        assert maxvalue > minvalue

        # draw
        self.meter = tk.Label(self.box)
        self.draw_base()
        self.draw_wedge()
        self.draw_ticks()
        self.meter.place(x=0, y=0)
        self.box.pack()

        # label with text
        if self.showtext:
            self.text_label = tk.Label(
                self.box, textvariable=self.textvar, width=7, font=(self.font, self.fontsize, "italic")
            )
            try:
                rely = 0.3 / (1 - self.cut_bottom)
            except ZeroDivisionError:
                rely = 1
            rely = min(rely, 0.9)
            self.var_changed_cb()  # force this callback to update textvar
            self.text_label.place(relx=0.5, rely=rely, anchor="center")

    def var_changed_cb(self, *args):
        if self.showtext:
            if not self._user_supplied_var:
                self.text = f"{self.value:.2f}\N{DEGREE SIGN}"
        self.draw_wedge()

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
        if new_value != self.value:
            if self.minvalue <= new_value <= self.maxvalue:
                self.var.set(new_value)
            else:
                raise ValueError("Value outside min and max")

    def draw_base(self):
        # base arc
        len_box = self.box_length * self.ss_mult
        self.base = Image.new("RGBA", (len_box, len_box))  # will be reduced
        draw = ImageDraw.Draw(self.base)
        offset = self.offset * self.ss_mult
        arc_w = self.arc_width * self.ss_mult
        draw.arc(
            (offset, offset, len_box - offset, len_box - offset),
            self.start_deg,
            self.end_deg,
            self.bg,
            arc_w,
        )

    def draw_ticks(self):
        offset = self.offset * self.ss_mult
        len_box = self.box_length * self.ss_mult
        arc_w = self.arc_width * self.ss_mult
        draw = ImageDraw.Draw(self.base)
        # major ticks
        len_tick = self.arc_width * self.ss_mult * 0.6
        pos_maj = (x for x in range(self.minvalue, self.maxvalue + 1) if x % 5 == 0)
        for pos in pos_maj:
            n_pos = np.interp(pos, (self.minvalue, self.maxvalue), (self.start_deg, self.end_deg))
            draw.arc(
                (
                    offset + (arc_w - len_tick) / 2,
                    offset + len_tick / 2,
                    len_box - offset - (arc_w - len_tick) / 2,
                    len_box - offset - (arc_w - len_tick) / 2,
                ),
                n_pos - 0.1,
                n_pos + 0.1,
                self.fg,
                round(len_tick),
            )
        # minor ticks
        len_tick = len_tick * 0.5
        pos_min = (x for x in range(self.minvalue, self.maxvalue + 1) if x % 5 != 0)
        for pos in pos_min:
            n_pos = np.interp(pos, (self.minvalue, self.maxvalue), (self.start_deg, self.end_deg))
            draw.arc(
                (
                    offset + (arc_w - len_tick) / 2,
                    offset + (arc_w - len_tick) / 2,
                    len_box - offset - (arc_w - len_tick) / 2,
                    len_box - offset - (arc_w - len_tick) / 2,
                ),
                n_pos - 0.1,
                n_pos + 0.1,
                self.fg,
                round(len_tick),
            )
        # draw labels
        where_what = (
            (-20, "-20\N{DEGREE SIGN}"),
            (0, "0\N{DEGREE SIGN}"),
            (20, "+20\N{DEGREE SIGN}"),
        )
        font_size = 14 * self.ss_mult
        max_len_text = max(len(ww[1]) for ww in where_what)
        arc_r = (self.box_length * self.ss_mult) * 0.5 - offset
        l_arc_r = arc_r + ((max_len_text + 1) * 0.5 * font_size) * 0.5

        # # WARN: TEST DELETE
        # print(max_len_text)
        # print(f"{len_box=} {arc_r=} {l_arc_r=}")
        # draw.arc(
        #     (len_box * 0.5 - l_arc_r, len_box * 0.5 - l_arc_r, len_box * 0.5 + l_arc_r, len_box * 0.5 + l_arc_r),
        #     self.start_deg,
        #     self.end_deg,
        #     "black",
        #     5,
        # )

        # l_h_offset = -1 * (max_len_text * font_size) * 0.5
        # l_v_offset = font_size * 0.5
        for pos, text in where_what:
            n_pos = np.interp(pos, (self.minvalue, self.maxvalue), (self.start_deg, self.end_deg))
            n_pos = n_pos - 90  # because reasons
            n_pos_rad = np.deg2rad(n_pos)
            n_pos_rad = -n_pos_rad  # because numpy counts counterclockwise, and pillow counts clockwise
            # x = len_box * 0.5 + np.sin(n_pos_rad) * l_arc_r + l_h_offset
            # y = len_box * 0.5 + np.cos(n_pos_rad) * l_arc_r + l_v_offset
            x = len_box * 0.5 + l_arc_r * np.sin(n_pos_rad)
            y = len_box * 0.5 + l_arc_r * np.cos(n_pos_rad)
            draw.text((x, y), text, anchor="mm", font_size=font_size, fill=self.fg)

    def draw_wedge(self):
        im = self.base.copy()
        draw = ImageDraw.Draw(im)
        # get normalized value from self.start_deg to self.end_deg degrees
        val = self.value
        normalized_val = np.interp(val, (self.minvalue, self.maxvalue), (self.start_deg, self.end_deg))
        ws = self.wedgesize
        # draw wedge
        sidelen = self.box_length
        offset = self.offset * self.ss_mult
        draw.arc(
            (offset, offset, sidelen * self.ss_mult - offset, sidelen * self.ss_mult - offset),
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
    gauge1 = Gauge(mainframe, -22, 22, var, 2, True, "Fira Code", None, 500, 30, None, None, 2)
    gauge1.pack()
    tk.Scale(mainframe, variable=var, from_=(-22), to=22, orient="horizontal", resolution=0.1).pack(fill="x")

    root.mainloop()
