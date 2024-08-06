import tkinter as tk

import numpy as np
from PIL import Image, ImageDraw, ImageTk


class RollMeter(tk.Frame):

    start_deg = -188
    end_deg = 8
    cut_bottom = 0.65  # 1 to not cut, 0.4 to cut 60% etc
    base_size = 250
    base_font_size = 16

    def __init__(
        self,
        master,
        minvalue=None,
        maxvalue=None,
        major_ticks_step=None,
        minor_ticks_per_major=None,
        variable=None,
        wedgesize=None,
        showtext=None,
        font=None,
        textvariable=None,
        textappend=None,
        box_length=None,
        arc_width=None,
        scale_color=None,
        wedge_color=None,
        ss_mult=None,
        **kwargs,
    ):
        # params
        self.ss_mult = ss_mult or 2 # supersampling for antialiasing
        self.showtext = showtext or True # show label in the middle
        self.var = variable or tk.DoubleVar(value=minvalue) # create var or use supplied
        self._user_supplied_var = False if textvariable is None else True  # flag that user supplied textvar
        self.textvar = textvariable or tk.StringVar()  # if user hasn't supplied it, display var
        self.textappend = textappend or "" # text to add to labels such as deg sign 
        self.wedgesize = wedgesize or 5 # size of wedge in degrees
        self.arc_width = arc_width or 10 # width of gauge arc in pixels
        self.minvalue = minvalue or 0 
        self.maxvalue = maxvalue or 100
        self.box_length = box_length or self.base_size # size of squart box in which to put arc
        self.box_length_ss = round(self.box_length * self.ss_mult)
        self.scale_color = scale_color or "#e5e5e5"
        self.wedge_color = scale_color or "#343a40"
        self.font = font or "Courier"
        self.fontsize = round(self.base_font_size * (self.box_length / self.base_size)) # for main label in the middle
        self.fontsize_ticks = max(round(self.base_font_size * (self.box_length / self.base_size) / 2), 14)
        self.major_ticks_step = major_ticks_step or 5
        self.minor_ticks_per_major = minor_ticks_per_major or 5

        # asserts
        assert 0 < self.wedgesize < 100
        assert self.maxvalue > self.minvalue

        # super
        kwargs["width"] = self.box_length
        kwargs["height"] = self.box_length * self.cut_bottom
        super().__init__(master=master, **kwargs)

        # automagically get offset
        self._offset = (
            max(
                len(f"{self.maxvalue:.1f}{self.textappend}") ,
                len(f"{self.minvalue:.1f}{self.textappend}") ,
            ) # number of symbols of text of ticks
            * self.fontsize_ticks # size of font of ticks
            * 0.5 # because offset if half the width of text
            # * 0.7
            * self.ss_mult
        )

        # trace
        self.var.trace_add("write", self.var_changed_cb)

        # draw
        self.meter = tk.Label(self)
        self.draw_base()
        self.draw_ticks()
        self.draw_wedge()
        self.meter.place(x=0, y=0)

        # label with text
        if self.showtext:
            self.text_label = tk.Label(self, textvariable=self.textvar, width=7, font=(self.font, self.fontsize, "italic"))
            try:
                rely = 0.25 / (1 - self.cut_bottom)
            except ZeroDivisionError:
                rely = 1
            rely = min(rely, 0.9)
            self.var_changed_cb()  # force this callback to update textvar
            self.text_label.place(relx=0.5, rely=rely, anchor="center")

    def var_changed_cb(self, *args):
        if self.showtext:
            if not self._user_supplied_var:
                self.text = f"{self.value:.1f}{self.textappend}"
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
        lb_ss = self.box_length_ss
        self.base = Image.new("RGBA", (lb_ss, lb_ss))  # will be reduced
        draw = ImageDraw.Draw(self.base)
        offset_ss = self._offset
        arc_w_ss = round(self.arc_width * self.ss_mult)
        draw.arc(
            (offset_ss, offset_ss, lb_ss - offset_ss, lb_ss - offset_ss),
            self.start_deg,
            self.end_deg,
            self.scale_color,
            arc_w_ss,
        )

    def draw_ticks(self):
        offset_ss = self._offset
        lb_ss = self.box_length_ss
        arc_w_ss = round(self.arc_width * self.ss_mult)
        maj_ts = self.major_ticks_step
        min_v = self.minvalue
        max_v = self.maxvalue
        s_deg = self.start_deg
        e_deg = self.end_deg
        draw = ImageDraw.Draw(self.base)
        l_tick_ss = arc_w_ss * 0.6 # length of tick ss
        w_tick_ss = round(1 * self.ss_mult) # width of tick ss
        center_ss = round(lb_ss/2) # center point coord of all arcs (both x and y)
        arc_r_ss = round(center_ss-offset_ss) # makes sense right
        tick_outer_r_ss = round(arc_r_ss - (arc_w_ss - l_tick_ss) / 2) 
        tick_inner_r_ss = round(tick_outer_r_ss - l_tick_ss)
        fontsize_ticks_ss = round(self.fontsize_ticks * self.ss_mult)
        arc_r_ss = lb_ss * 0.5 - offset_ss # radius of arc
        l_arc_r_ss = arc_r_ss + round(offset_ss/2) # radius of arc where to make labels
        # major ticks
        pos_maj = np.arange(min_v, max_v + maj_ts, maj_ts)
        for pos in pos_maj:
            if isinstance(pos, float):
                pos = round(pos, 2)
            n_pos = np.interp(pos, (min_v, max_v), (s_deg, e_deg)) # normalized deg pos on arc
            n_pos -= 180 # because pillow counts weirdly from +90 deg. also WTF
            n_pos_rad = np.deg2rad(n_pos) # because np.sin likes radians
            n_pos_rad = -n_pos_rad # because pillow counts clockwise, and numpy countercw
            x1 = round(center_ss + tick_outer_r_ss * np.cos(n_pos_rad))
            y1 = round(center_ss + tick_outer_r_ss * np.sin(n_pos_rad))
            x2 = round(center_ss + tick_inner_r_ss * np.cos(n_pos_rad))
            y2 = round(center_ss + tick_inner_r_ss * np.sin(n_pos_rad))
            draw.line((x1,y1,x2,y2), width=w_tick_ss, fill=self.wedge_color)
            # also draw labels
            text = f"{pos}{self.textappend}"
            n_pos += 90  # because reasons
            n_pos_rad = np.deg2rad(n_pos)
            n_pos_rad = -n_pos_rad  # because numpy counts counterclockwise, and pillow counts clockwise
            x = lb_ss * 0.5 + l_arc_r_ss * np.sin(n_pos_rad) # these are coords of the CENTER of label
            y = lb_ss * 0.5 + l_arc_r_ss * np.cos(n_pos_rad) # look how I draw with anchor='mm'
            draw.text((x, y), text, anchor="mm", font_size=fontsize_ticks_ss, fill=self.wedge_color)
        # minor ticks
        l_tick_ss = l_tick_ss * 0.5
        tick_outer_r_ss = round(arc_r_ss - (arc_w_ss - l_tick_ss) / 2) 
        tick_inner_r_ss = round(tick_outer_r_ss - l_tick_ss)
        min_ts = maj_ts / self.minor_ticks_per_major
        pos_min = []
        for maj_tick in pos_maj:
            start = maj_tick + min_ts
            end = maj_tick + maj_ts
            if end > max_v:
                end = end - (max_v - end) / min_ts
                break  # WARN: crutch
            pos_min.extend(np.arange(start, end, min_ts))
        for pos in pos_min:
            n_pos = np.interp(pos, (min_v, max_v), (s_deg, e_deg)) # normalized deg pos on arc
            n_pos -= 180 # because pillow counts weirdly from +90 deg. also WTF
            n_pos = - n_pos # because pillow counts clockwise, and numpy countercw
            n_pos = np.deg2rad(n_pos) # because np.sin likes radians
            x1 = round(center_ss + tick_outer_r_ss * np.cos(n_pos))
            y1 = round(center_ss + tick_outer_r_ss * np.sin(n_pos))
            x2 = round(center_ss + tick_inner_r_ss * np.cos(n_pos))
            y2 = round(center_ss + tick_inner_r_ss * np.sin(n_pos))
            draw.line((x1,y1,x2,y2), width=w_tick_ss, fill=self.wedge_color)

    def draw_wedge(self):
        im = self.base.copy()
        draw = ImageDraw.Draw(im)
        # get normalized value from self.start_deg to self.end_deg degrees
        val = self.value
        normalized_val = np.interp(val, (self.minvalue, self.maxvalue), (self.start_deg, self.end_deg))
        ws = self.wedgesize
        # draw wedge
        len_im = self.box_length # length of end image after reducing
        lb_ss = self.box_length_ss
        offset_ss = self._offset
        arc_w = round(self.arc_width * self.ss_mult)
        draw.arc(
            (offset_ss, offset_ss, lb_ss - offset_ss, lb_ss - offset_ss),
            normalized_val - ws,
            normalized_val + ws,
            self.wedge_color,
            arc_w,
        )
        # resize image (if needed)
        if self.ss_mult != 1:
            im = im.resize((len_im, len_im), Image.BICUBIC)
        # crop image
        self.meterimage = ImageTk.PhotoImage( im.crop((0, 0, len_im, len_im * self.cut_bottom)))
        # put image on label
        self.meter.configure(image=self.meterimage)


