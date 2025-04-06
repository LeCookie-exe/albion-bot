import os
import json
import psutil
import numpy as np
from PIL import ImageGrab
import win32gui
import win32process
import win32con
import logging
from . import Capture, ScreenInformation

# Configuration du logging
logger = logging.getLogger("ProcessCapture")

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
            logger.info(f"Fenêtre trouvée et capturée: {win32gui.GetWindowText(self.hwnd)} (PID: {self.process_info.get('pid', 'inconnu')})")
        else:
            # Utiliser WindowsCapture comme fallback
            logger.warning("Impossible de trouver la fenêtre par PID, tentative par nom de fenêtre...")
            self._try_fallback_to_window_name(window_name)

    def _try_fallback_to_window_name(self, window_name):
        """Essaye de trouver la fenêtre par son nom si la recherche par PID échoue"""
        try:
            self.hwnd = win32gui.FindWindow(None, window_name)
            if self.hwnd:
                self.window = self.get_window_information()
                self.grab_coordinates = {
                    "top": self.window.top,
                    "left": self.window.left,
                    "width": self.window.width,
                    "height": self.window.height
                }
                logger.info(f"Fenêtre trouvée par nom: {window_name} (hwnd: {self.hwnd})")
                return
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par nom de fenêtre: {e}")

        # Si tout échoue, utiliser l'écran entier
        self.window = ScreenInformation(0, 0, 1920, 1080)
        self.grab_coordinates = {
            "top": 0,
            "left": 0,
            "width": 1920,
            "height": 1080
        }
        logger.warning("Aucune fenêtre trouvée, utilisation de l'écran entier.")

    def _load_process_info(self):
        """Charge les informations du processus depuis le fichier JSON"""
        try:
            # Vérifier d'abord dans le répertoire Application
            file_paths = ['albion_process.json', 'Application/albion_process.json']

            for path in file_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        config = json.load(f)
                        process_info = config.get('process', {})
                        logger.info(f"Informations du processus chargées depuis {path}: PID={process_info.get('pid', 'inconnu')}")
                        return process_info

            logger.warning("Aucun fichier albion_process.json trouvé")
            return None
        except Exception as e:
            logger.error(f"Erreur lors du chargement des informations du processus: {e}")
            return None

    def _find_window_by_process(self):
        """Trouve la fenêtre appartenant au PID spécifié"""
        if not self.process_info or 'pid' not in self.process_info:
            logger.warning("Informations de processus manquantes ou incomplètes")
            return None

        pid = self.process_info['pid']
        windows = []

        def callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    # Récupérer le style de la fenêtre pour vérifier si c'est une fenêtre principale
                    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                    has_title = win32gui.GetWindowText(hwnd)

                    if has_title or (style & win32con.WS_OVERLAPPEDWINDOW):
                        windows_list.append({
                            'hwnd': hwnd,
                            'title': win32gui.GetWindowText(hwnd),
                            'style': style
                        })
            return True

        # Vérifier si le processus existe toujours
        try:
            process = psutil.Process(pid)
            if not process.is_running():
                logger.error(f"Le processus avec PID {pid} n'est plus en cours d'exécution.")
                return None

            # Chercher toutes les fenêtres du processus
            win32gui.EnumWindows(callback, windows)

            if windows:
                # Trier les fenêtres pour favoriser celles avec titre et avec style de fenêtre principale
                windows.sort(key=lambda w: (
                    len(w['title']) > 0,  # Préférer les fenêtres avec titre
                    w['style'] & win32con.WS_OVERLAPPEDWINDOW,  # Préférer les fenêtres principales
                    len(w['title'])  # À titre égal, préférer les titres plus longs
                ), reverse=True)

                # Utiliser la première fenêtre dans la liste triée
                best_window = windows[0]
                logger.info(f"Fenêtre trouvée: '{best_window['title']}' (PID: {pid}, HWND: {best_window['hwnd']})")
                return best_window['hwnd']
            else:
                logger.warning(f"Aucune fenêtre visible trouvée pour le PID {pid}.")
                return None

        except psutil.NoSuchProcess:
            logger.error(f"Le processus avec PID {pid} n'existe pas.")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de fenêtre: {e}")
            return None

    def get_window_information(self):
        """Récupère les informations de la fenêtre"""
        if not self.hwnd:
            # Retourner des informations d'écran par défaut si aucune fenêtre n'est trouvée
            logger.warning("Aucun handle de fenêtre disponible, utilisation de dimensions par défaut")
            return ScreenInformation(0, 0, 1920, 1080)

        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            # Vérifier si la fenêtre est minimisée
            if rect[0] <= -32000 or rect[1] <= -32000:
                logger.warning("La fenêtre semble être minimisée, tentative de restauration")
                # Tentative de restauration de la fenêtre
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                # Récupérer à nouveau les dimensions après restauration
                rect = win32gui.GetWindowRect(self.hwnd)

            info = ScreenInformation(
                top=rect[1],
                left=rect[0],
                width=rect[2] - rect[0],
                height=rect[3] - rect[1]
            )
            logger.info(f"Dimensions de la fenêtre: {info}")
            return info
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations de la fenêtre: {e}")
            return ScreenInformation(0, 0, 1920, 1080)

    def __get_window_id(self):
        """Non utilisé mais requis par la classe abstraite"""
        return self.hwnd if self.hwnd else 0
