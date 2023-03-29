import pyautogui
import keyboard
import time
is_ready = False
while True:

    if keyboard.is_pressed('q'):
        is_ready = True

    while is_ready:
        pyautogui.click()

        if keyboard.is_pressed('w'):
            break