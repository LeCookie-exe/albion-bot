from abc import ABC
import win32gui
import win32con
import logging
import re

from . import Capture, ScreenInformation

# Configuration du logging
logger = logging.getLogger("WindowsCapture")

class WindowsCapture(Capture, ABC):

    def __init__(self, window_name=Capture.WINDOWS_NAME):
        super().__init__(window_name)

        self.hwnd = self.__get_window_id()

        if self.hwnd == 0:
            # Aucune fenêtre trouvée avec le nom exact, essayer de façon plus flexible
            logger.warning(f"Fenêtre '{window_name}' non trouvée, tentative de recherche plus flexible")
            self.hwnd = self.__find_similar_window(window_name)

        if self.hwnd == 0:
            raise Exception(f'Impossible de trouver une fenêtre correspondant à {window_name}')

        self.window = self.get_window_information()

        self.grab_coordinates = {
            "top": self.window.top,
            "left": self.window.left,
            "width": self.window.width,
            "height": self.window.height
        }

        logger.info(f"Fenêtre capturée: '{win32gui.GetWindowText(self.hwnd)}' (hwnd: {self.hwnd})")

    def get_window_information(self):
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
            raise

    def __get_window_id(self):
        """Recherche la fenêtre par son nom exact"""
        try:
            hwnd = win32gui.FindWindow(None, self.windowName)
            if hwnd != 0:
                logger.info(f"Fenêtre trouvée avec le nom exact: '{self.windowName}'")
            return hwnd
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de la fenêtre par nom exact: {e}")
            return 0

    def __find_similar_window(self, window_name):
        """Recherche une fenêtre avec un nom similaire"""
        # Convertir le nom de fenêtre recherché en minuscule et créer une regex
        search_term = window_name.lower()
        # Créer des termes de recherche basés sur le nom original
        search_terms = ['albion', 'online', 'client', 'game']

        # Mots-clés spécifiques qui pourraient être dans le titre de la fenêtre
        candidate_windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    title_lower = title.lower()
                    # Vérifier si l'un des termes est présent dans le titre
                    matches = sum(1 for term in search_terms if term in title_lower)
                    if matches > 0:
                        # Vérifier si c'est une fenêtre principale
                        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                        if style & win32con.WS_OVERLAPPEDWINDOW:
                            candidate_windows.append({
                                'hwnd': hwnd,
                                'title': title,
                                'matches': matches
                            })
            return True

        try:
            win32gui.EnumWindows(callback, None)

            if candidate_windows:
                # Trier par nombre de correspondances (descendant)
                candidate_windows.sort(key=lambda w: w['matches'], reverse=True)
                best_match = candidate_windows[0]
                logger.info(f"Fenêtre similaire trouvée: '{best_match['title']}' avec {best_match['matches']} termes correspondants")
                return best_match['hwnd']

            return 0
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de fenêtre similaire: {e}")
            return 0
