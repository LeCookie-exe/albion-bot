import os
import sys
import logging
import argparse
import cv2 as cv
import time
import random
from time import sleep

from Albion.detection import AlbionDetection
from Application.Interaction.interaction import Interaction
from Application.AntiDetection import get_anti_detection_manager

# Vérifier si PyQt5 est disponible pour l'interface graphique
try:
    from Application.GUI.main_window import run_gui
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("albion_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AlbionMain")

def parse_arguments():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(description='Albion Online Gathering Bot')

    parser.add_argument('--mode', type=str, choices=['gather', 'debug', 'test', 'gui'], default='gather',
                        help='Mode de fonctionnement (gather: récolte automatique, debug: affichage visuel, test: test de détection, gui: interface graphique)')

    parser.add_argument('--debug', action='store_true',
                        help='Active le mode de débogage avec visualisation')

    parser.add_argument('--confidence', type=float, default=0.7,
                        help='Seuil de confiance pour la détection (0.0-1.0)')

    parser.add_argument('--max-resources', type=int, default=100,
                        help='Nombre maximal de ressources à récolter avant de s\'arrêter')

    parser.add_argument('--max-time', type=int, default=60,
                        help='Durée maximale en minutes avant de s\'arrêter')

    parser.add_argument('--window-name', type=str, default="Albion Online Client",
                        help='Nom de la fenêtre du jeu')

    parser.add_argument('--model', type=str, default="best.pt",
                        help='Chemin vers le fichier modèle YOLOv5')

    # Options anti-détection
    parser.add_argument('--safe-mode', action='store_true',
                        help='Active un mode encore plus sécurisé pour éviter la détection (mouvements plus lents, plus humains)')

    parser.add_argument('--disable-anti-detection', action='store_true',
                        help='Désactive les fonctionnalités anti-détection (non recommandé)')

    parser.add_argument('--memory-protection', action='store_true',
                        help='Active la protection de la mémoire contre les scans (expérimental)')

    return parser.parse_args()

def setup_anti_detection(args):
    """Configure des mesures anti-détection pour l'anti-cheat"""
    # Obtenir l'instance du gestionnaire anti-détection
    anti_detection = get_anti_detection_manager()

    # Configurer les options en fonction des arguments
    if args.disable_anti_detection:
        logger.warning("Fonctionnalités anti-détection désactivées! Risque accru de détection.")
        anti_detection.RANDOMIZE_DELAYS = False
        anti_detection.AVOID_PATTERNS = False
        anti_detection.HUMAN_LIKE_MOUSE = False
        return anti_detection

    # Configurez les options anti-détection en fonction des arguments
    if args.safe_mode:
        logger.info("Mode sécurisé activé avec comportements plus humains")
        # Augmenter les délais pour des mouvements plus naturels
        anti_detection.mouse_speed_variance = random.uniform(0.5, 0.8)

    # Randomiser les seed pour les comportements aléatoires
    random.seed(time.time())

    # Simuler des délais variables comme un humain
    time.sleep(random.uniform(1.5, 3.0))

    # Démarrer le monitoring en arrière-plan
    anti_detection.start_monitoring()

    logger.info("Mesures anti-détection configurées")
    return anti_detection

def shutdown_anti_detection(anti_detection):
    """Arrête proprement les mesures anti-détection"""
    if anti_detection:
        try:
            anti_detection.stop_monitoring()
            logger.info("Système anti-détection arrêté")
        except:
            pass

