import colorama
import random

def banner():
    banner = '''
 _     _ _____   _______ ______  _     _     ______ ______  _   _ _ 
| |   | (____ \ (_______)  ___ \| |   | |   / _____|_____ \( ) | | |
| |   | |_   \ \ _____  | | _ | | |___| |  | /      _____) )/__| | |
| |   | | |   | |  ___) | || || |\_____/   | |     |  ____//___)_|_|
| |___| | |__/ /| |_____| || || |  ___     | \_____| |    |___ |_ _ 
 \______|_____/ |_______)_||_||_| (___)     \______)_|    (___/|_|_|
'''
    bad_colors = ['BLACK', 'WHITE', 'LIGHTBLACK_EX', 'RESET']
    codes = vars(colorama.Fore)
    colors = [codes[color] for color in codes if color not in bad_colors]
    colored_chars = [random.choice(colors) + char for char in banner]

    return ''.join(colored_chars)
