import os
import json
import psutil
import numpy as np
from PIL import ImageGrab
import win32gui
import win32process
from . import Capture, ScreenInformation

class ProcessCapture(Capture):
    """Capture d'écran basée sur le PID du processus"""

    def __init__(self, window_name=Capture.WINDOWS_NAME):
        super().__init__(window_name)
        
        # Essayer de charger les informations du processus depuis le fichier
        self.process_info = self._load_process_info()
        self.hwnd = self._find_window_by_process()
        
        # Si un handle de fenêtre est trouvé, récupérer ses informations
        if self.hwnd:
            self.window = self.get_window_information()
            self.grab_coordinates = {
                "top": self.window.top,
                "left": self.window.left,
                "width": self.window.width,
                "height": self.window.height
            }
        else:
            # Utiliser les coordonnées par défaut si aucune fenêtre n'est trouvée
            self.window = ScreenInformation(0, 0, 1920, 1080)
            self.grab_coordinates = {
                "top": 0,
                "left": 0,
                "width": 1920,
                "height": 1080
            }
            print("Aucune fenêtre trouvée, utilisation de l'écran entier.")
    
    def _load_process_info(self):
        """Charge les informations du processus depuis le fichier JSON"""
        try:
            if os.path.exists('albion_process.json'):
                with open('albion_process.json', 'r') as f:
                    config = json.load(f)
                    return config.get('process', {})
            return None
        except Exception as e:
            print(f"Erreur lors du chargement des informations du processus: {e}")
            return None
    
    def _find_window_by_process(self):
        """Trouve la fenêtre appartenant au PID spécifié"""
        if not self.process_info or 'pid' not in self.process_info:
            return None
            
        pid = self.process_info['pid']
        result = None
        
        def callback(hwnd, pid):
            nonlocal result
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    text = win32gui.GetWindowText(hwnd)
                    if text:  # Ignorer les fenêtres sans titre
                        result = hwnd
                        return False
            return True
            
        # Vérifier si le processus existe toujours
        try:
            process = psutil.Process(pid)
            if not process.is_running():
                print(f"Le processus avec PID {pid} n'est plus en cours d'exécution.")
                return None
                
            # Chercher la fenêtre principale du processus
            win32gui.EnumWindows(callback, pid)
            
            if result:
                print(f"Fenêtre trouvée: {win32gui.GetWindowText(result)} (PID: {pid})")
            else:
                print(f"Aucune fenêtre visible trouvée pour le PID {pid}.")
                
            return result
            
        except psutil.NoSuchProcess:
            print(f"Le processus avec PID {pid} n'existe pas.")
            return None
    
    def get_window_information(self):
        """Récupère les informations de la fenêtre"""
        if not self.hwnd:
            # Retourner des informations d'écran par défaut si aucune fenêtre n'est trouvée
            return ScreenInformation(0, 0, 1920, 1080)
            
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            return ScreenInformation(
                top=rect[1],
                left=rect[0],
                width=rect[2] - rect[0],
                height=rect[3] - rect[1]
            )
        except Exception as e:
            print(f"Erreur lors de la récupération des informations de la fenêtre: {e}")
            return ScreenInformation(0, 0, 1920, 1080)
            
    def __get_window_id(self):
        """Non utilisé mais requis par la classe abstraite"""
        return self.hwnd if self.hwnd else 0