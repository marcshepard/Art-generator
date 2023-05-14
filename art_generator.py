"""
art_generator.py - produce an image from a content and style picture

The generated image will be similar to the content image, but with the style of the style image.
This file provides a graphical user interface for the neural_net.py code, which is based on
Andrew Ng's Coursera course on Convolutional Neural Networks. 
"""

import tkinter as tk
from tkinter import filedialog, scrolledtext
import os
import json
from threading import Thread
from PIL import Image, ImageTk
from neural_net import ImageGenerator

# pylint: disable=too-many-ancestors, line-too-long, too-many-arguments, too-many-instance-attributes

# Configuration variables (not yet settable in the GUI)
IMAGE_WIDTH = 400   # The width of the images used for training
IMAGE_HEIGHT = 400  # The height of the images used for training
DISPLAY_SCALE = .5  # The scale of the images displayed in the GUI

# Global read-only variables
HOME = os.path.join (os.path.expanduser("~"))
SETTINGS_FILE = os.path.join (HOME, "art_generator.json")
KEY_CONTENT_FILE = "content"
KEY_STYLE_FILE = "style"
KEY_EPOCHS = "epochs"
WELCOME_MESSAGE = """Welcome to the Art Generator.
Select content and style images and then click 'Generate' to create a new image."""
DEFAULT_EPOCHS = 200

