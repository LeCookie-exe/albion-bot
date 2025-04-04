#!/usr/bin/env python
"""
Script d'installation pour le bot Albion Gathering Bot.
Ce script vérifie et installe les dépendances nécessaires.
"""

import os
import sys
import subprocess
import platform

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
    ║       INSTALLATION DU BOT DE RÉCOLTE ALBION ONLINE        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(header)

def check_python_version():
    """Vérifie que la version de Python est suffisante"""
    print("\n📋 Vérification de la version de Python...")

    major, minor, _ = platform.python_version_tuple()
    major, minor = int(major), int(minor)

    if major < 3 or (major == 3 and minor < 8):
        print(f"❌ Python 3.8+ requis, mais vous utilisez Python {major}.{minor}")
        print("Veuillez installer Python 3.8 ou supérieur: https://www.python.org/downloads/")
        return False
    else:
        print(f"✅ Python {platform.python_version()} détecté")
        return True

def get_pip_command():
    """Détermine la commande pip à utiliser"""
    # Tester différentes commandes pip
    commands = ["pip", "pip3", f"{sys.executable} -m pip"]

    for cmd in commands:
        try:
            subprocess.run(f"{cmd} --version", shell=True, check=True, capture_output=True)
            return cmd
        except subprocess.CalledProcessError:
            continue

    return None

def install_dependencies():
    """Installe les dépendances nécessaires"""
    print("\n📦 Installation des dépendances...")

    pip_cmd = get_pip_command()
    if not pip_cmd:
        print("❌ Impossible de trouver pip. Veuillez l'installer manuellement.")
        return False

    print(f"📌 Utilisation de: {pip_cmd}")

    # Installation des dépendances de base
    try:
        # D'abord installer numpy avec une version compatible
        print("📥 Installation de numpy...")
        subprocess.run(f"{pip_cmd} install numpy==1.26.3", shell=True, check=True)

        # Installer OpenCV avec une version compatible
        print("📥 Installation d'OpenCV...")
        subprocess.run(f"{pip_cmd} install opencv-python==4.8.1.78", shell=True, check=True)

        # Installer les autres dépendances
        print("📥 Installation des autres dépendances...")
        subprocess.run(f"{pip_cmd} install -r requirements.txt", shell=True, check=True)

        print("✅ Toutes les dépendances ont été installées avec succès.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances: {e}")
        return False

def check_model_file():
    """Vérifie si le fichier modèle est présent"""
    print("\n🔍 Vérification du modèle YOLOv5...")

    model_path = "best.pt"
    if os.path.exists(model_path):
        print(f"✅ Modèle trouvé: {model_path}")
        return True
    else:
        print("⚠️ Modèle non trouvé.")
        print("Vous devrez télécharger le modèle depuis Roboflow:")
        print("https://universe.roboflow.com/albiononline-c8fxi/albiongathering")
        print(f"Et le placer dans le dossier racine sous le nom '{model_path}'")
        return False

def check_game_installation():
    """Vérifie si Albion Online semble être installé"""
    print("\n🎮 Vérification de l'installation du jeu...")

    # Chemins possibles d'installation d'Albion Online
    possible_paths = []

    if platform.system() == "Windows":
        possible_paths = [
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Albion Online", "game", "Albion-Online.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Albion Online", "game", "Albion-Online.exe"),
            # Ajouter d'autres chemins courants d'installation
        ]
    elif platform.system() == "Darwin":  # macOS
        possible_paths = [
            "/Applications/Albion Online.app",
            # Ajouter d'autres chemins courants d'installation
        ]
    elif platform.system() == "Linux":
        possible_paths = [
            os.path.expanduser("~/.local/share/Steam/steamapps/common/Albion Online/game/bin/Albion-Online"),
            # Ajouter d'autres chemins courants d'installation
        ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Albion Online semble être installé: {path}")
            return True

    print("⚠️ Albion Online n'a pas été trouvé dans les emplacements standard.")
    print("Le bot ne fonctionnera que si le jeu est correctement installé et ouvert.")
    return False

def create_run_scripts():
    """Crée des scripts de lancement rapide"""
    print("\n📝 Création des scripts de lancement...")

    if platform.system() == "Windows":
        # Créer un fichier batch pour lancer l'interface graphique
        with open("run_gui.bat", "w") as f:
            f.write("@echo off\n")
            f.write("echo Lancement de l'interface graphique du bot Albion...\n")
            f.write("python gui_main.py\n")
            f.write("pause\n")

        # Créer un fichier batch pour lancer le mode test
        with open("run_test.bat", "w") as f:
            f.write("@echo off\n")
            f.write("echo Lancement du test du bot Albion...\n")
            f.write("python main.py --mode test\n")
            f.write("pause\n")

        # Créer un fichier batch pour lancer le mode récolte
        with open("run_gathering.bat", "w") as f:
            f.write("@echo off\n")
            f.write("echo Lancement du mode récolte du bot Albion...\n")
            f.write("python main.py --mode gather\n")
            f.write("pause\n")

        print("✅ Scripts batch créés (.bat)")
    else:
        # Créer des scripts shell pour Unix/Linux/Mac
        with open("run_gui.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo Lancement de l'interface graphique du bot Albion...\n")
            f.write("python3 gui_main.py\n")

        with open("run_test.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo Lancement du test du bot Albion...\n")
            f.write("python3 main.py --mode test\n")

        with open("run_gathering.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo Lancement du mode récolte du bot Albion...\n")
            f.write("python3 main.py --mode gather\n")

        # Rendre les scripts exécutables
        os.chmod("run_gui.sh", 0o755)
        os.chmod("run_test.sh", 0o755)
        os.chmod("run_gathering.sh", 0o755)

        print("✅ Scripts shell créés (.sh)")

def main():
    """Fonction principale d'installation"""
    print_header()

    print("\n🔧 Bienvenue dans l'assistant d'installation du bot de récolte Albion Online.")
    print("Cet assistant va vérifier et installer les dépendances nécessaires.")

    # Vérifier la version de Python
    if not check_python_version():
        return

    # Installer les dépendances
    if not install_dependencies():
        return

    # Vérifier le fichier modèle
    check_model_file()

    # Vérifier l'installation du jeu
    check_game_installation()

    # Créer les scripts de lancement
    create_run_scripts()

    print("\n🎉 Installation terminée avec succès !")
    print("\nVous pouvez maintenant lancer le bot avec:")
    if platform.system() == "Windows":
        print("  - run_gui.bat (interface graphique)")
        print("  - run_test.bat (test de fonctionnement)")
        print("  - run_gathering.bat (mode récolte)")
    else:
        print("  - ./run_gui.sh (interface graphique)")
        print("  - ./run_test.sh (test de fonctionnement)")
        print("  - ./run_gathering.sh (mode récolte)")

    print("\n⚠️ N'oubliez pas d'ouvrir Albion Online avant d'utiliser le bot.")
    print("⚠️ Assurez-vous que votre personnage est dans une zone de récolte.")

    input("\nAppuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()
