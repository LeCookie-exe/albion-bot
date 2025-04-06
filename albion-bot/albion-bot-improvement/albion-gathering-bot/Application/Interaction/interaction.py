from Application.Albion.detection import AlbionDetection
from time import sleep
import cv2 as cv
import pyautogui
import random
import logging
import numpy as np
from Application.AntiDetection import get_anti_detection_manager

# Configuration pour un comportement plus humain
pyautogui.MINIMUM_DURATION = 0.1
pyautogui.MINIMUM_SLEEP = 0.05
pyautogui.PAUSE = 0.1

# Configuration du logging
logger = logging.getLogger("Interaction")

class Gathering:
    def __init__(self, x, y, resource):
        self.x = x
        self.y = y
        self.resource = resource
        self.mining_time = 0
        self.successful = False


class Interaction:
    # Temps approximatifs de récolte pour différentes ressources (en secondes)
    RESOURCE_TIMING = {
        0: 12,  # Pierre
        1: 10,  # Bois
        2: 8,   # Fibre
        3: 15,  # Minerai
        4: 9    # Cuir
    }

    # Temps par défaut si le type de ressource est inconnu
    DEFAULT_MINING_TIME = 12

    # Nombre maximal de tentatives de récolte avant de chercher une nouvelle ressource
    MAX_MINING_ATTEMPTS = 3

    # Limite approximative d'inventaire - à ajuster selon le jeu
    INVENTORY_LIMIT = 15

    def __init__(self, model):
        self.model: AlbionDetection = model
        self.current_gathering: Gathering | None = None
        self.debug = self.model.debug

        # Initialiser le gestionnaire anti-détection
        self.anti_detection = get_anti_detection_manager()

        # Démarrer le monitoring anti-détection en arrière-plan
        self.anti_detection.start_monitoring()

        try:
            self.img_border_resource = cv.imread("images/cropped_bar_resource.png", cv.IMREAD_UNCHANGED)
            if self.img_border_resource is None:
                logger.warning("Image de barre de ressource non trouvée. Certaines fonctionnalités seront limitées.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'image de référence: {e}")
            self.img_border_resource = None

        # État du bot
        self.resources_gathered = 0
        self.last_move_time = 0
        self.mining_attempts = 0

        logger.info("Interaction initialisée avec protection anti-détection")

    def __del__(self):
        """Destructeur pour s'assurer que le monitoring est arrêté"""
        try:
            if self.anti_detection:
                self.anti_detection.stop_monitoring()
        except:
            pass

    def toggle_ath(self):
        """Toggle l'ATH du jeu pour masquer les actions du bot"""
        def _toggle():
            # Ajout d'un délai aléatoire pour simuler un comportement humain
            sleep(self.anti_detection.randomize_delay(0.2))
            pyautogui.hotkey('alt', 'h')
            logger.debug("ATH basculé")

        # Utiliser l'exécution sécurisée
        self.anti_detection.safe_execute_action(_toggle)

    def go_on_mount(self):
        """Monte sur la monture"""
        def _mount():
            # Simulation d'un comportement humain avec un délai aléatoire
            sleep(self.anti_detection.randomize_delay(0.3))
            pyautogui.press('a')
            logger.debug("Montée sur la monture")

        # Utiliser l'exécution sécurisée
        self.anti_detection.safe_execute_action(_mount)

    def __crop_image_resource(self):
        """Extraire la zone de l'image contenant la barre de progression de récolte"""
        try:
            # Coordonnées de la barre de progression (peut nécessiter un ajustement)
            top_x, top_y = 265, 365
            bottom_x, bottom_y = 293, 410

            img = self.model._process_image(self.model.window_capture.screenshot())
            if img is None:
                return None

            return cv.cvtColor(img, cv.COLOR_BGR2GRAY)[top_y:bottom_y, top_x:bottom_x]
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de la zone d'image: {e}")
            return None

    def __is_mining(self):
        """Vérifier si la récolte est en cours en utilisant la correspondance de modèle"""
        if self.img_border_resource is None:
            # Si l'image de référence est manquante, utiliser un délai fixe
            return True

        try:
            img = self.__crop_image_resource()
            if img is None:
                return False

            result = cv.matchTemplate(img, self.img_border_resource, cv.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv.minMaxLoc(result)

            if self.debug:
                logger.debug(f"Confiance de correspondance de la barre de récolte: {max_val:.3f}")

            return max_val >= 0.8
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'état de récolte: {e}")
            return False

    def __is_inventory_full(self):
        """
        Vérifier si l'inventaire est plein
        Cette méthode est une approximation simple basée sur le nombre de ressources récoltées
        Une implémentation plus avancée pourrait analyser l'interface utilisateur
        """
        return self.resources_gathered >= self.INVENTORY_LIMIT

    def __mining(self):
        """Gérer le processus de récolte"""
        if self.debug:
            logger.info("Début de la récolte...")

        start_time = 0
        mining_time = 0
        success = False

        # Déterminer le temps approximatif de récolte
        if self.current_gathering and self.current_gathering.resource in self.RESOURCE_TIMING:
            # Ajouter une variation de temps pour simuler un comportement humain
            base_time = self.RESOURCE_TIMING[self.current_gathering.resource]
            mining_time = base_time + random.uniform(-1, 1)
        else:
            mining_time = self.DEFAULT_MINING_TIME + random.uniform(-1, 1)

        if self.debug:
            logger.debug(f"Temps estimé de récolte: {mining_time:.1f} secondes")

        # Attendre que la récolte soit terminée
        max_wait_time = mining_time * 1.5  # 50% de temps supplémentaire au cas où
        elapsed_time = 0
        check_interval = 0.5

        while elapsed_time < max_wait_time:
            # Mettre à jour le temps de dernière action pour le système anti-détection
            self.anti_detection.update_last_action_time()

            if not self.__is_mining():
                # Si la récolte est terminée
                success = True
                self.resources_gathered += 1
                logger.debug(f"Récolte réussie! Ressources récoltées: {self.resources_gathered}")
                break

            # Attendre un court intervalle avant de vérifier à nouveau
            sleep(self.anti_detection.randomize_delay(check_interval))
            elapsed_time += check_interval

        if not success:
            logger.warning("La récolte a échoué ou a pris trop de temps")
            self.mining_attempts += 1
        else:
            self.mining_attempts = 0

        if self.debug:
            logger.info("Récolte terminée")

        # Ajout d'un petit délai après la récolte pour un comportement plus naturel
        sleep(self.anti_detection.randomize_delay(0.7))

    def __moving(self):
        """Gérer le processus de déplacement vers une ressource"""
        if self.debug:
            logger.info("Déplacement vers la ressource...")

        # Temps maximal d'attente pour arriver à la ressource
        max_wait_time = 15
        elapsed_time = 0
        check_interval = 0.5

        while elapsed_time < max_wait_time:
            # Mettre à jour le temps de dernière action pour le système anti-détection
            self.anti_detection.update_last_action_time()

            if self.__is_mining():
                logger.debug("Arrivé à la ressource, début de la récolte")
                return True

            # Vérifier si nous sommes bloqués
            if elapsed_time > 5 and not self.__is_mining():
                # Essayer de relancer le mouvement
                if self.current_gathering:
                    logger.debug("Potentiellement bloqué, tentative de relance du mouvement")
                    self.anti_detection.human_like_click(
                        self.current_gathering.x,
                        self.current_gathering.y
                    )

            # Attendre un court intervalle avant de vérifier à nouveau
            sleep(self.anti_detection.randomize_delay(check_interval))
            elapsed_time += check_interval

        logger.warning("N'a pas pu atteindre la ressource dans le temps imparti")
        return False

    def find_and_gather_nearest_resource(self):
        """
        Trouve la ressource la plus proche et la récolte
        """
        # Prédire la position de la ressource la plus proche
        x, y, resource, _ = self.model.predict()

        if x is None or y is None or resource is None:
            logger.info("Aucune ressource détectée, recherche en cours...")
            # Faire pivoter légèrement la caméra pour chercher des ressources
            self.__rotate_camera()
            return False

        # Commencer le processus de récolte
        return self.gathering(x, y, resource)

    def __rotate_camera(self):
        """
        Fait pivoter légèrement la caméra pour rechercher des ressources
        """
        def _rotate():
            # Simuler un mouvement de caméra aléatoire
            angle = random.uniform(-20, 20)
            duration = self.anti_detection.get_human_mouse_duration()

            # Maintenir le bouton droit de la souris enfoncé et déplacer
            pyautogui.mouseDown(button='right')
            pyautogui.moveRel(angle, 0, duration=duration)
            pyautogui.mouseUp(button='right')

            logger.debug(f"Rotation de caméra de {angle:.1f} degrés")

            # Petit délai après la rotation
            sleep(self.anti_detection.randomize_delay(0.3))

        # Utiliser l'exécution sécurisée
        self.anti_detection.safe_execute_action(_rotate)

    def gathering(self, x, y, resource):
        """
        Processus principal de récolte
        """
        try:
            # Vérifier si l'inventaire est plein
            if self.__is_inventory_full():
                logger.info("Inventaire plein! Retour au menu principal...")
                # Ici, vous pourriez implémenter une logique pour retourner à la ville
                return False

            # Vérifier si le nombre de tentatives de récolte est trop élevé
            if self.mining_attempts >= self.MAX_MINING_ATTEMPTS:
                logger.warning("Trop de tentatives de récolte ont échoué. Recherche d'une nouvelle ressource...")
                self.mining_attempts = 0
                return False

            # Basculer l'ATH pour minimiser les éléments visuels
            self.toggle_ath()

            # Stocker les informations sur la ressource en cours de récolte
            self.current_gathering = Gathering(x, y, resource)

            # Clic sur la ressource avec comportement humain
            self.anti_detection.human_like_click(
                self.current_gathering.x,
                self.current_gathering.y
            )

            # Déplacer la souris ailleurs pour éviter de bloquer la vue
            safe_x, safe_y = self.anti_detection.get_safe_coordinates(
                random.randint(5, 20),
                random.randint(5, 20)
            )

            pyautogui.moveTo(safe_x, safe_y,
                             duration=self.anti_detection.get_human_mouse_duration())

            # Attendre d'arriver à la ressource
            if self.__moving():
                # Commencer la récolte
                self.__mining()

            # Basculer l'ATH pour revenir à l'état normal
            self.toggle_ath()

            return True

        except Exception as e:
            logger.error(f"Erreur lors du processus de récolte: {e}")
            # En cas d'erreur, essayer de rétablir l'ATH
            try:
                self.toggle_ath()
            except:
                pass
            return False

    def run_gathering_loop(self, max_resources=100, max_time_minutes=60):
        """
        Exécute une boucle de récolte continue avec des limites de sécurité

        :param max_resources: Nombre maximal de ressources à récolter
        :param max_time_minutes: Durée maximale en minutes
        """
        import time

        start_time = time.time()
        max_time_seconds = max_time_minutes * 60

        logger.info(f"Démarrage de la boucle de récolte (limite: {max_resources} ressources ou {max_time_minutes} minutes)")

        try:
            while (self.resources_gathered < max_resources and
                   time.time() - start_time < max_time_seconds):

                # Vérifier si la fenêtre du jeu est active
                if not self.anti_detection.is_game_window_active():
                    logger.warning("Fenêtre du jeu non active. Pause...")
                    sleep(2.0)
                    continue

                # Vérifier si l'inventaire est plein
                if self.__is_inventory_full():
                    logger.info("Inventaire plein! Fin de la session de récolte.")
                    break

                # Trouver et récolter la ressource la plus proche
                self.find_and_gather_nearest_resource()

                # Ajouter un délai variable entre les actions pour simuler un comportement humain
                sleep_time = self.anti_detection.randomize_delay(1.0)
                sleep(sleep_time)

                # Ajouter du "bruit" à la mémoire pour compliquer les scans
                if random.random() < 0.1:  # 10% de chance
                    self.anti_detection.add_memory_noise()

                # Afficher l'état actuel
                elapsed_minutes = (time.time() - start_time) / 60
                logger.info(f"Progression: {self.resources_gathered}/{max_resources} ressources, "
                           f"{elapsed_minutes:.1f}/{max_time_minutes} minutes")

                # Petite pause aléatoire occasionnelle pour simuler un comportement humain
                if random.random() < 0.05:  # 5% de chance
                    pause_time = self.anti_detection.randomize_delay(5.0)
                    logger.debug(f"Pause aléatoire de {pause_time:.1f} secondes")
                    sleep(pause_time)

            logger.info(f"Session de récolte terminée! {self.resources_gathered} ressources récoltées en "
                       f"{(time.time() - start_time)/60:.1f} minutes")

        except KeyboardInterrupt:
            logger.info("Arrêt manuel de la boucle de récolte")
        except Exception as e:
            logger.error(f"Erreur dans la boucle de récolte: {e}")
        finally:
            # Arrêter le monitoring anti-détection
            self.anti_detection.stop_monitoring()

            # S'assurer que l'ATH est remis à l'état normal
            try:
                if random.random() < 0.5:  # Ne pas toujours faire la même chose
                    self.toggle_ath()
            except:
                pass
