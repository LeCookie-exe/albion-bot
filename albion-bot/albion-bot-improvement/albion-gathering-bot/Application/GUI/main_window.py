"""
Interface graphique principale pour le bot de récolte Albion.
"""

import sys
import os
import logging
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTabWidget, QTextEdit, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox, QSlider, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont, QTextCursor

from Application.Albion.detection import AlbionDetection
from Application.Interaction.interaction import Interaction
from Application.AntiDetection import get_anti_detection_manager

# Configuration du logging pour l'interface graphique
logger = logging.getLogger("GUI")


class LogHandler(logging.Handler):
    """Handler personnalisé pour rediriger les logs vers un QTextEdit"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        log_message = self.format(record)
        self.text_widget.append(log_message)
        # Faire défiler automatiquement vers le bas
        self.text_widget.moveCursor(QTextCursor.End)


class GatheringThread(QThread):
    """Thread séparé pour exécuter le processus de récolte"""

    # Signaux
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        self.resources_gathered = 0
        self.anti_detection = None
        self.model = None
        self.interaction = None

    def run(self):
        """Méthode principale du thread de récolte"""
        try:
            # Initialiser le système anti-détection
            self.anti_detection = get_anti_detection_manager()
            self.configure_anti_detection()

            # Initialiser le modèle et l'interaction
            self.update_signal.emit("Chargement du modèle de détection...")
            self.model = AlbionDetection(
                model_name=self.config.get("model_path", "best.pt"),
                debug=self.config.get("debug_mode", False),
                confidence=self.config.get("confidence", 0.7),
                window_name=self.config.get("window_name", "Albion Online Client")
            )

            self.update_signal.emit("Initialisation du système d'interaction...")
            self.interaction = Interaction(self.model)

            self.update_signal.emit("Démarrage de la récolte...")

            max_resources = self.config.get("max_resources", 100)
            max_time_minutes = self.config.get("max_time", 60)
            start_time = time.time()
            max_time_seconds = max_time_minutes * 60

            # Petite pause avant de commencer
            time.sleep(3)

            # Boucle principale de récolte
            while (self.running and
                   self.resources_gathered < max_resources and
                   time.time() - start_time < max_time_seconds):

                # Vérifier si la fenêtre du jeu est active
                if not self.anti_detection.is_game_window_active():
                    self.update_signal.emit("Fenêtre du jeu non active. Pause...")
                    time.sleep(2.0)
                    continue

                # Rechercher et récolter une ressource
                result = self.interaction.find_and_gather_nearest_resource()

                if result:
                    self.resources_gathered = self.interaction.resources_gathered
                    progress = int((self.resources_gathered / max_resources) * 100)
                    self.progress_signal.emit(progress)

                    elapsed_minutes = (time.time() - start_time) / 60
                    self.update_signal.emit(
                        f"Ressources récoltées: {self.resources_gathered}/{max_resources} "
                        f"({elapsed_minutes:.1f}/{max_time_minutes} minutes)"
                    )

                # Pause entre les actions
                time.sleep(self.anti_detection.randomize_delay(1.0))

            # Fin de la boucle
            elapsed_minutes = (time.time() - start_time) / 60
            self.update_signal.emit(
                f"Session terminée! {self.resources_gathered} ressources récoltées "
                f"en {elapsed_minutes:.1f} minutes"
            )
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"Erreur: {str(e)}")
            logger.error(f"Erreur dans le thread de récolte: {e}", exc_info=True)
        finally:
            # Nettoyer les ressources
            if self.anti_detection:
                self.anti_detection.stop_monitoring()

    def configure_anti_detection(self):
        """Configure le système anti-détection selon les paramètres"""
        if self.config.get("disable_anti_detection", False):
            self.update_signal.emit("⚠️ Fonctionnalités anti-détection désactivées!")
            self.anti_detection.RANDOMIZE_DELAYS = False
            self.anti_detection.AVOID_PATTERNS = False
            self.anti_detection.HUMAN_LIKE_MOUSE = False
            return

        if self.config.get("safe_mode", False):
            self.update_signal.emit("Mode sécurisé activé avec comportements plus humains")
            self.anti_detection.mouse_speed_variance = 0.7

        self.anti_detection.start_monitoring()
        self.update_signal.emit("Système anti-détection configuré et actif")

    def stop(self):
        """Arrête le thread proprement"""
        self.running = False
        self.update_signal.emit("Arrêt en cours... Veuillez patienter.")

        # Attendre que le thread se termine correctement
        self.wait(5000)  # Attendre max 5 secondes


class AlbionBotGUI(QMainWindow):
    """Interface graphique principale du bot de récolte Albion"""

    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre
        self.setWindowTitle("Albion Gathering Bot")
        self.setMinimumSize(800, 600)

        # État du bot
        self.gathering_thread = None
        self.is_running = False

        # Configuration par défaut
        self.config = {
            "mode": "gather",
            "confidence": 0.7,
            "max_resources": 100,
            "max_time": 60,
            "window_name": "Albion Online Client",
            "model_path": "best.pt",
            "safe_mode": True,
            "disable_anti_detection": False,
            "debug_mode": False
        }

        # Configurer l'interface utilisateur
        self.setup_ui()

        # Minuteur pour mettre à jour l'état
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Mise à jour toutes les secondes

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)

        # En-tête avec logo et titre
        self.setup_header(main_layout)

        # Onglets
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Onglet principal
        main_tab = QWidget()
        tabs.addTab(main_tab, "Récolte")

        # Onglet de configuration
        config_tab = QWidget()
        tabs.addTab(config_tab, "Configuration")

        # Onglet des logs
        logs_tab = QWidget()
        tabs.addTab(logs_tab, "Logs")

        # Onglet À propos
        about_tab = QWidget()
        tabs.addTab(about_tab, "À propos")

        # Configurer chaque onglet
        self.setup_main_tab(main_tab)
        self.setup_config_tab(config_tab)
        self.setup_logs_tab(logs_tab)
        self.setup_about_tab(about_tab)

        # Barre d'état
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Prêt")

    def setup_header(self, layout):
        """Configure l'en-tête avec logo et titre"""
        header_layout = QHBoxLayout()

        # Logo (à remplacer par le chemin vers votre logo)
        logo_path = os.path.join("ressources", "logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            header_layout.addWidget(logo_label)

        # Titre
        title_label = QLabel("Albion Gathering Bot")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        # Étirer l'espace
        header_layout.addStretch()

        # Ajouter l'en-tête au layout principal
        layout.addLayout(header_layout)

    def setup_main_tab(self, tab):
        """Configure l'onglet principal de récolte"""
        layout = QVBoxLayout(tab)

        # Groupe d'informations sur l'état
        status_group = QGroupBox("État")
        status_layout = QFormLayout(status_group)

        self.status_label = QLabel("Prêt")
        status_layout.addRow("État:", self.status_label)

        self.resource_count_label = QLabel("0")
        status_layout.addRow("Ressources récoltées:", self.resource_count_label)

        self.time_elapsed_label = QLabel("0:00")
        status_layout.addRow("Temps écoulé:", self.time_elapsed_label)

        layout.addWidget(status_group)

        # Barre de progression
        progress_group = QGroupBox("Progression")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(progress_group)

        # Zone de journal d'activité
        activity_group = QGroupBox("Activité")
        activity_layout = QVBoxLayout(activity_group)

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        activity_layout.addWidget(self.activity_log)

        layout.addWidget(activity_group)

        # Boutons de contrôle
        control_layout = QHBoxLayout()

        self.start_button = QPushButton("Démarrer")
        self.start_button.clicked.connect(self.start_gathering)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Arrêter")
        self.stop_button.clicked.connect(self.stop_gathering)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.run_test)
        control_layout.addWidget(self.test_button)

        layout.addLayout(control_layout)

    def setup_config_tab(self, tab):
        """Configure l'onglet de configuration"""
        layout = QVBoxLayout(tab)

        # Groupe des paramètres de détection
        detection_group = QGroupBox("Paramètres de détection")
        detection_layout = QFormLayout(detection_group)

        self.confidence_spinbox = QDoubleSpinBox()
        self.confidence_spinbox.setRange(0.1, 1.0)
        self.confidence_spinbox.setSingleStep(0.05)
        self.confidence_spinbox.setValue(self.config["confidence"])
        detection_layout.addRow("Seuil de confiance:", self.confidence_spinbox)

        self.model_path_edit = QTextEdit()
        self.model_path_edit.setFixedHeight(30)
        self.model_path_edit.setText(self.config["model_path"])
        self.model_path_edit.setReadOnly(True)

        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_path_edit)

        browse_button = QPushButton("Parcourir")
        browse_button.clicked.connect(self.browse_model)
        model_layout.addWidget(browse_button)

        detection_layout.addRow("Modèle:", model_layout)

        self.window_name_edit = QTextEdit()
        self.window_name_edit.setFixedHeight(30)
        self.window_name_edit.setText(self.config["window_name"])
        detection_layout.addRow("Nom de la fenêtre:", self.window_name_edit)

        layout.addWidget(detection_group)

        # Groupe des paramètres de récolte
        gathering_group = QGroupBox("Paramètres de récolte")
        gathering_layout = QFormLayout(gathering_group)

        self.max_resources_spinbox = QSpinBox()
        self.max_resources_spinbox.setRange(1, 1000)
        self.max_resources_spinbox.setValue(self.config["max_resources"])
        gathering_layout.addRow("Max. ressources:", self.max_resources_spinbox)

        self.max_time_spinbox = QSpinBox()
        self.max_time_spinbox.setRange(1, 720)  # max 12 heures
        self.max_time_spinbox.setValue(self.config["max_time"])
        gathering_layout.addRow("Temps max. (minutes):", self.max_time_spinbox)

        layout.addWidget(gathering_group)

        # Groupe des paramètres anti-détection
        anti_detection_group = QGroupBox("Paramètres anti-détection")
        anti_detection_layout = QFormLayout(anti_detection_group)

        self.safe_mode_checkbox = QCheckBox()
        self.safe_mode_checkbox.setChecked(self.config["safe_mode"])
        anti_detection_layout.addRow("Mode sécurisé:", self.safe_mode_checkbox)

        self.disable_anti_detection_checkbox = QCheckBox()
        self.disable_anti_detection_checkbox.setChecked(self.config["disable_anti_detection"])
        anti_detection_layout.addRow("Désactiver anti-détection:", self.disable_anti_detection_checkbox)

        self.debug_mode_checkbox = QCheckBox()
        self.debug_mode_checkbox.setChecked(self.config["debug_mode"])
        anti_detection_layout.addRow("Mode débogage:", self.debug_mode_checkbox)

        layout.addWidget(anti_detection_group)

        # Bouton pour sauvegarder les paramètres
        save_button = QPushButton("Sauvegarder la configuration")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

    def setup_logs_tab(self, tab):
        """Configure l'onglet des logs"""
        layout = QVBoxLayout(tab)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Configurer le gestionnaire de logs pour rediriger vers le widget
        log_handler = LogHandler(self.log_text)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        # Ajouter le gestionnaire aux loggers
        root_logger = logging.getLogger()
        root_logger.addHandler(log_handler)

        # Boutons pour les logs
        button_layout = QHBoxLayout()

        clear_logs_button = QPushButton("Effacer les logs")
        clear_logs_button.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_logs_button)

        layout.addLayout(button_layout)

    def setup_about_tab(self, tab):
        """Configure l'onglet À propos"""
        layout = QVBoxLayout(tab)

        # Logo plus grand
        logo_path = os.path.join("ressources", "logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)

        # Informations sur l'application
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
        <h2 align='center'>Albion Gathering Bot</h2>
        <p align='center'>Version 2.0</p>
        <p align='center'>Bot de récolte amélioré pour Albion Online.</p>
        <p align='center'>Utilise la détection d'objets YOLOv5 pour repérer et récolter automatiquement les ressources.</p>
        <hr>
        <p><b>Avertissement</b>: Ce bot a été créé à des fins éducatives et expérimentales uniquement.
        L'utilisation de bots dans Albion Online va à l'encontre des conditions d'utilisation du jeu
        et peut entraîner la suspension ou le bannissement de votre compte.</p>
        <hr>
        <p align='center'>Créé par <a href='https://github.com/Michelprogram'>Michelprogram</a></p>
        <p align='center'>Amélioré par la communauté</p>
        """)
        layout.addWidget(info_text)

    def browse_model(self):
        """Ouvre une boîte de dialogue pour sélectionner le fichier modèle"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le modèle",
            "",
            "PyTorch Models (*.pt);;All Files (*)"
        )

        if file_path:
            self.model_path_edit.setText(file_path)

    def save_config(self):
        """Sauvegarde les paramètres configurés"""
        try:
            self.config["confidence"] = self.confidence_spinbox.value()
            self.config["max_resources"] = self.max_resources_spinbox.value()
            self.config["max_time"] = self.max_time_spinbox.value()
            self.config["window_name"] = self.window_name_edit.toPlainText()
            self.config["model_path"] = self.model_path_edit.toPlainText()
            self.config["safe_mode"] = self.safe_mode_checkbox.isChecked()
            self.config["disable_anti_detection"] = self.disable_anti_detection_checkbox.isChecked()
            self.config["debug_mode"] = self.debug_mode_checkbox.isChecked()

            QMessageBox.information(self, "Succès", "Configuration sauvegardée avec succès!")
            logger.info("Configuration sauvegardée: %s", str(self.config))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}", exc_info=True)

    def start_gathering(self):
        """Démarre le processus de récolte"""
        if self.is_running:
            return

        # Vérifier si le jeu est ouvert
        anti_detection = get_anti_detection_manager()
        if not anti_detection.is_game_window_active():
            QMessageBox.warning(
                self,
                "Attention",
                "La fenêtre du jeu n'est pas active. Veuillez ouvrir Albion Online avant de démarrer."
            )
            return

        # Confirmation avant de commencer
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Vous êtes sur le point de démarrer la récolte automatique. "
            "Assurez-vous que votre personnage est positionné dans une zone de récolte. "
            "\n\nVoulez-vous continuer?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            # Mettre à jour les paramètres
            self.save_config()

            # Réinitialiser les indicateurs
            self.progress_bar.setValue(0)
            self.activity_log.clear()

            # Créer et démarrer le thread de récolte
            self.gathering_thread = GatheringThread(self.config)

            # Connecter les signaux
            self.gathering_thread.update_signal.connect(self.update_activity_log)
            self.gathering_thread.progress_signal.connect(self.progress_bar.setValue)
            self.gathering_thread.finished_signal.connect(self.gathering_finished)
            self.gathering_thread.error_signal.connect(self.handle_error)

            # Démarrer le thread
            self.gathering_thread.start()

            # Mettre à jour l'interface
            self.is_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.test_button.setEnabled(False)

            # Démarrer le minuteur de temps écoulé
            self.start_time = time.time()

            self.status_label.setText("En cours de récolte")
            self.status_bar.showMessage("Récolte en cours...")

            logger.info("Démarrage du processus de récolte")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du démarrage: {str(e)}")
            logger.error(f"Erreur lors du démarrage du processus: {e}", exc_info=True)

    def stop_gathering(self):
        """Arrête le processus de récolte"""
        if not self.is_running or not self.gathering_thread:
            return

        try:
            # Arrêter le thread
            self.gathering_thread.stop()

            # Mettre à jour l'interface
            self.is_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.test_button.setEnabled(True)

            self.status_label.setText("Arrêté")
            self.status_bar.showMessage("Récolte arrêtée")

            logger.info("Processus de récolte arrêté")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'arrêt: {str(e)}")
            logger.error(f"Erreur lors de l'arrêt du processus: {e}", exc_info=True)

    def run_test(self):
        """Exécute un test rapide"""
        try:
            # Sauvegarder la configuration
            self.save_config()

            # Vérifier si le jeu est ouvert
            anti_detection = get_anti_detection_manager()
            if not anti_detection.is_game_window_active():
                QMessageBox.warning(
                    self,
                    "Test",
                    "❌ La fenêtre du jeu n'est pas active. Veuillez ouvrir Albion Online."
                )
                return

            # Test de détection
            self.update_activity_log("Test de détection en cours...")

            model = AlbionDetection(
                model_name=self.config["model_path"],
                debug=True,
                confidence=self.config["confidence"],
                window_name=self.config["window_name"]
            )

            x, y, resource, _ = model.predict()

            results = ["✅ Modèle chargé avec succès"]

            if resource is not None:
                resource_name = model.classes[resource]["label"]
                results.append(f"✅ Ressource détectée: {resource_name} à ({x}, {y})")
            else:
                results.append("❌ Aucune ressource détectée. Essayez d'ajuster le seuil de confiance.")

            # Afficher les résultats
            QMessageBox.information(
                self,
                "Résultats du test",
                "\n".join(results)
            )

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du test: {str(e)}")
            logger.error(f"Erreur lors du test: {e}", exc_info=True)

    def update_activity_log(self, message):
        """Met à jour le journal d'activité"""
        self.activity_log.append(message)
        # Faire défiler vers le bas
        self.activity_log.moveCursor(QTextCursor.End)

    def gathering_finished(self):
        """Appelé lorsque le processus de récolte est terminé"""
        self.is_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.test_button.setEnabled(True)

        self.status_label.setText("Terminé")
        self.status_bar.showMessage("Récolte terminée")

        QMessageBox.information(
            self,
            "Terminé",
            f"Session de récolte terminée!\n"
            f"Ressources récoltées: {self.gathering_thread.resources_gathered}"
        )

        logger.info("Processus de récolte terminé")

    def handle_error(self, error_message):
        """Gère les erreurs du thread de récolte"""
        self.is_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.test_button.setEnabled(True)

        self.status_label.setText("Erreur")
        self.status_bar.showMessage("Erreur lors de la récolte")

        self.update_activity_log(f"ERREUR: {error_message}")

        QMessageBox.critical(
            self,
            "Erreur",
            f"Une erreur est survenue pendant la récolte:\n{error_message}"
        )

    def update_status(self):
        """Met à jour les informations d'état régulièrement"""
        if self.is_running:
            # Mettre à jour le temps écoulé
            elapsed_seconds = int(time.time() - self.start_time)
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            self.time_elapsed_label.setText(f"{minutes}:{seconds:02d}")

            # Mettre à jour le nombre de ressources
            if self.gathering_thread:
                self.resource_count_label.setText(str(self.gathering_thread.resources_gathered))

    def clear_logs(self):
        """Efface le contenu de la zone de logs"""
        self.log_text.clear()

    def closeEvent(self, event):
        """Gère l'événement de fermeture de la fenêtre"""
        if self.is_running:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "La récolte est en cours. Voulez-vous vraiment quitter?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Arrêter le thread de récolte
                if self.gathering_thread:
                    self.gathering_thread.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def run_gui():
    """Démarre l'interface graphique"""
    app = QApplication(sys.argv)
    window = AlbionBotGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("albion_bot_gui.log"),
            logging.StreamHandler()
        ]
    )

    run_gui()
