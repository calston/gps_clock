# -*- coding: utf-8 -*-

import os
import time

from math import floor, isnan
from datetime import datetime

import gps

from luma.core.render import canvas
from luma.oled.device import ssd1351
from luma.core.interface.serial import spi

from PIL import ImageFont


class App(object):
    def __init__(self):
        self._run = True
        self.count = 0
        self.ip = ""

        self.device = ssd1351(spi(), rotate=2, bgr=True)
        self.gpsd = gps.gps(mode=gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE)

        self.fontawesome = self.load_font('fa-solid-900.ttf', 16)
        self.default_font = self.load_font('DejaVuSansMono-Bold.ttf', 24)
        self.small_font = self.load_font('DejaVuSans.ttf', 10)

    def format_time(self):
        return datetime.utcnow().strftime("%H:%M:%S")

    def load_font(self, name, size):
        font_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), name))
        return ImageFont.truetype(font_path, size)

    def center_text(self, draw, x, y, w, h, text, font=None, fill=(255, 255, 255)):
        if not font:
            font = self.default_font

        dtime = self.format_time()
        w2, h2 = draw.textsize(dtime, font=font)

        x = x + floor((w - w2) / 2.0)
        y = y + floor((h - h2) / 2.0)

        draw.text((x, y), text=text, font=font, fill=fill)

    def rel_box(self, draw, x, y, w, h, outline=(255, 255, 255), fill=None, width=1):
        draw.rectangle(((x, y), (x+w, y+h)), outline=outline, fill=fill, width=1)

    def box_3d(self, draw, x, y, w, h, light=(255, 255, 255), dark=(32, 32, 32), fill=None, width=1):

        draw.rectangle(((x, y), (x+w, y+h)), fill=fill, width=1)
        draw.line((x, y+h, x, y, x, y, x+w, y), fill=light, width=width)
        draw.line((x+w, y, x+w, y+h, x+w, y+h, x, y+h), fill=dark, width=width)

    def fa_icon(self, draw, x, y, icon, fill=(0, 182, 214)):
        # Draw sattelite icon
        draw.text((x, y), text=icon, font=self.fontawesome, fill=fill)

    def formatDMS(self, deg):
        if isnan(deg):
            return "No fix"
        d = int(deg)
        md = abs(deg - d) * 60
        m = int(md)
        sd = (md - m) * 60
        return "%s°%s'%0.6f" % (d, m, sd)

    def draw(self):
        with canvas(self.device) as draw:
            self.rel_box(draw, 0, 25, 127, 30, (64, 64, 64))
            self.rel_box(draw, 0, 55, 127, 72, (64, 64, 64))

            self.center_text(draw, 0, 25, 127, 28, self.format_time(), fill=(0, 182, 214))

            if self.gpsd.fix.status > 0:
                # Draw sattelite icon
                self.fa_icon(draw, 0, 0, "\uf7c0")
                if self.gpsd.fix.mode == 2:
                    # 2D fix
                    self.fa_icon(draw, 32, 0, "\uf546")
                if self.gpsd.fix.mode == 3:
                    # 3D fix
                    self.fa_icon(draw, 32, 0, "\uf1b2")

                text = [
                    "Lat: " + self.formatDMS(self.gpsd.fix.latitude),
                    "Long: " + self.formatDMS(self.gpsd.fix.longitude),
                    "eth0: %s" % self.ip
                ]

                draw.multiline_text((4, 57), '\n'.join(text), font=self.small_font, fill=(255, 255,255))

    def getAddress(self):
        ipa = os.popen("/sbin/ip addr show dev eth0").read()
        for l in ipa.split('\n'):
            r = l.strip()
            if r.startswith('inet '):
                self.ip = r.split()[1]
        
    def run(self):
        while self._run:
            if self.gpsd.waiting():
                self.gpsd.next()

            self.draw()
            self.count += 1
            if self.count == 10:
                try:
                    self.getAddress()
                except:
                    pass
                self.count = 0

            time.sleep(0.2)

app = App()
app.run()