class PitchMeter(tk.Frame):

    base_font_size = 16
    base_height = 250

    def __init__(
        self,
        master,
        height=None,
        width=None,
        minvalue=None,
        maxvalue=None,
        major_ticks_step=None,
        minor_ticks_per_major=None,
        variable=None,
        textvariable=None,
        textappend=None,
        font=None,
        wedgesize=None,
        scale_color=None,
        wedge_color=None,
        **kwargs,
    ):
        # params
        self.minvalue = minvalue or -20
        self.maxvalue = maxvalue or 20
        self.var = variable or tk.DoubleVar(value=self.minvalue)
        self.textvar = textvariable or tk.StringVar()  # TODO: update this value
        self.textappend = textappend or ""
        self._user_supplied_var = False if textvariable is None else True
        self.height = height or self.base_height
        self.fontsize = round(self.base_font_size * (self.height / self.base_height))
        self.fontsize_ticks = max(round(self.base_font_size * (self.height / self.base_height) / 2), 14)
        self.scale_color = scale_color or "#e5e5e5"
        self.wedge_color = wedge_color or "#343a40"
        self.font = font or "Courier"
        self.wedgesize = wedgesize or 2  # this is in percent
        self.major_ticks_step = major_ticks_step or 5
        self.minor_ticks_per_major = minor_ticks_per_major or 5

        # get width automagically out of estimated text width
        max_text_w = max(
            len(f"{self.maxvalue:+.1f}{self.textappend}"),
            len(f"{self.minvalue:+.1f}{self.textappend}"),
        )
        self.width = width or round(max_text_w * self.fontsize_ticks * 0.25)
        
        # offsets for drawing rectangle
        v_offs = self.fontsize_ticks + 2 # vertical offset to give space for tick labels
        self._base_v_offset = v_offs
        h_offs = round((max_text_w + 1) * self.fontsize_ticks * 0.5)
        self._base_h_offset = h_offs

        # trace
        self.var.trace_add("write", self.var_changed_cb)

        # asserts
        assert self.maxvalue > self.minvalue
        assert 0 < self.wedgesize < 100

        # super
        kwargs["padx"] = 5
        kwargs["pady"] = 5
        kwargs["height"] = self.height
        kwargs["width"] = self.width
        super().__init__(master, **kwargs)

        # labels
        self.meter = tk.Label(self)
        self.label = tk.Label(
            self, textvariable=self.textvar, anchor="center", width=max_text_w + 1, font=(self.font, self.fontsize, "italic")
        )

        # draw
        self.draw_base()
        self.draw_ticks()
        self.draw_wedge()

        # force this callback to update textvar
        self.var_changed_cb()

        # pack all
        self.meter.pack(expand=True, fill="y", side="left")
        self.label.pack(expand=True, side="left", anchor="w", padx=(5, 0))

    def draw_base(self):
        text_top = f"{self.maxvalue:+}{self.textappend}"
        text_bot = f"{self.minvalue:+}{self.textappend}"
        w = self.width
        h = self.height
        v_offs = self._base_v_offset
        h_offs = self._base_h_offset
        self._base_v_offset = v_offs
        self.base = Image.new("RGBA", (w+h_offs, h))
        draw = ImageDraw.Draw(self.base)
        # base rectangle
        draw.rectangle(
            (h_offs, v_offs, w + h_offs, h - v_offs),
            fill=self.scale_color,
            width=w,
        )
        # labels
        fontsize_ticks = self.fontsize_ticks
        draw.text((round((w+h_offs*2) / 2), 0), text=text_top, anchor="mt", font_size=fontsize_ticks, fill=self.wedge_color)
        draw.text((round((w+h_offs*2) / 2), h), text=text_bot, anchor="mb", font_size=fontsize_ticks, fill=self.wedge_color)

    def draw_ticks(self):
        draw = ImageDraw.Draw(self.base)
        bh = self.height
        v_offs = self._base_v_offset
        h_offs = self._base_h_offset
        w = self.width
        # major ticks
        len_tick = w * 0.6
        x_st = w / 2 - len_tick / 2 + h_offs
        x_end = w / 2 + len_tick / 2 + h_offs
        pos_maj = np.arange(self.minvalue, self.maxvalue + self.major_ticks_step, self.major_ticks_step)
        for pos in pos_maj:
            # normalized position
            n_pos = bh - np.interp(pos, (self.minvalue, self.maxvalue), (v_offs, bh - v_offs))
            draw.line(
                ((x_st, n_pos), (x_end, n_pos)),
                width=1,
                fill=self.wedge_color,
            )
            # also draw labels for major ticks
            text_tick = f"{pos:+}{self.textappend}"
            draw.text((h_offs, n_pos), text_tick, anchor="rm", font_size=self.fontsize_ticks, fill=self.wedge_color)

        # minor ticks
        len_tick *= 0.4
        x_st = w / 2 - len_tick / 2 + h_offs
        x_end = w / 2 + len_tick / 2 + h_offs
        min_tick_step = self.major_ticks_step / self.minor_ticks_per_major
        pos_min = []
        for maj_tick in pos_maj:
            start = maj_tick + min_tick_step
            end = maj_tick + self.major_ticks_step
            if end > self.maxvalue:
                end = end - (self.maxvalue - end) / min_tick_step
                break  # WARN: crutch
            pos_min.extend(np.arange(start, end, min_tick_step))
        for pos in pos_min:
            n_pos = np.interp(pos, (self.minvalue, self.maxvalue), (v_offs, bh - v_offs))
            draw.line(
                ((x_st, n_pos), (x_end, n_pos)),
                width=1,
                fill=self.wedge_color,
            )

    def draw_wedge(self):
        im = self.base.copy()
        draw = ImageDraw.Draw(im)
        # normalize val based on height and position of base column
        val = self.value
        inv_val = (self.maxvalue - val) + self.minvalue  # inverting because upside down
        bh = self.height
        v_ofs = self._base_v_offset
        h_ofs = self._base_h_offset
        w = self.width
        wsize = self.wedgesize * 0.01 * bh  # wedgesize is in percent
        normalized_val = np.interp(inv_val, (self.minvalue, self.maxvalue), (v_ofs, bh - v_ofs))
        # draw wedge
        upmostpos = wsize / 2
        botmostpos = bh - wsize / 2
        y = max(upmostpos, min(botmostpos, normalized_val))
        xy_start = (h_ofs, y - wsize / 2)
        xy_end = (w+h_ofs, y + wsize / 2)
        draw.rectangle(
            (xy_start, xy_end),
            fill=self.wedge_color,
        )
        # resize and put on label
        self.meterimage = ImageTk.PhotoImage(im)
        self.meter.configure(image=self.meterimage)

    def var_changed_cb(self, *args):
        if not self._user_supplied_var:
            self.text = f"{self.value:.1f}{self.textappend}"
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


