"""
anonymizer.py - anonymize excel data exported from Forms
And put it in html format for easy viewing
"""

import os
import json
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext

# Configuration variables
SETTINGS_FILE = os.path.join (os.path.expanduser("~"), "anonymizer_settings.json")
DEFAULT_EXCLUDE_COLUMNS = "Start time,Completion time,Email,Name"
KEY_EXCLUDE_COLUMNS = "exclude_columns"
KEY_APPLICATIONS_FILE = "applications_file"

# save settings dictionary to SETTINGS_FILE
def save_settings (settings : dict):
    with open (SETTINGS_FILE, "w") as f:
        json.dump (settings, f)

# load settings dictionary from SETTINGS_FILE
def load_settings () -> dict:
    d = {}
    if os.path.exists (SETTINGS_FILE):
        with open (SETTINGS_FILE, "r") as f:
            d = json.load (f)

    if KEY_EXCLUDE_COLUMNS not in d:
        d[KEY_EXCLUDE_COLUMNS] = DEFAULT_EXCLUDE_COLUMNS
        save_settings (d)
    if KEY_APPLICATIONS_FILE not in d:
        d[KEY_APPLICATIONS_FILE] = "<none>"
        save_settings (d)

    return d
    
# create a dataframe from an excel file, on None if there is an error
def load_excel (filename : str) -> pd.DataFrame:
    try:
        return pd.read_excel (filename)
    except:
        return None

# save a dataframe to an excel file
def save_excel (df : pd.DataFrame, filename : str):
    df.to_excel (filename, index = False)

# get a valid file path from the user and store in settings
def get_file_path (settings : dict, key : str, file_description : str):
    while True:
        path = input (f"Enter the path to the {file_description}: ")
        if os.path.exists (path):
            settings[key] = path
            save_settings (settings)
            break
        else:
            print ("Invalid path. Please try again.")

# Generate an html file from the dataframe, excluding the columns in exclude_columns.
# Each element in a df row is output as the column header in an h3 tag, and the value in a p tag.
def create_anonymized_file (df : pd.DataFrame, exclude_columns : str, filename : str):
    # Iterate through each row in the dataframe
    with open (filename, "w") as f:
        # Write the opening html tags
        f.write ("<html>\n<body>\n")

        for index, row in df.iterrows ():
            # For each element in the row, output the column header in an h3 tag, and the value in a p tag
            for column in row.index:
                if column not in exclude_columns:
                    f.write (f"\t<h3>{column}</h3>\n\t<p>{row[column]}</p>\n")

            # Add a page break between rows
            f.write ("<br><br><hr>\n")

        # Write the closing html tags
        f.write ("</body>\n</html>")

def create_aggregated_file (df : pd.DataFrame, input_file : str, output_file : str):
    df = load_excel (input_file)

    # Remove all columns from the dataframe that are not numberic
    df = df.select_dtypes (include = ["number"])

    # Aggregate all column values grouped by column "ID"
    df = df.groupby ("ID").sum ()

    # Save to the output file
    save_excel (df, output_file)

def launch (filename : str):
    if os.name == "nt":
        os.startfile (filename)
    elif os.name == "posix":
        os.system ("open " + filename)

# Create a class for read-only text output
class ReadOnlyScrolledText (scrolledtext.ScrolledText):
    def __init__ (self, win : tk.Tk, w : int, h : int, pad : int = 0):
        super (ReadOnlyScrolledText, self).__init__ (win, wrap = tk.WORD, width = w, height = h, padx = pad, pady = pad)
        self.config (state = tk.DISABLED)

    def writeln (self, text):
        self.config (state = tk.NORMAL)
        self.insert (tk.END, text + "\n")
        self.see (tk.END)
        self.config (state = tk.DISABLED)

class ReadOnlyText (tk.Text):
    def __init__ (self, win : tk.Tk, text : str, pady : int = 0):
        super (ReadOnlyText, self).__init__ (win, height = 2, pady=pady)
        self.set_text(text)

    def set_text (self, text):
        self.config (state = tk.NORMAL)
        self.delete (1.0, tk.END)
        self.insert (tk.END, text)
        self.config (state = tk.DISABLED)

