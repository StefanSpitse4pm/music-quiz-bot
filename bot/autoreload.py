
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from time import sleep
import subprocess

VENV = "/home/tagordo/snap/code/179/.local/share/virtualenvs/music-quiz-bot-PZw_aL80/bin/python"

class ReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"🔄 Detected change in {event.src_path}, restarting bot...")
            self.restart()


    def restart(self):
        global bot_process
        if bot_process:
            bot_process.terminate()
            bot_process.wait()            
        bot_process = subprocess.Popen([VENV, "bot/app.py"])

observer = Observer()

for folder in ["bot/cogs", "bot/utils"]:
    observer.schedule(ReloadHandler(), path=folder, recursive=True)

observer.start()
bot_process = subprocess.Popen([VENV, "bot/app.py"])
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()