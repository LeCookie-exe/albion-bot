#!/usr/bin/env python
"""
Script principal pour lancer l'interface graphique du bot de récolte Albion.
"""

import sys
import os
import logging
import json
import argparse
from Application.GUI.main_window import run_gui

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("albion_bot_gui.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AlbionBotGUI")

def ensure_process_config():
    """Vérifie que la configuration du processus existe et est à jour"""
    if os.path.exists('albion_process.json'):
        try:
            with open('albion_process.json', 'r') as f:
                config = json.load(f)
                
            # Vérifier que le fichier contient les informations nécessaires
            if 'process' in config and 'pid' in config['process']:
                logger.info(f"Configuration du processus trouvée: PID={config['process']['pid']}")
                
                # Vérifier si la copie dans le dossier Application existe
                if not os.path.exists('Application/albion_process.json'):
                    # Copier le fichier dans le dossier Application
                    os.makedirs('Application', exist_ok=True)
                    with open('Application/albion_process.json', 'w') as f:
                        json.dump(config, f, indent=4)
                    logger.info("Configuration copiée dans le dossier Application")
                
                return True
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la configuration: {e}")
    
    logger.warning("Configuration de processus non trouvée ou invalide")
    return False

def parse_args():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description="Lanceur de l'interface graphique du bot Albion")
    parser.add_argument('--force-pid-detection', action='store_true', 
                        help='Force l\'utilisation de la détection par PID')
    return parser.parse_args()

def main():
    """Fonction principale pour démarrer l'interface graphique"""
    args = parse_args()
    
    if args.force_pid_detection:
        # Vérifier que la configuration du processus existe
        if not ensure_process_config():
            logger.warning("La détection par PID a été forcée mais aucune configuration n'a été trouvée")
            print("⚠️ ATTENTION: Aucune configuration de détection n'a été trouvée.")
            print("Exécutez d'abord 'python find_albion.py' pour détecter le jeu.")
            input("Appuyez sur Entrée pour continuer quand même...")
    
    logger.info("Démarrage de l'interface graphique")
    run_gui()

if __name__ == "__main__":
    main()