# Create the root window class
class Root (tk.Tk):
    def __init__ (self):
        super (Root, self).__init__ ()
        self.title ("Anonymizer")
        pad = 10
        settings = load_settings ()
        self.settings = settings

        # Create a frame to hold the widgets
        frame = tk.Frame (self, relief=tk.RAISED, borderwidth=1)

        # Create a text label to let folks know what to do
        tk.Label(frame, text="Welcome to the Excel anonymizer. What do you want to do?").grid(row=0, column = 0, columnspan=5, sticky="ew")

        # Create buttons for the four primary actions
        tk.Button(frame, text="Select spreadsheet", command=self.select_file)        .grid(row=1, column=0, pady = pad)
        tk.Button(frame, text="Configure columns",  command=self.configure_columns)  .grid(row=1, column=1, pady = pad)
        tk.Button(frame, text="Anonymize",          command=self.anonymize)          .grid(row=1, column=2, pady = pad)
        tk.Button(frame, text="View HTML file",     command=self.view_output)        .grid(row=1, column=3, pady = pad)
        tk.Button(frame, text="Help",               command=self.help)               .grid(row=1, column=4, pady = pad)

        # Show current configuration
        tk.Label(frame, text="Spreadsheet: ", anchor="w").grid(row=2, column=0, pady = pad, sticky="e")
        self.applications_file_label = ReadOnlyText(frame, settings[KEY_APPLICATIONS_FILE])
        self.applications_file_label.grid(row=2, column=1, columnspan = 4, pady = pad, sticky="w")

        tk.Label(frame, text="Anonymized file: ", justify=tk.LEFT).grid(row=3, column=0, pady = pad, sticky="e")
        self.output_file_label = ReadOnlyText(frame, text=Root.get_anonymized_filename(settings[KEY_APPLICATIONS_FILE]))
        self.output_file_label.grid(row=3, column=1, columnspan = 4, pady = pad, sticky="w")

        tk.Label(frame, text="Exclude columns: ", justify=tk.LEFT).grid(row=4, column=0, pady = pad, sticky="e")
        self.exclude_columns_label = tk.Label(frame, text=settings[KEY_EXCLUDE_COLUMNS], justify=tk.LEFT)
        self.exclude_columns_label.grid(row=4, column=1, columnspan = 4, pady = pad, sticky="w")

        # Create a read-only message box to display the file path
        self.textbox = ReadOnlyScrolledText(frame, 80, 10, pad)
        self.textbox.grid(row=5, columnspan=5, sticky="ew")

        frame.pack(padx=pad, pady=pad)

    @staticmethod
    def get_anonymized_filename (filename : str) -> str:
        return os.path.join (os.path.dirname (filename), "Anonymized " + os.path.basename (filename).rsplit(".", 1)[0] + ".html")
    
    def println (self, text):
        self.textbox.writeln (text)
                              
    def select_file(self):
        file = filedialog.askopenfilename(initialdir = "~", title = "Select a spreadsheet of applications", filetype = (("xlsx files", "*.xlsx"), ("all files", "*.*")))
        if os.path.exists(file):
            self.settings[KEY_APPLICATIONS_FILE] = file
            save_settings(self.settings)
            self.applications_file_label.set_text (file)
            self.output_file_label.set_text (Root.get_anonymized_filename(file))
        return file

    def configure_columns(self):
        pd = load_excel (self.settings[KEY_APPLICATIONS_FILE])
        if pd is None:
            self.println (f"Error loading file {self.settings[KEY_APPLICATIONS_FILE]}. Please check that the file exists and is a valid Excel file or configure a new file")
            return
        # Create a popup dialog to let the user select the columns to exclude
        dialog = tk.Toplevel (self)
        dialog.title ("Configure columns")
        dialog.geometry ("400x400")
        dialog.resizable (False, False)
        frame = tk.Frame (dialog, relief=tk.RAISED, borderwidth=1)
        frame.pack (fill=tk.BOTH, expand=True)
        tk.Label(frame, text="Select the columns to exclude from the anonymized file").pack (pady=10)
        listbox = tk.Listbox (frame, selectmode=tk.MULTIPLE)
        listbox.pack (fill=tk.BOTH, expand=True)
        for column in pd.columns:
            listbox.insert (tk.END, column)
        for column in self.settings[KEY_EXCLUDE_COLUMNS].split(","):
            listbox.selection_set (listbox.get (0, tk.END).index (column))
        tk.Button (frame, text="OK", command=lambda: self.configure_columns_ok (dialog, listbox)).pack (pady=10)

    def configure_columns_ok(self, dialog, listbox):
        excludes = []
        for i in listbox.curselection ():
            excludes.append (listbox.get (i))
        self.settings[KEY_EXCLUDE_COLUMNS] = ",".join (excludes)
        save_settings(self.settings)
        self.exclude_columns_label.config (text=self.settings[KEY_EXCLUDE_COLUMNS])
        dialog.destroy ()

    def anonymize(self):
        spreadsheet = self.settings[KEY_APPLICATIONS_FILE]
        html_file = Root.get_anonymized_filename (spreadsheet)
        pd = load_excel (spreadsheet)
        if pd is None:
            self.println (f"Error loading file {spreadsheet}. Please check that the file exists and is a valid Excel file or configure a new file")
            return
        create_anonymized_file (pd, self.settings[KEY_EXCLUDE_COLUMNS], html_file)
        self.println (f"Anonymized file saved to {html_file}")
        self.view_output()

    def view_output(self):
        spreadsheet = self.settings[KEY_APPLICATIONS_FILE]
        html_file = Root.get_anonymized_filename (spreadsheet)
        if os.path.exists (html_file):
            launch (html_file)
        else:
            self.println (f"File {html_file} does not exist. Please anonymize the spreadsheet first")
   
    def help(self):
        self.println ("First, select a spreadsheet to anonymize and configuring the columns to exclude during the anonymization process.")
        self.println ("After that, you can anonymize the spreadsheet. This process will create an HTML file with a separate page for each row " +
                      "in the spreadsheet formatted to show the column name and cell value for each cell in that row")
        self.println ("For more info, see https://github.com/marcshepard/Anonymizer/blob/master/README.md")

window = Root()
window.mainloop()
