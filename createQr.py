import os
import random
import sys
import tempfile
import threading
import tkinter as tk
import tkinter.colorchooser
import tkinter.filedialog
from tkinter import messagebox

import pyqrcode
from PIL import Image, ImageTk


def show(location):
    with Image.open(location, "r") as img:
        img.show(title="Vorschau")
    os.remove(location)


def hex_to_rgb(value):
    try:
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    except ValueError:
        return 255, 255, 255


def color_converter(value):
    colors = {
        "Weiß": (255, 255, 255),
        "Schwarz": (0, 0, 0),
        "Blau": (0, 0, 139),
        "Grün": (124, 252, 0),
        "Gelb": (255, 255, 0),
    }
    return colors[value]


def nospace():
    tkinter.messagebox.showerror("Fehler", "Du hast zu viel Text eingegeben.\nBitte versuche es mit weniger!")


def add_picture(picture, location):
    # Now open that png image to put the logo
    with Image.open(location) as img:
        width, height = img.size
        # How big the logo we want to put in the qr code png
        logo_size = (width + height) // 10
        # Open the logo image
        with Image.open(picture) as logo:
            logo = logo.convert("RGBA")
            img = img.convert("RGBA")
            # Calculate xmin, ymin, xmax, ymax to put the logo
            xmin = ymin = int((width / 2) - (logo_size / 2))
            xmax = ymax = int((width / 2) + (logo_size / 2))
            # resize the logo as calculated
            logo = logo.resize((xmax - xmin, ymax - ymin))
            # put the logo in the qr code
            img.paste(logo, (xmin, ymin, xmax, ymax))
            img.save(fp=location)