def run_debug_mode(args):
    """Exécuter le mode de débogage pour visualiser la détection"""
    logger.info("Démarrage du mode débogage")

    # Configurer le système anti-détection
    anti_detection = setup_anti_detection(args)

    # Attendre que le joueur se positionne
    print("Positionnez-vous dans le jeu et appuyez sur Entrée pour commencer...")
    input()

    # Démarrer avec un délai pour laisser le temps de revenir au jeu
    sleep(2)

    # Initialiser le modèle avec un seuil de confiance élevé pour la visualisation
    model = AlbionDetection(
        model_name=args.model,
        debug=True,
        confidence=args.confidence,
        window_name=args.window_name
    )

    logger.info(f"Modèle chargé avec un seuil de confiance de {args.confidence}")
    print("Appuyez sur 'q' pour quitter le mode débogage")

    try:
        while True:
            # Vérifier si la fenêtre du jeu est active
            if not anti_detection.is_game_window_active():
                logger.debug("Fenêtre de jeu inactive, attente...")
                time.sleep(1)
                continue

            # Effectuer la prédiction et afficher les résultats
            x, y, resource, _ = model.predict()

            # Si une ressource est détectée, afficher ses informations
            if resource is not None:
                resource_name = model.classes[resource]["label"]
                logger.info(f"Ressource détectée: {resource_name} à la position ({x}, {y})")

            # Quitter si 'q' est pressé
            if cv.waitKey(1) == ord('q'):
                cv.destroyAllWindows()
                break

            # Petit délai pour ne pas surcharger le CPU
            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Mode débogage arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur en mode débogage: {e}")
    finally:
        cv.destroyAllWindows()
        shutdown_anti_detection(anti_detection)

def run_gathering_mode(args):
    """Exécuter le mode de récolte automatique"""
    logger.info("Démarrage du mode récolte")

    # Configurer le système anti-détection
    anti_detection = setup_anti_detection(args)

    # Attendre que le joueur se positionne
    print("Positionnez-vous dans le jeu et appuyez sur Entrée pour commencer la récolte...")
    input()

    # Démarrer avec un délai pour laisser le temps de revenir au jeu
    sleep(2)

    try:
        # Initialiser le modèle et l'interaction
        model = AlbionDetection(
            model_name=args.model,
            debug=args.debug,
            confidence=args.confidence,
            window_name=args.window_name
        )

        interaction = Interaction(model)

        # Exécuter la boucle de récolte
        logger.info(f"Début de la récolte (max: {args.max_resources} ressources, {args.max_time} minutes)")
        interaction.run_gathering_loop(
            max_resources=args.max_resources,
            max_time_minutes=args.max_time
        )

    except KeyboardInterrupt:
        logger.info("Récolte arrêtée par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur pendant la récolte: {e}")
    finally:
        # Nettoyer les fenêtres OpenCV si elles sont ouvertes
        cv.destroyAllWindows()

        # Arrêter le système anti-détection
        shutdown_anti_detection(anti_detection)

        logger.info("Session de récolte terminée")

def run_test_mode(args):
    """Mode de test pour vérifier la configuration et les fonctionnalités de base"""
    logger.info("Démarrage du mode test")

    # Configurer le système anti-détection
    anti_detection = setup_anti_detection(args)

    try:
        # Vérifier si le modèle existe
        if not os.path.exists(args.model):
            logger.error(f"Le fichier modèle '{args.model}' n'existe pas")
            return

        # Tester le chargement du modèle
        print(f"Test de chargement du modèle {args.model}...")
        model = AlbionDetection(
            model_name=args.model,
            debug=True,
            confidence=args.confidence,
            window_name=args.window_name
        )

        print("Test du système anti-détection...")
        if anti_detection.is_game_window_active():
            print("✓ Fenêtre du jeu détectée et active")
        else:
            print("❌ Fenêtre du jeu non détectée. Assurez-vous que le jeu est ouvert.")
            return

        print("Test de détection de l'anti-cheat...")
        if anti_detection._is_eac_present():
            print("✓ Anti-cheat EAC détecté, mesures de protection actives")
        else:
            print("ℹ️ Anti-cheat EAC non détecté")

        print("Capture d'une image de test...")
        img = model.window_capture.screenshot()

        if img is None:
            print("❌ Échec de la capture d'écran. Vérifiez que le jeu est ouvert.")
            return

        print(f"✓ Image capturée avec succès: {img.shape}")

        print("Test de prédiction...")
        x, y, resource, _ = model.predict()

        if resource is not None:
            resource_name = model.classes[resource]["label"]
            print(f"✓ Détection réussie! Ressource: {resource_name} à ({x}, {y})")
        else:
            print("ℹ️ Aucune ressource détectée. Essayez d'ajuster le seuil de confiance ou de vous déplacer dans le jeu.")

        print("\nTest terminé avec succès! Le système est prêt à être utilisé.")

    except Exception as e:
        logger.error(f"Erreur pendant le test: {e}")
    finally:
        # Arrêter le système anti-détection
        shutdown_anti_detection(anti_detection)