def save_settings (settings : dict):
    """Save the settings dictionary to the SETTINGS_FILE"""
    with open (SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump (settings, f)

def load_settings () -> dict:
    """Load the settings dictionary from the SETTINGS_FILE"""
    settings = {}
    if os.path.exists (SETTINGS_FILE):
        with open (SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load (f)

    if KEY_EPOCHS not in settings:
        settings[KEY_EPOCHS] = DEFAULT_EPOCHS
    if KEY_CONTENT_FILE not in settings:
        settings[KEY_CONTENT_FILE] = None
    if KEY_STYLE_FILE not in settings:
        settings[KEY_STYLE_FILE] = None

    if not os.path.exists (settings[KEY_CONTENT_FILE]):
        settings[KEY_CONTENT_FILE] = None
    if not os.path.exists (settings[KEY_STYLE_FILE]):
        settings[KEY_STYLE_FILE] = None

    return settings

class ReadOnlyScrolledText (scrolledtext.ScrolledText):
    """A read-only scrolled text widget, for displaying output"""
    def __init__ (self, win : tk.Tk, w : int, h : int, pad : int = 0):
        super ().__init__ (win, wrap = tk.WORD, width = w, height = h, padx = pad, pady = pad)
        self.config (state = tk.DISABLED)
        self.tag_config("error", foreground="red")
        self.tag_config("error", background="yellow")

    def writeln (self, text):
        """Write a line of text to the widget"""
        self.config (state = tk.NORMAL)
        self.insert (tk.END, text + "\n")
        self.see (tk.END)
        self.config (state = tk.DISABLED)

    def write_error (self, text):
        """Write an error message to the widget"""
        self.config (state = tk.NORMAL)
        self.insert (tk.END, "ERROR: " + text + "\n", "error")
        self.see (tk.END)
        self.config (state = tk.DISABLED)

# Create a class to display an image scaled to a given size
class DisplayImage (tk.Label):
    """A label that displays an image scaled to a given size"""
    def __init__ (self, parent : tk.Tk, w : int = None, h : int = None):
        super ().__init__ (parent)
        self.width = w
        self.height = h
        self.image = None

    def set_image (self, file : str):
        """Set the image to be displayed"""
        img = Image.open (file)
        if self.width is not None and self.height is not None:
            img = img.resize ((self.width, self.height))
        img = ImageTk.PhotoImage (img)
        self.config (image = img)
        self.image = img
        #self.update ()

# Create a class to display a label and small numeric input field
class NumberEntry (tk.Frame):
    """A frame containing a label and a numeric entry field"""
    def __init__ (self, win : tk.Tk, label : str, value : int, min_value : int, max_value : int):
        super ().__init__ (win)
        self.label = tk.Label (self, text = label)
        self.label.pack (side = tk.LEFT)
        self.entry = tk.Entry (self, width = 5)
        self.entry.pack (side = tk.LEFT)
        self.entry.insert (0, str (value))
        self.min_value = min_value
        self.max_value = max_value
        self.value = value

    def get_value (self) -> int:
        """Return the value in the entry field"""
        value = self.value
        if self.entry.get().isdigit():
            value = int (self.entry.get ())
        if value < self.min_value:
            value = self.min_value
        elif value > self.max_value:
            value = self.max_value
        self.entry.delete (0, tk.END)
        self.entry.insert (0, str (value))
        return value

class Root (tk.Tk):
    """The root window for the application"""
    def __init__ (self):
        super ().__init__ ()
        self.title ("Art Generator")
        pad = 10
        settings = load_settings ()
        self.settings = settings

        # Create a frame to hold all the widgets
        frame = tk.Frame (self, relief=tk.RAISED, borderwidth=1)

        # A read-only message box to display program information
        self.textbox = ReadOnlyScrolledText(frame, 80, 10, pad)
        self.textbox.writeln (WELCOME_MESSAGE)
        self.textbox.grid(row=0, column = 0, columnspan=4, sticky="ew")

        # Controls for each actions
            # Generate/Cancel button - disabled until images are selected
        self.generate_button = tk.Button(frame, text="Generate", command=self.generate)
        if settings[KEY_CONTENT_FILE] is None or settings[KEY_STYLE_FILE] is None:
            self.generate_button.config (state = tk.DISABLED)
        self.generate_button.grid(row=1, column=0, pady = pad)

            # Content and style images
        self.content_image_label = tk.StringVar()
        self.content_image_label.set(self.display_text (KEY_CONTENT_FILE))
        tk.Button(frame, text="Select content image",
                command=self.select_content).grid(row=1, column=1, pady = pad)
        self.style_image_label = tk.StringVar()
        self.style_image_label.set(self.display_text (KEY_STYLE_FILE))
        tk.Button(frame, text="Select style image",
                  command=self.select_style).grid(row=1, column=2, pady = pad)

            # Number of epochs
        self.epochs = NumberEntry (frame, "Epochs", settings[KEY_EPOCHS], 1, 1000)
        self.epochs.grid(row=1, column=3, pady = pad)

        # Labels for the selected images
        tk.Label(frame, textvariable=self.content_image_label).grid(row=2, column=0, columnspan=2, sticky="ew", padx=pad)
        tk.Label(frame, textvariable=self.style_image_label).grid(row=2, column=2, columnspan=2, sticky="ew", padx=pad)

        # And the actual scaled images for settings[KEY_CONTENT_FILE] and settings[KEY_STYLE_FILE], 
        # scaled to IMAGE_WIDTH*DISPLAY_SCALE x IMAGE_HEIGHT*DISPLAY_SCALE
        width = int(IMAGE_WIDTH * DISPLAY_SCALE)
        height = int(IMAGE_HEIGHT * DISPLAY_SCALE)

        self.content_image = DisplayImage(frame, width, height)
        self.content_image.grid(row=3, column=0, columnspan=2, sticky="ew", padx=pad, pady=pad)
        content_file = settings[KEY_CONTENT_FILE]
        if content_file is not None and os.path.exists (content_file):
            self.content_image.set_image (settings[KEY_CONTENT_FILE])

        self.style_image = DisplayImage(frame, width, height)
        self.style_image.grid(row=3, column=2, columnspan=2, sticky="ew", padx=pad, pady=pad)
        style_file = settings[KEY_STYLE_FILE]
        if style_file is not None and os.path.exists (style_file):
            self.style_image.set_image (settings[KEY_STYLE_FILE])

        frame.pack(padx=pad, pady=pad)

        self.image_generator = ImageGenerator(self.textbox.writeln)

    def println (self, text):
        """Write a line of text output"""
        self.textbox.writeln (text)

    def printerr (self, text):
        """Write an error message"""
        self.textbox.write_error (text)

    def display_text (self, key : str) -> str:
        """Return the base file name for a key"""
        if key == KEY_CONTENT_FILE:
            text = "Content image: "
        else:
            text = "Style image: "
        if self.settings[key] is None:
            return text + "None"
        return text + os.path.basename(self.settings[key])

    def pop_up_image(self, image_file : str):
        """Display the image in a pop-up window"""
        image = Image.open(image_file)
        image.show()

    def generate_async (self):
        """Generate the image in a separate thread"""
        self.generate_button.config (text = "Cancel")
        try:
            save_settings(self.settings)
            content_img = self.settings[KEY_CONTENT_FILE]
            style_img = self.settings[KEY_STYLE_FILE]
            output_img = content_img.rsplit(".", 1)[0] + " styled as " + os.path.basename(style_img)
            self.image_generator.generate (content_img, style_img, output_img, IMAGE_WIDTH, self.epochs.get_value ())
            self.textbox.writeln ("Generated image: " + output_img)
            self.pop_up_image (output_img)
        except Exception as exc: # pylint: disable=broad-except
            self.printerr ("Error generating image: " + str(exc))
        finally:
            self.generate_button.config (text = "Generate")
            self.generate_button.config (state = tk.NORMAL)

    def generate (self):
        """Generate a new image (or cancel the current generation)"""
        current_button = self.generate_button.cget("text")
        if current_button == "Generate":
            self.generate_button.config (text = "Cancel")
            Thread (target = self.generate_async).start ()
        elif current_button == "Cancel":
            self.generate_button.config (state = tk.DISABLED)
            self.image_generator.cancel ()
        else:
            self.printerr ("Unknown button text: " + current_button)

    def select_image_file (self, key : str) -> None:
        """Select an image file and return the path"""
        file = filedialog.askopenfilename(initialdir = "~", title = "Select an image", filetype = [("Image files", "*.jpg *.jpeg")])
        if os.path.exists(file):
            self.settings[key] = file
            save_settings(self.settings)
            if self.settings[KEY_STYLE_FILE] is not None and self.settings[KEY_CONTENT_FILE] is not None:
                self.generate_button.config (state = tk.NORMAL)

    def select_content(self):
        """Select a content image file"""
        self.select_image_file (KEY_CONTENT_FILE)
        self.content_image_label.set (self.display_text(KEY_CONTENT_FILE))
        self.content_image.set_image (self.settings[KEY_CONTENT_FILE])

    def select_style(self):
        """Select a style image file"""
        self.select_image_file (KEY_STYLE_FILE)
        self.style_image_label.set (self.display_text(KEY_STYLE_FILE))
        self.content_image.set_image (self.settings[KEY_STYLE_FILE])

window = Root()
window.mainloop()
