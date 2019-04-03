import time
import random
import subprocess
from pathlib import Path
from SMWinservice import SMWinservice

class import_service(SMWinservice):
    _svc_name_ = "import_service"
    _svc_display_name_ = "Google Student Importer"
    _svc_description_ = "Runs google import program. See readme at https://github.com/gospelg/Google-Import"

    def start(self):
        self.isrunning = True

    def stop(self):
        self.isrunning = False

    def main(self):
        program_path = "C:\\users\\crosbyg\\desktop\\Google-Import-master\\google_import4131.exe"
        while self.isrunning:
            hour = time.strftime('%H')
            if hour == '23':
                subprocess.call(program_path)
                time.sleep(3600)
                hour = time.strftime('%H')
            else:
                time.sleep(2700)
                hour = time.strftime('%H')

if __name__ == '__main__':
    import_service.parse_command_line()
