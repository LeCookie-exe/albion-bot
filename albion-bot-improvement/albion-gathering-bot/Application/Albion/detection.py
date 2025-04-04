import cv2 as cv
import torch
from Application.Capture.Factory import CaptureFactory
from time import time
from math import sqrt
import os
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("albion_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AlbionDetection")

class AlbionDetection:
    MODEL_NAME = "best.pt"
    IMG_SIZE = 640
    CONFIDENCE = 0.5

    def __init__(self,
                 model_name=MODEL_NAME,
                 debug=False,
                 confidence=CONFIDENCE,
                 window_name="Albion Online Client"
                 ):
        """
        Initialize the AlbionDetection object.

        :param model_name: Name of the YOLOv5 model file.
        :param debug: Flag to enable debug mode.
        :param confidence: Confidence threshold for detections.
        :param window_name: Name of the window to capture.
        """
        self.model_name = model_name
        self.debug = debug
        self.confidence = confidence

        try:
            # Tentative de capture de la fenêtre
            self.window_capture = CaptureFactory(window_name).capture
            logger.info(f"Fenêtre '{window_name}' capturée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la capture de la fenêtre: {e}")
            raise

        try:
            # Chargement du modèle
            self.model = self._load_model()
            self.classes = self._load_classes()
            logger.info(f"Modèle '{model_name}' chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            raise

        # Position par défaut du personnage (centre de l'écran)
        self.character_position_X = self.IMG_SIZE / 2
        self.character_position_Y = self.IMG_SIZE / 2 - 60

    def _process_image(self, img):
        """
        Preprocess the image.

        :param img: Input image.
        :return: Processed image.
        """
        if img is None:
            logger.error("Capture d'écran vide")
            return None

        try:
            img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
            return cv.resize(img, (self.IMG_SIZE, self.IMG_SIZE))
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image: {e}")
            return None

    def _load_classes(self):
        """
        Load class information.

        :return: Dictionary containing class information.
        """
        classes = {}
        for k, v in self.model.names.items():
            classes[k] = {
                "label": v,
                "color": (0, 255, k * 10)
            }
        logger.debug(f"Classes chargées: {classes}")
        return classes

    def draw_boxes(self, img, coordinates):
        """
        Draw bounding boxes on the image.

        :param img: Input image.
        :param coordinates: Bounding box coordinates.
        """
        if img is None:
            return

        for coord in coordinates:
            x1, y1, x2, y2 = coord[:4].int()
            confidence, class_id = coord[4], self.classes[int(coord[5])]
            cv.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), class_id["color"], 2)
            label = f"{class_id['label']} {confidence:.2f}"
            cv.putText(img, label, (int(x1), int(y1) - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, class_id["color"], 2)

        self.__cross_line(img)

        cv.drawMarker(img, (int(self.character_position_X), int(self.character_position_Y)), (255, 255, 255),
                      cv.MARKER_DIAMOND, 10, 2)
        self.__marker_closest(img, coordinates)

    def __cross_line(self, img):
        """
        Draw cross lines on the image to indicate character position.

        :param img: Input image.
        """
        if img is None:
            return

        cv.line(img, (0, int(self.character_position_Y)), (self.IMG_SIZE, int(self.character_position_Y)),
                (255, 255, 255), 2)
        cv.line(img, (int(self.character_position_X), 0), (int(self.character_position_X), self.IMG_SIZE),
                (255, 255, 255), 2)

    def __marker_closest(self, img, coordinates):
        """
        Mark the closest resource point on the image.

        :param img: Input image.
        :param coordinates: Bounding box coordinates.
        """
        if img is None:
            return

        closest = self.closest_point(coordinates)

        if closest is not None:
            cv.drawMarker(img, (int(closest[0]), int(closest[1])), (37, 150, 190), cv.MARKER_CROSS, 10, 2)
            cv.putText(img, "Closest", (int(closest[0]), int(closest[1]) + 50), cv.FONT_HERSHEY_SIMPLEX, 0.5,
                       (0, 255, 0), 2)

    def closest_point(self, coordinates):
        """
        Find the closest resource point to the character.

        :param coordinates: Bounding box coordinates.
        :return: Tuple containing (x, y, resource_id) or None if no resources found.
        """
        if not coordinates or len(coordinates) == 0:
            if self.debug:
                logger.debug("Aucune ressource détectée")
            return None

        min_dist = float('inf')
        position = 0
        centers = []

        for index, coord in enumerate(coordinates):
            x1, y1, x2, y2 = coord[:4].int()

            center_x, center_y = ((x2 - x1) / 2) + x1, ((y2 - y1) / 2) + y1

            computed = sqrt(
                abs(self.character_position_X - center_x) ** 2 + abs(self.character_position_Y - center_y) ** 2)

            if computed < min_dist:
                min_dist = computed
                position = index

            centers.append((center_x, center_y, coord[5].int()))

        if not centers:
            return None

        return centers[position]

    def __convert_coordinates_to_screen_position(self, center_x, center_y):
        """
        Convert normalized coordinates to screen position.

        :param center_x: Center X coordinate.
        :param center_y: Center Y coordinate.
        :return: Tuple containing screen position (x, y).
        """
        if not hasattr(self.window_capture, 'window'):
            logger.error("Information de fenêtre manquante")
            return center_x, center_y

        try:
            # Conversion des coordonnées de l'image vers les coordonnées de l'écran
            screen_x = ((center_x * self.window_capture.window.width) / self.IMG_SIZE) + self.window_capture.window.left
            screen_y = ((center_y * self.window_capture.window.height) / self.IMG_SIZE) + self.window_capture.window.top
            return screen_x, center_y
        except Exception as e:
            logger.error(f"Erreur lors de la conversion des coordonnées: {e}")
            return center_x, center_y

    def _load_model(self):
        """
        Load the YOLOv5 model.

        :return: Loaded YOLOv5 model.
        """
        if not os.path.exists(self.model_name):
            logger.error(f"Le fichier modèle '{self.model_name}' n'existe pas")
            raise FileNotFoundError(f"Le fichier modèle '{self.model_name}' n'existe pas")

        try:
            model = torch.hub.load('yolov5', 'custom', path=self.model_name, source="local", force_reload=True,
                               verbose=self.debug)
            # Réduire l'utilisation de la mémoire
            model.conf = self.confidence  # Seuil de confiance
            model.iou = 0.45  # Seuil IoU pour NMS

            # Passer en mode évaluation pour de meilleures performances
            model.eval()

            return model
        except Exception as e:
            logger.error(f"Échec du chargement du modèle: {str(e)}")
            raise

    def predict(self):
        """
        Make predictions using the YOLOv5 model.

        :return: Tuple containing (center_x, center_y, resource_id, img) or (None, None, None, img) if no resources found.
        """
        loop_time = time()

        try:
            # Capture et prétraitement de l'image
            screenshot = self.window_capture.screenshot()
            img = self._process_image(screenshot)

            if img is None:
                logger.error("Échec du traitement de l'image de capture d'écran")
                return None, None, None, None

            # Prédiction avec le modèle
            res = self.model(img)

            # Filtrage des détections par seuil de confiance
            coordinates = [coord for coord in res.xyxy[0] if coord[4].item() > self.confidence]

            # Affichage du debug si activé
            if self.debug:
                self.draw_boxes(img, coordinates)
                fps = 1 / (time() - loop_time)
                cv.putText(img, f'FPS {fps:.1f}', (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv.imshow("Détection Albion", img)

            # Trouver le point le plus proche
            closest = self.closest_point(coordinates)

            if closest is None:
                return None, None, None, img

            center_x, center_y, resource_id = closest

            # Conversion des coordonnées
            screen_x, screen_y = self.__convert_coordinates_to_screen_position(center_x, center_y)

            logger.debug(f"Ressource détectée: {self.classes[resource_id]['label']} à ({screen_x}, {screen_y})")

            return screen_x, screen_y, resource_id, img

        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {str(e)}")
            return None, None, None, None
