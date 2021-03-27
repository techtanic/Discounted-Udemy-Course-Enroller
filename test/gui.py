import json
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Window


with open('test.json') as f:
    config = json.load(f)
config['list'] = '\n'.join(config['list'])

layout = [
    [sg.Multiline(default_text=config['list'],key='ml')],
    [sg.Button('Save', key='save')]
]

window = sg.Window("Test", layout)
event, values = window.read()

if event == None:
    window.close()

elif event == 'save':
    config['list'] = values['ml'].split()
    with open('test.json','w') as f:
        json.dump(config,f,indent=4)
