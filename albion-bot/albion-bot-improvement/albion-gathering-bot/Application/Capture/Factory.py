from .Windows import WindowsCapture
from .process_capture import ProcessCapture
from platform import system
import os
import logging

# Configuration du logging
logger = logging.getLogger("CaptureFactory")

class CaptureFactory:
    capture = None

    def __init__(self, window_name="Albion Online Client"):
        self.windowName = window_name

        # Vérifier si le fichier d'informations de processus existe
        if os.path.exists('albion_process.json') or os.path.exists('Application/albion_process.json'):
            try:
                # Essayer d'utiliser la capture basée sur le processus
                logger.info("Tentative de capture par PID via ProcessCapture")
                self.capture = ProcessCapture(window_name=window_name)

                # Vérifier si la capture a été réussie (si un hwnd valide a été trouvé)
                if not hasattr(self.capture, 'hwnd') or not self.capture.hwnd:
                    logger.warning("ProcessCapture n'a pas trouvé de fenêtre valide, fallback à WindowsCapture")
                    self._try_windows_capture(window_name)

            except Exception as e:
                logger.error(f"Erreur lors de l'utilisation de ProcessCapture: {e}")
                self._try_windows_capture(window_name)
        elif system() == "Windows":
            # Utiliser la capture Windows standard
            self._try_windows_capture(window_name)
        else:
            error_msg = f"Le système d'exploitation {system()} n'est pas pris en charge."
            logger.error(error_msg)
            raise NotImplementedError(error_msg)

    def _try_windows_capture(self, window_name):
        """Essaie d'utiliser WindowsCapture comme méthode de fallback"""
        try:
            logger.info(f"Tentative de capture par nom de fenêtre '{window_name}' via WindowsCapture")
            self.capture = WindowsCapture(window_name=window_name)
            logger.info("Capture par WindowsCapture réussie")
        except Exception as e:
            logger.error(f"Échec de WindowsCapture: {e}")
            # Si aucune des méthodes ne fonctionne, lever une exception
            raise Exception(f"Impossible de capturer la fenêtre '{window_name}': {e}")
