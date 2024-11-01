import os
import config
import json
import requests
import pandas as pd
import tkinter as tk
from tkinter import ttk

# App logo
image_path = os.path.join('images', 'bus.png')

API_KEY = config.api_secret
API_REFRESH = config.api_refresh
APP_BLINKC = config.app_blinkc
ID_STATION = config.id_station
STATION = ID_STATION
headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'x-access-token': API_KEY
}


def fetch_data():
    try:
        response = requests.get(
            'https://api.golemio.cz/v2/pid/departureboards?aswIds='+ID_STATION+'&minutesBefore=0&minutesAfter=60&includeMetroTrains=false&airCondition=true&preferredTimezone=Europe_Prague&mode=departures&order=real&filter=none&skip=canceled&limit=10&total=10&offset=0',
            headers=headers,
            verify=False
        )
        response.raise_for_status()  # Check if the request was successful
        data = response.json()  # Parse the JSON response
        print(json.dumps(data, indent=4))  # Pretty-print the JSON data
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        data = None
    except Exception as err:
        print(f'Other error occurred: {err}')
        data = None

    if data:
        brumla_depart = data['departures']

        departures = [
            {
                'short_name': item['route']['short_name'],
                'is_wheelchair_accessible': '♿' if item['trip']['is_wheelchair_accessible'] else '',
                'is_air_conditioned': '❆' if item['trip']['is_air_conditioned'] else '',
                'headsign': item['trip']['headsign'],
                'name': item['last_stop']['name'],
                'minutes': item['departure_timestamp']['minutes']
            }
            for item in brumla_depart
        ]

        df_departures = (pd.DataFrame(departures, columns=['short_name', 'is_wheelchair_accessible', 'is_air_conditioned', 'headsign', 'name', 'minutes']))
        df_departures = df_departures.fillna('')

        # Clear the existing data in the Treeview widget
        for row in tree.get_children():
            tree.delete(row)

        # Add the new data to the Treeview widget
        for row in df_departures.itertuples(index=False):
            tree.insert('', 'end', values=row)

    # Schedule the fetch_data function to refresh the app after x seconds (x milliseconds / 1000 = x seconds)
    # Defined in config file as 'API_REFRESH'
    root.after(API_REFRESH, fetch_data)


# Function to update font size, column widths, and row heights based on window size
def update_font_size(event):
    width = event.width
    height = event.height
    new_size = min(max(int(width / 65), 45), 45)  # Adjust these values as needed
    # new_size = min(max(int(width / 50), 10), 20)  # Adjust these values as needed
    row_height = max(int(height / 97), 97)  # Adjust these values as needed

    style.configure('Treeview', font=('Helvetica', new_size), rowheight=row_height)
    style.configure('Treeview.Heading', font=('Helvetica', new_size + 2, 'bold'))

    # Update column widths proportionally
    tree.column('Route', width=int(width * 0.09))
    tree.column('Acs', width=int(width * 0.05))
    tree.column('AC', width=int(width * 0.05))
    tree.column('Destination', width=int(width * 0.315))
    tree.column('Last Position', width=int(width * 0.315))
    tree.column('Time', width=int(width * 0.08))


def exit_fullscreen(event=None):
    root.attributes('-fullscreen', False)


def enter_fullscreen(event=None):
    root.attributes('-fullscreen', True)


# Create the main window
root = tk.Tk()
img = tk.PhotoImage(file=image_path)
root.iconphoto(False, img)
root.title('Brumlovka Departure Board')
root.configure(bg='black')  # Set the background color
root.attributes('-fullscreen', True)  # Start in fullscreen mode
root.bind('<Escape>', exit_fullscreen)  # Exit fullscreen on Escape key press
root.bind('<F11>', enter_fullscreen)  # Enter fullscreen on F11 key press
root.focus_set()  # Ensure the root window has focus

# Configure the Treeview widget
style = ttk.Style()
style.theme_use('default')
style.configure('Treeview',
                background='black',
                foreground='white',
                fieldbackground='black')
style.configure('Treeview.Heading',
                background='black',
                foreground='white')

# Create a Treeview widget
tree = ttk.Treeview(root)

# Define the columns
tree['columns'] = ['Route', 'Acs', 'AC', 'Destination', 'Last Position', 'Time']
tree['show'] = 'headings'

# Define the column headings
for column in tree['columns']:
    tree.heading(column, text=column)

# Define the column widths and alignments
tree.column('Route', anchor='center')
tree.column('Acs', anchor='center')
tree.column('AC', anchor='center')
tree.column('Destination', anchor='w')
tree.column('Last Position', anchor='w')
tree.column('Time', anchor='center')


# Function to blink the row
def blink_row(item, toggle):
    if item in tree.get_children():
        if toggle:
            tree.item(item, tags=('blink',))
        else:
            tree.item(item, tags=('no_blink',))
        root.after(500, blink_row, item, not toggle)


# Function to check the 'Time' value and start blinking if necessary
def check_time_and_blink():
    for item in tree.get_children():
        time_value = tree.item(item, 'values')[5]
        if time_value == '<1':
            blink_row(item, True)
    root.after(1000, check_time_and_blink)


# Add tags for blinking effect, blink color defined in config file
tree.tag_configure('blink', background=APP_BLINKC)
tree.tag_configure('no_blink', background='black')

# Pack the Treeview widget
tree.pack(expand=True, fill='both')

# Bind the configure event to update font size, column widths, and row heights
root.bind('<Configure>', update_font_size)

# Fetch data initially and start the refresh loop
fetch_data()

# Start checking the 'Time' values
check_time_and_blink()

# Run the application
root.mainloop()