if __name__ == "__main__":
    root = tk.Tk()
    mainfr = tk.Frame(root)

    # scale
    var = tk.DoubleVar(value=0)
    tk.Scale(mainfr, variable=var, from_=(-22), to=22, orient="horizontal", resolution=0.1).pack(
        fill="x", expand=True, side="bottom"
    )

    # radgauge
    gfr = tk.Frame(mainfr)
    gfr.pack(expand=True, fill="both", side="left")
    RollMeter(gfr, -24, 24, 4, 5, var, 2, True, "Fira Code", None, "\N{DEGREE SIGN}", 500, 30, None, None).pack()
    RollMeter(gfr, -22, 23, 8, 0, var, 30, True, "Fira Code", None, "\N{DEGREE SIGN}", 250, 10, None, None).pack()
    RollMeter(
        gfr, -100, 100, 20, 2, var, 1, True, "Fira Code", tk.StringVar(value="Noice!"), None, 250, 10, None, None).pack()
    RollMeter(gfr, -1, 1, 0.1, 1, var, box_length=350, arc_width=50).pack()

    # pitchemeter
    pfr = tk.Frame(mainfr)
    PitchMeter(pfr, height=500, variable=var, textappend="\N{DEGREE SIGN}").pack(side="top")
    PitchMeter(pfr, variable=var, width=100, textappend="\N{DEGREE SIGN}", major_ticks_step=3, minor_ticks_per_major=3).pack(
        side="top", anchor="w"
    )
    PitchMeter(
        pfr,
        variable=var,
        maxvalue=1,
        minvalue=-1,
        textappend="\N{DEGREE SIGN} deg",
        major_ticks_step=0.5,
        minor_ticks_per_major=2,
        font="Victor Mono",
    ).pack(side="top", anchor="w")
    pfr.pack(expand=True, fill="both", side="left")

    # star mainloop
    mainfr.pack(expand=True, fill="both", padx=20, pady=20)
    root.mainloop()
