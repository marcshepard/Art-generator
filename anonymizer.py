"""
anonymizer.py - anonymize data exported from Forms for review
"""

import os
import json
import pandas as pd

SETTINGS_FILE = os.path.join (os.path.expanduser("~"), "anonymizer_settings.json")

# save settings dictionary to SETTINGS_FILE
def save_settings (settings : dict):
    with open (SETTINGS_FILE, "w") as f:
        json.dump (settings, f)

# load settings dictionary from SETTINGS_FILE
def load_settings () -> dict:
    if os.path.exists (SETTINGS_FILE):
        with open (SETTINGS_FILE, "r") as f:
            return json.load (f)
    else:
        return {}
    
# create a dataframe from an excel file, on None if there is an error
def load_excel (filename : str) -> pd.DataFrame:
    try:
        return pd.read_excel (filename)
    except:
        return None

# save a dataframe to an excel file
def save_excel (df : pd.DataFrame, filename : str):
    df.to_excel (filename, index = False)

# view all settings and let user change them
def change_settings (settings : dict):
    print ("Current settings:")
    for key, value in settings.items ():
        print ("\t{}: {}".format (key, value))
    print ("Enter a new value for a setting, or just press enter to keep the current value.")
    for key, value in settings.items ():
        new_value = input ("{} [{}]: ".format (key, value))
        if new_value != "":
            settings[key] = new_value
    save_settings (settings)

# get a valid file path from the user and store in settings
def get_file_path (settings : dict, key : str, file_description : str):
    while True:
        path = input (f"Enter the path to the {file_description}: ")
        print (path)
        print (os.path.join (os.getcwd(), path))
        print (os.path.join (os.path.expanduser("~"), path))
        if os.path.exists (path):
            settings[key] = path
            save_settings (settings)
            break
        elif os.path.exists (os.path.join (os.getcwd(), path)):
            settings[key] = os.path.join (os.getcwd(), path)
            save_settings (settings)
            break
        elif os.path.exists(os.path.join (os.path.expanduser("~"), path)):
            settings[key] = os.path.join (os.path.expanduser("~"), path)
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
                    f.write (f"\t<h3>{column}</h3>\n<p>{row[column]}</p>\n")

            # Add a page break between rows
            f.write ("<br><br><hr>\n")

        # Write the closing html tags
        f.write ("</body>\n</html>")

def main():
    # load settings
    settings = load_settings ()
    while True:
        command = input ("What do you want to do (type enter for options)? ")
        if command == "a":
            if "applications_file" not in settings:
                get_file_path (settings, "applications_file", "Excel file of honor society applications exported from Forms")
            pd = load_excel (settings["applications_file"])
            if pd is None:
                print (f"Error loading file {settings['applications_file']}. Please check that the file exists and is a valid Excel file. Type s to configure a new file")
                continue
            if "exclude_columns" not in settings:
                settings["exclude_columns"] = input ("Enter a comma-separated list of columns to exclude from the anonymized file: ")
                save_settings (settings)
            # Set anonymized_applications_file to the same path as applications_file, but with "anonymized_" appended to the filename, and with a .html extensio
            settings["anonymized_applications_file"] = os.path.join (os.path.dirname (settings["applications_file"]), "anonymized_" + \
                                                                     os.path.basename (settings["applications_file"]).rsplit (".", 1)[0] + ".html")
            save_settings (settings)
            create_anonymized_file (pd, settings["exclude_columns"], settings["anonymized_applications_file"])
        elif command == "s" and len(settings) > 0:
            change_settings(settings)
        elif command == "agg":
            print ("Aggregate not yet implemented")
        elif command == "q":
            break
        else:
            print ("Valid commands are:")
            print ("\ta\tanonymize")
            if (len(settings) > 0):
                print ("\ts\tview or change settings")
            print ("\tagg\taggregate")
            print ("\tq\tquit")
            print ("For more info, see https://github.com/marcshepard/Anonymizer/blob/master/README.md")

main()
