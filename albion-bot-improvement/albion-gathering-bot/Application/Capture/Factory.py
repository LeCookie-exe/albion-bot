from .Windows import WindowsCapture
from .process_capture import ProcessCapture
from platform import system
import os

class CaptureFactory:
    capture = None

    def __init__(self, window_name="Albion Online Client"):
        self.windowName = window_name
        
        # Vérifier si le fichier d'informations de processus existe
        if os.path.exists('albion_process.json'):
            # Utiliser la capture basée sur le processus
            self.capture = ProcessCapture(window_name=window_name)
        elif system() == "Windows":
            # Utiliser la capture Windows standard
            self.capture = WindowsCapture(window_name=window_name)
        else:
            raise NotImplementedError(f"Le système d'exploitation {system()} n'est pas pris en charge.")