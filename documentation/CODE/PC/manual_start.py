import subprocess
import pygetwindow as gw
import pyautogui
import time

# Launch both scripts
process1 = subprocess.Popen(['python', 'camerafeed_pc.py'])
process2 = subprocess.Popen(['python', 'manual_pc.py'])

# Give some time for the windows to open
time.sleep(5)

# Get the windows of both scripts by title
windows = gw.getAllTitles()
script1_window = None
script2_window = None

# Loop to find matching windows
for win in windows:
    if 'Script1 Window Title' in win:  # Replace with actual window title
        script1_window = gw.getWindowsWithTitle(win)[0]
    elif 'Script2 Window Title' in win:  # Replace with actual window title
        script2_window = gw.getWindowsWithTitle(win)[0]

# Ensure both windows were found
if script1_window and script2_window:
    # Move the first window to the left side
    script1_window.moveTo(0, 0)
    script1_window.resizeTo(pyautogui.size().width // 2, pyautogui.size().height)
    
    # Move the second window to the right side
    script2_window.moveTo(pyautogui.size().width // 2, 0)
    script2_window.resizeTo(pyautogui.size().width // 2, pyautogui.size().height)
else:
    print("Could not find the windows")