def run_gui_mode():
    """Exécuter le mode interface graphique"""
    if not GUI_AVAILABLE:
        logger.error("Interface graphique non disponible. Installez PyQt5 avec 'pip install PyQt5'.")
        print("❌ Interface graphique non disponible. Installez PyQt5 avec 'pip install PyQt5'.")
        return

    try:
        logger.info("Démarrage de l'interface graphique")
        run_gui()
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'interface graphique: {e}")
        print(f"❌ Erreur lors du démarrage de l'interface graphique: {e}")

def main():
    """Fonction principale"""
    # Analyser les arguments de la ligne de commande
    args = parse_arguments()

    # Exécuter le mode sélectionné
    if args.mode == 'debug':
        run_debug_mode(args)
    elif args.mode == 'gather':
        run_gathering_mode(args)
    elif args.mode == 'test':
        run_test_mode(args)
    elif args.mode == 'gui':
        run_gui_mode()
    else:
        logger.error(f"Mode inconnu: {args.mode}")

def print_header():
    """Affiche une bannière ASCII au démarrage"""
    header = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   █████╗ ██╗     ██████╗ ██╗ ██████╗ ███╗   ██╗          ║
    ║  ██╔══██╗██║     ██╔══██╗██║██╔═══██╗████╗  ██║          ║
    ║  ███████║██║     ██████╔╝██║██║   ██║██╔██╗ ██║          ║
    ║  ██╔══██║██║     ██╔══██╗██║██║   ██║██║╚██╗██║          ║
    ║  ██║  ██║███████╗██████╔╝██║╚██████╔╝██║ ╚████║          ║
    ║  ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝ ╚═════╝ ╚═╝  ╚═══╝          ║
    ║                                                           ║
    ║  ██████╗ ██████╗  ████████╗                              ║
    ║  ██╔══██╗██╔═══██╗╚══██╔══╝                              ║
    ║  ██████╔╝██║   ██║   ██║                                 ║
    ║  ██╔══██╗██║   ██║   ██║                                 ║
    ║  ██████╔╝╚██████╔╝   ██║                                 ║
    ║  ╚═════╝  ╚═════╝    ╚═╝                                 ║
    ║                                                           ║
    ║               BOT DE RÉCOLTE AMÉLIORÉ                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(header)
    print("Utilisation: python main.py [--mode {gather,debug,test,gui}] [--debug] [--confidence 0.7] ...")
    print("Pour plus d'options: python main.py --help\n")

def print_disclaimer():
    """Affiche un avertissement sur l'utilisation du bot"""
    disclaimer = """
    ⚠️  AVERTISSEMENT  ⚠️

    Ce bot a été créé à des fins éducatives et expérimentales uniquement.
    L'utilisation de bots et d'automatisation dans Albion Online va à l'encontre
    des conditions d'utilisation du jeu et peut entraîner la suspension ou le
    bannissement de votre compte.

    Utilisez ce logiciel à vos propres risques. Les développeurs n'assument
    aucune responsabilité pour les conséquences de son utilisation.

    En continuant, vous acceptez ces conditions.
    """
    print(disclaimer)
    input("Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    print_header()
    print_disclaimer()
    main()
