from threading import Event
import PySimpleGUI


import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Column

all_sites={
    0:"eefewfew",
    1:"defefef"
}

for site in all_sites:
    scrape_col = []
    scrape_col.append([site])
print(scrape_col)
layout = [
    [sg.Column(scrape_col)],
    [sg.Cancel()],
]

# create the Window
window = sg.Window('Custom Progress Meter', layout,finalize=True)
while True:
    event,values=window.read()
# loop that would normally do something useful