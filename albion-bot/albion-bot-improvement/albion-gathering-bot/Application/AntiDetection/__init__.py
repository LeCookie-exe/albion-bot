"""
Module pour éviter la détection par l'anti-cheat Easy Anti-Cheat.
Ce module contient des fonctions et classes pour réduire les risques d'être détecté.
"""

import os
import sys
import random
import time
import logging
import psutil
from threading import Thread
import ctypes
import win32api
import win32con
import win32process
import win32gui
import pyautogui

# Configuration du logging
logger = logging.getLogger("AntiDetection")

class AntiDetectionManager:
    """
    Gestionnaire des techniques anti-détection pour l'anti-cheat.
    """

    # Constantes pour les fonctionnalités anti-détection
    RANDOMIZE_DELAYS = True
    AVOID_PATTERNS = True
    HUMAN_LIKE_MOUSE = True

    def __init__(self, process_name="AlbionClient.exe"):
        """
        Initialise le gestionnaire anti-détection.

        :param process_name: Nom du processus du jeu
        """
        self.process_name = process_name
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_action_time = time.time()

        # Facteurs humains
        self.max_clicks_per_minute = random.randint(70, 120)  # Nombre max de clics par minute
        self.mouse_speed_variance = random.uniform(0.3, 0.6)  # Variance de vitesse de la souris

        # Caractéristiques uniques pour chaque instance
        self.unique_id = self._generate_unique_id()

        logger.info(f"Gestionnaire anti-détection initialisé (ID: {self.unique_id[:8]})")

    def _generate_unique_id(self):
        """Génère un identifiant unique pour cette session"""
        import uuid
        import socket
        from datetime import datetime

        # Mélanger différentes sources d'unicité
        system_info = f"{socket.gethostname()}-{os.getpid()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        unique_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, system_info))

        return unique_id

    def start_monitoring(self):
        """Démarre la surveillance en arrière-plan"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_thread = Thread(target=self._monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        logger.info("Surveillance anti-détection démarrée")

    def stop_monitoring(self):
        """Arrête la surveillance"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
            self.monitoring_thread = None

        logger.info("Surveillance anti-détection arrêtée")

    def _monitor_loop(self):
        """Boucle de surveillance en arrière-plan"""
        while self.is_monitoring:
            try:
                # Vérifier si EAC est actif
                if self._is_eac_present():
                    logger.debug("EAC détecté actif")

                # Vérifier le temps depuis la dernière action
                idle_time = time.time() - self.last_action_time
                if idle_time > 300:  # 5 minutes
                    # Ajouter des micro-mouvements pour éviter la détection d'absence d'activité
                    self._simulate_micro_activity()

                # Pause aléatoire entre les vérifications
                time.sleep(random.uniform(5, 15))

            except Exception as e:
                logger.error(f"Erreur dans la boucle de surveillance: {e}")
                time.sleep(30)  # Pause plus longue en cas d'erreur

    def _is_eac_present(self):
        """Vérifie si EAC est actif dans les processus"""
        eac_processes = ["EasyAntiCheat.exe", "EACService.exe"]

        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in eac_processes:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        return False

    def _simulate_micro_activity(self):
        """Simule une micro-activité pour éviter la détection d'inactivité"""
        try:
            # Micro-mouvement presque imperceptible
            current_x, current_y = pyautogui.position()
            offset_x = random.uniform(-2, 2)
            offset_y = random.uniform(-2, 2)

            # Mouvement lent et subtil
            pyautogui.moveTo(current_x + offset_x, current_y + offset_y,
                            duration=random.uniform(0.5, 1.0))

            # Retour presque à la position d'origine
            pyautogui.moveTo(current_x, current_y,
                            duration=random.uniform(0.5, 1.0))

            logger.debug("Micro-activité simulée")

            # Mettre à jour le temps de dernière action
            self.last_action_time = time.time()

        except Exception as e:
            logger.error(f"Erreur lors de la simulation de micro-activité: {e}")

    def update_last_action_time(self):
        """Met à jour le temps de la dernière action"""
        self.last_action_time = time.time()

    def get_human_mouse_duration(self):
        """
        Renvoie une durée 'humaine' pour le mouvement de la souris
        basée sur la distance parcourue
        """
        if not self.HUMAN_LIKE_MOUSE:
            return 0.1  # Valeur par défaut

        # Ajouter une variance aléatoire pour simuler un humain
        base_duration = random.uniform(0.2, 0.4)
        variance = random.uniform(-self.mouse_speed_variance, self.mouse_speed_variance)

        return max(0.1, base_duration + variance)

    def randomize_delay(self, base_delay):
        """
        Randomise un délai pour éviter des motifs détectables

        :param base_delay: Délai de base en secondes
        :return: Délai randomisé
        """
        if not self.RANDOMIZE_DELAYS:
            return base_delay

        # Ajouter une variance de ±30% au délai
        variance_factor = random.uniform(0.7, 1.3)
        randomized_delay = base_delay * variance_factor

        # Ajouter occasionnellement un délai supplémentaire plus important (5% de chance)
        if random.random() < 0.05:
            randomized_delay += random.uniform(0.2, 1.0)

        return randomized_delay

    def get_safe_coordinates(self, x, y, screen_width=None, screen_height=None):
        """
        Renvoie des coordonnées sécurisées en ajoutant une légère variation
        et en s'assurant qu'elles restent dans les limites de l'écran

        :param x: Coordonnée X cible
        :param y: Coordonnée Y cible
        :return: Tuple (x, y) modifié
        """
        if not self.AVOID_PATTERNS:
            return x, y

        # Obtenir les dimensions de l'écran si non fournies
        if screen_width is None or screen_height is None:
            screen_width, screen_height = pyautogui.size()

        # Ajouter une variation aléatoire (±5 pixels)
        variation_x = random.uniform(-5, 5)
        variation_y = random.uniform(-5, 5)

        # S'assurer que les coordonnées restent dans les limites de l'écran
        safe_x = max(0, min(screen_width - 1, x + variation_x))
        safe_y = max(0, min(screen_height - 1, y + variation_y))

        return safe_x, safe_y

    def human_like_click(self, x, y, right_click=False):
        """
        Effectue un clic avec un comportement humain

        :param x: Coordonnée X
        :param y: Coordonnée Y
        :param right_click: Si True, effectue un clic droit, sinon clic gauche
        """
        try:
            # Obtenir des coordonnées sécurisées
            safe_x, safe_y = self.get_safe_coordinates(x, y)

            # Obtenir une durée humaine pour le mouvement
            duration = self.get_human_mouse_duration()

            # Mouvement avec trajectoire non linéaire
            pyautogui.moveTo(
                safe_x,
                safe_y,
                duration=duration,
                tween=pyautogui.easeOutQuad
            )

            # Délai avant le clic (simuler le temps de réaction)
            time.sleep(self.randomize_delay(0.1))

            # Effectuer le clic
            button = 'right' if right_click else 'left'
            pyautogui.click(button=button)

            # Mettre à jour le temps de dernière action
            self.update_last_action_time()

            logger.debug(f"Clic humain effectué à ({safe_x:.1f}, {safe_y:.1f})")

        except Exception as e:
            logger.error(f"Erreur lors du clic humain: {e}")

    def get_window_visibility(self, window_handle):
        """
        Vérifie si une fenêtre est visible et active

        :param window_handle: Handle de la fenêtre
        :return: True si la fenêtre est visible et active, False sinon
        """
        if window_handle == 0:
            return False

        # Vérifier si la fenêtre est visible
        if not win32gui.IsWindowVisible(window_handle):
            return False

        # Vérifier si la fenêtre est minimisée
        placement = win32gui.GetWindowPlacement(window_handle)
        if placement[1] == win32con.SW_SHOWMINIMIZED:
            return False

        # Vérifier si la fenêtre est active (au premier plan)
        foreground_window = win32gui.GetForegroundWindow()
        if foreground_window != window_handle:
            return False

        return True

    def is_game_window_active(self):
        """
        Vérifie si la fenêtre du jeu est active et visible

        :return: True si la fenêtre du jeu est active, False sinon
        """
        try:
            # Trouver la fenêtre Albion Online
            window_handle = win32gui.FindWindow(None, "Albion Online Client")
            if window_handle == 0:
                return False

            return self.get_window_visibility(window_handle)

        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la fenêtre du jeu: {e}")
            return False

    def add_memory_noise(self):
        """
        Ajoute du 'bruit' à la mémoire pour compliquer les scans de mémoire
        """
        try:
            # Créer des tableaux de données aléatoires
            num_arrays = random.randint(5, 15)
            arrays = []

            for _ in range(num_arrays):
                size = random.randint(1024, 4096)  # 1-4 KB
                data = bytearray(random.getrandbits(8) for _ in range(size))
                arrays.append(data)

            # Modifier aléatoirement le contenu pour éviter l'optimisation par le compilateur
            for arr in arrays:
                if len(arr) > 0:
                    index = random.randint(0, len(arr) - 1)
                    arr[index] = random.getrandbits(8)

            logger.debug(f"Bruit mémoire ajouté: {num_arrays} tableaux")

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de bruit mémoire: {e}")

    def safe_execute_action(self, action_func, max_retries=3):
        """
        Exécute une action en toute sécurité, avec vérification et retries

        :param action_func: Fonction à exécuter
        :param max_retries: Nombre maximal de tentatives
        :return: Résultat de la fonction ou None en cas d'échec
        """
        retries = 0
        while retries < max_retries:
            try:
                # Vérifier si le jeu est actif
                if not self.is_game_window_active():
                    logger.warning("Fenêtre du jeu non active. Attente...")
                    time.sleep(self.randomize_delay(2.0))
                    retries += 1
                    continue

                # Exécuter l'action
                result = action_func()

                # Mettre à jour le temps de dernière action
                self.update_last_action_time()

                # Ajouter du bruit mémoire
                if random.random() < 0.1:  # 10% de chance
                    self.add_memory_noise()

                return result

            except Exception as e:
                logger.error(f"Erreur lors de l'exécution de l'action: {e}")
                retries += 1
                time.sleep(self.randomize_delay(1.0))

        logger.error(f"Action abandonnée après {max_retries} tentatives")
        return None


# Fonction d'aide pour obtenir l'instance globale du gestionnaire
_anti_detection_manager = None

def get_anti_detection_manager():
    """
    Renvoie l'instance globale du gestionnaire anti-détection

    :return: Instance de AntiDetectionManager
    """
    global _anti_detection_manager

    if _anti_detection_manager is None:
        _anti_detection_manager = AntiDetectionManager()

    return _anti_detection_manager