class Main:
    FONT = ('Arial', 13, 'bold')

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Qr-Code erstellen")
        self.root.wm_resizable(False, False)
        self.radio_frame = tk.Frame(self.root)
        self.radio_frame.pack()
        var = tk.IntVar()
        tk.Radiobutton(self.radio_frame, command=self.normal, variable=var, value=0, text="Einfache Einstellung",
                       font=self.FONT).grid(row=0)
        tk.Radiobutton(self.radio_frame, command=self.advanced, variable=var, value=1,
                       text="Erweiterte Einstellungen", font=self.FONT).grid(row=0, column=1)

        self.frame_normal = tk.LabelFrame(self.root, text="Einfache Einstellungen", font=self.FONT,
                                          fg="white", bg="grey")
        self.frame_advanced = tk.LabelFrame(self.root, text="Erweiterte Einstellungen", font=self.FONT,
                                            fg="white", bg="grey")
        self.frame_normal.pack()

        # Create necessary variables
        self.label_list_einfach = ["Hintergrundfarbe", "Vordergrundfarbe", "Inhalt", "Bild(optional)"]
        self.label_list_advanced = ["Hintergrundfarbe", "Vordergrundfarbe", "Inhalt", "Version",
                                    "Fehler korrektur", "Bild(optional)"]
        self.version_list = ["Kleinstmögliches Level (Standard)"]
        for i in range(1, 41):
            self.version_list.append(i)
        self.colors = ["Weiß", "Schwarz", "Blau", "Grün", "Gelb"]
        self.error_correct_list = ["7%", "15%", "25%", "30%"]
        self.advanced_fg = "#000000"
        self.advanced_bg = "#ffffff"
        self.bg_opt_var = tk.StringVar(self.frame_normal)
        self.bg_opt_var.set(self.colors[0])
        self.fg_opt_var = tk.StringVar(self.frame_normal)
        self.fg_opt_var.set(self.colors[1])
        self.version_var = tk.StringVar(self.frame_advanced)
        self.version_var.set(self.version_list[0])
        self.error_correct_var = tk.StringVar(self.frame_advanced)
        self.error_correct_var.set(self.error_correct_list[0])

        # Create widgets
        self.bg_opt_widget = tk.OptionMenu(self.frame_normal, self.bg_opt_var, *self.colors)
        self.bg_opt_widget.configure(font=self.FONT)
        self.frame_normal.nametowidget(self.bg_opt_widget.menuname).config(font=self.FONT)
        self.fg_opt_widget = tk.OptionMenu(self.frame_normal, self.fg_opt_var, *self.colors)
        self.fg_opt_widget.configure(font=self.FONT)
        self.frame_normal.nametowidget(self.fg_opt_widget.menuname).config(font=self.FONT)
        self.content_widget = tk.Text(self.frame_normal, font=self.FONT, height=15, width=60, bg="light yellow",
                                      cursor="rtl_logo")
        self.picture_button = tk.Button(self.frame_normal, text="Öffnen", command=lambda: self.load_picture("normal"),
                                        bg="lightblue", cursor="draped_box", font=self.FONT)
        self.picture_label = tk.Button(self.frame_normal, cursor="X_cursor")
        self.picture_label["command"] = self.picture_label.grid_forget
        self.create_button = tk.Button(self.frame_normal, text="Erstellen",
                                       command=lambda: self.read(master="normal"), bg="DarkSeaGreen4",
                                       cursor="draped_box", font=self.FONT)
        self.preview_button = tk.Button(self.frame_normal, text="Vorschau",
                                        command=lambda: self.read(master="normal", preview=True), bg="LightGoldenrod1",
                                        cursor="draped_box", font=self.FONT)
        # ============================================================================================================ #
        self.version_widget = tk.OptionMenu(self.frame_advanced, self.version_var, *self.version_list)
        self.version_widget.configure(font=self.FONT)
        self.frame_advanced.nametowidget(self.version_widget.menuname).config(font=self.FONT)
        self.error_correct_widget = tk.OptionMenu(self.frame_advanced, self.error_correct_var, *self.error_correct_list)
        self.error_correct_widget.configure(font=self.FONT)
        self.frame_advanced.nametowidget(self.error_correct_widget.menuname).config(font=self.FONT)
        self.bg_colorpicker_button = tk.Button(self.frame_advanced, text="Auswählen",
                                               command=lambda: self.return_color("bg"))
        self.fg_colorpicker_button = tk.Button(self.frame_advanced, text="Auswählen",
                                               command=lambda: self.return_color("fg"))
        self.bg_colorpicker_frame = tk.Frame(self.frame_advanced, bg=self.advanced_bg)
        self.fg_colorpicker_frame = tk.Frame(self.frame_advanced, bg=self.advanced_fg)
        self.content_widget_advanced = tk.Text(self.frame_advanced, font=self.FONT, height=15, width=60,
                                               bg="light yellow", cursor="rtl_logo")
        self.picture_button_advanced = tk.Button(self.frame_advanced, text="Öffnen",
                                                 command=lambda: self.load_picture("advanced"),
                                                 bg="lightblue", cursor="draped_box", font=self.FONT)
        self.picture_label_advanced = tk.Button(self.frame_advanced)
        self.picture_label_advanced["command"] = self.picture_label_advanced.grid_forget
        self.create_button_advanced = tk.Button(self.frame_advanced, text="Erstellen",
                                                command=lambda: self.read(master="advanced"), bg="DarkSeaGreen4",
                                                cursor="draped_box", font=self.FONT)
        self.preview_button_advanced = tk.Button(self.frame_advanced, text="Vorschau",
                                                 command=lambda: self.read(master="advanced", preview=True),
                                                 bg="LightGoldenrod1",
                                                 cursor="draped_box", font=self.FONT)
        # Place all widgets in normal_frame
        row = 0
        for key in self.label_list_einfach:
            tk.Label(self.frame_normal, text=key + ":",
                     font=("Arial", 20), bg=self.frame_normal["bg"]).grid(row=row)  # place the first row of labels
            row += 1
        self.bg_opt_widget.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        self.fg_opt_widget.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        self.content_widget.grid(row=2, column=1, columnspan=2, pady=5)
        self.picture_button.grid(row=3, column=1, columnspan=2, sticky="ew", ipady=20, pady=5)
        self.create_button.grid(row=4, column=2, sticky="ew", ipady=20, pady=5, padx=10)
        self.preview_button.grid(row=4, column=1, sticky="ew", ipady=20, pady=5, padx=10)

        # Place all widgets in advanced_frame
        row = 0
        for key in self.label_list_advanced:
            tk.Label(self.frame_advanced, text=key + ":",
                     font=("Arial", 20), bg=self.frame_advanced["bg"]).grid(row=row)  # place the first row of labels
            row += 1
        self.bg_colorpicker_button.grid(row=0, column=1, sticky="swne", padx=2, pady=2)
        self.fg_colorpicker_button.grid(row=1, column=1, sticky="swne", padx=2, pady=2)
        self.bg_colorpicker_frame.grid(row=0, column=2, sticky="swne", padx=2, pady=2)
        self.fg_colorpicker_frame.grid(row=1, column=2, sticky="swne", padx=2, pady=2)
        self.content_widget_advanced.grid(row=2, column=1, columnspan=2, pady=5)
        self.version_widget.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)
        self.error_correct_widget.grid(row=4, column=1, columnspan=2, sticky="ew", pady=5)
        self.picture_button_advanced.grid(row=5, column=1, columnspan=2, sticky="ew", ipady=20, pady=5)
        self.create_button_advanced.grid(row=6, column=2, sticky="ew", ipady=20, pady=5, padx=10)
        self.preview_button_advanced.grid(row=6, column=1, sticky="ew", ipady=20, pady=5, padx=10)
        self.root.mainloop()

    def read(self, master, preview=False):
        if preview:
            try:
                location = tempfile.gettempdir() + "\\" + str(random.randint(0, 99999999999)) + ".png"
            except:
                exit(1)
        else:
            location = tk.filedialog.asksaveasfilename(filetypes=(("Imagefile", ".png"),),
                                                       defaultextension="png",
                                                       title="Bild laden")
        if master == "normal":
            text = self.content_widget.get(1.0, tk.END)
            fg = color_converter(self.fg_opt_var.get())
            bg = color_converter(self.bg_opt_var.get())
            if self.picture_label.winfo_ismapped():
                picture = self.image_obj
            else:
                picture = None
            self.create_qr(location=location, text=text, fg=fg, bg=bg, picture=picture, preview=preview)
        else:
            text = self.content_widget_advanced.get(1.0, tk.END)
            fg = hex_to_rgb(self.advanced_fg)
            bg = hex_to_rgb(self.advanced_bg)
            version = self.version_var.get()
            error = self.error_correct_var.get().replace("%", "")
            error = {"7": "l", "15": "m", "25": "q", "30": "h"}.get(error)
            if self.picture_label_advanced.winfo_ismapped():
                picture = self.image_obj
            else:
                picture = None
            try:
                version = int(version)
            except Exception:
                version = None
            self.create_qr(location=location, text=text, fg=fg, bg=bg, picture=picture, version=version,
                           error=error, preview=preview)

    def create_qr(self, preview, location, text, fg, bg, picture, error="q", version=None):
        try:
            url = pyqrcode.create(text, error=error, version=version)
            url.png(location, module_color=(*fg, 255), background=(*bg, 255), scale=10)
            with Image.open(location) as f:
                f = f.convert("RGBA")
                f.save(location)
            if picture:
                add_picture(picture=self.image_location, location=location)
            if preview:
                threading.Thread(target=lambda: show(location)).start()
        except ValueError:
            nospace()

    def return_color(self, dimension):
        color = tk.colorchooser.askcolor(title="Farbe auswählen")[1]
        if color is not None:
            if dimension == "bg":
                self.advanced_bg = color
                self.bg_colorpicker_frame.configure(bg=color)
            else:
                self.advanced_fg = color
                self.fg_colorpicker_frame.configure(bg=color)
            return color

    def load_picture(self, master):
        self.image_location = tkinter.filedialog.askopenfilename(filetypes=(("Imagefile", ".png"),),
                                                                 defaultextension="png",
                                                                 title="Bild laden")
        try:
            self.image_obj = Image.open(self.image_location, )
            self.resized_image = self.image_obj.resize((50, 50), Image.LANCZOS)
            self.resized_image = ImageTk.PhotoImage(self.resized_image)
            if master == "normal":
                self.picture_label.grid(row=3, column=1, sticky="w")
                self.picture_label["image"] = self.resized_image
            else:
                self.picture_label_advanced.grid(row=5, column=1, sticky="w")
                self.picture_label_advanced["image"] = self.resized_image
        except Exception:
            print(sys.exc_info()[1])

    def normal(self):
        self.frame_normal.pack()
        self.frame_advanced.pack_forget()
        self.root.update()
        self.root.mainloop()

    def advanced(self):
        self.frame_normal.pack_forget()
        self.frame_advanced.pack()
        self.root.update()


if __name__ == '__main__':
    Main()
