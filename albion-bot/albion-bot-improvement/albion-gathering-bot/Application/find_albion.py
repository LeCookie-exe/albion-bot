import psutil
import os
import json
import time
import win32gui
import win32process
import win32con
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("find_albion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FindAlbion")

def find_albion_process():
    logger.info("Recherche des processus Albion...")
    found_processes = []

    # Liste des noms de processus possibles pour Albion Online
    possible_process_names = [
        'albion-online', 'albiononline', 'albion online',
        'albion', 'albionclient'
    ]

    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            proc_info = proc.info
            if not proc_info['name']:
                continue

            process_name = proc_info['name'].lower()
            process_exe = proc_info['exe'].lower() if proc_info['exe'] else ""

            # Recherche par nom de processus
            name_match = any(name in process_name for name in possible_process_names)

            # Recherche par chemin d'exécution
            exe_match = any(name in process_exe for name in possible_process_names)

            if name_match or exe_match:
                window_title = get_window_title_for_process(proc_info['pid'])

                found_processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'exe': proc_info['exe'] if proc_info['exe'] else "Inconnu",
                    'window_title': window_title
                })

                logger.info(f"Trouvé: PID={proc_info['pid']}, Nom={proc_info['name']}, Fenêtre={window_title}")

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.debug(f"Exception lors de l'accès au processus: {e}")
            pass

    if found_processes:
        logger.info(f"Trouvé {len(found_processes)} processus liés à Albion")

        # Trier les processus pour mettre en priorité ceux qui ont une fenêtre
        found_processes.sort(key=lambda p: p.get('window_title', '') != '', reverse=True)

        for i, proc in enumerate(found_processes, 1):
            window_info = f", Fenêtre: {proc.get('window_title', 'Non trouvée')}" if proc.get('window_title') else ""
            logger.info(f"{i}. PID: {proc['pid']}, Nom: {proc['name']}{window_info}, Exécutable: {proc['exe']}")

        return found_processes
    else:
        logger.warning("Aucun processus Albion trouvé.")
        return []

def get_window_title_for_process(pid):
    """Obtient le titre de la fenêtre principale pour un processus donné"""
    window_title = None

    def callback(hwnd, _):
        nonlocal window_title
        if win32gui.IsWindowVisible(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                title = win32gui.GetWindowText(hwnd)
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                # Vérifier si c'est une fenêtre principale (avec titre et style approprié)
                if title and (style & win32con.WS_OVERLAPPEDWINDOW):
                    window_title = title
                    return False
        return True

    try:
        win32gui.EnumWindows(callback, None)
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de fenêtre pour PID {pid}: {e}")

    return window_title

def save_process_info(process_info):
    """Sauvegarde les informations du processus dans un fichier de configuration"""

    if 'window_title' in process_info:
        window_name = process_info['window_title']
    else:
        # Utiliser un nom de fenêtre par défaut si non trouvé
        window_name = "Albion Online Client"

    config = {
        "process": {
            "pid": process_info['pid'],
            "name": process_info['name'],
            "exe": process_info['exe'],
            "window_name": window_name
        },
        "capture_mode": "process",
        "timestamp": time.time()
    }

    # Sauvegarder dans le dossier racine
    try:
        with open('albion_process.json', 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Fichier de configuration sauvegardé: albion_process.json")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de albion_process.json: {e}")

    # Sauvegarder également dans le dossier Application pour assurer la synchronisation
    try:
        os.makedirs('Application', exist_ok=True)
        with open('Application/albion_process.json', 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Fichier de configuration sauvegardé: Application/albion_process.json")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de Application/albion_process.json: {e}")

    # Créer un fichier de configuration globale
    try:
        config_global = {
            "albion_pid": process_info['pid'],
            "capture_mode": "process",
            "window_name": window_name,
            "last_update": time.time()
        }

        with open('config.json', 'w') as f:
            json.dump(config_global, f, indent=4)
        logger.info(f"Fichier de configuration globale sauvegardé: config.json")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de config.json: {e}")

    logger.info(f"Informations du processus sauvegardées avec succès")

    # Créer un fichier README qui explique comment utiliser la configuration
    try:
        with open('CAPTURE_CONFIG.txt', 'w') as f:
            f.write(f"""
===== CONFIGURATION DE CAPTURE ALBION =====

PID trouvé: {process_info['pid']}
Nom du processus: {process_info['name']}
Chemin: {process_info['exe']}
Fenêtre: {window_name}

Cette configuration a été générée le {time.ctime()}
Le bot utilisera ce PID pour détecter la fenêtre de jeu.

Si le jeu n'est toujours pas détecté:
1. Fermez et relancez Albion Online
2. Exécutez à nouveau find_albion.py
3. Relancez le bot
""")
        logger.info(f"Fichier d'instructions sauvegardé: CAPTURE_CONFIG.txt")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de CAPTURE_CONFIG.txt: {e}")

if __name__ == "__main__":
    processes = find_albion_process()

    if processes:
        if len(processes) == 1:
            # Si un seul processus est trouvé, l'utiliser automatiquement
            process_to_use = processes[0]
            save_process_info(process_to_use)
            logger.info("Un seul processus trouvé et configuré automatiquement")
            print("\nConfiguration sauvegardée ! Vous pouvez maintenant lancer run_gui.bat")
        else:
            # Si plusieurs processus sont trouvés, demander à l'utilisateur de choisir
            print("\nPlusieurs processus trouvés. Veuillez choisir :")
            for i, proc in enumerate(processes, 1):
                window_info = f", Fenêtre: {proc.get('window_title', 'Non trouvée')}" if proc.get('window_title') else ""
                print(f"{i}. PID: {proc['pid']}, Nom: {proc['name']}{window_info}")

            try:
                choice = int(input("\nEntrez le numéro du processus à utiliser: "))
                if 1 <= choice <= len(processes):
                    process_to_use = processes[choice-1]
                    save_process_info(process_to_use)
                    print("\nConfiguration sauvegardée ! Vous pouvez maintenant lancer run_gui.bat")
                else:
                    logger.error(f"Choix invalide: {choice}")
                    print("Choix invalide.")
            except ValueError as e:
                logger.error(f"Erreur lors de la saisie du choix: {e}")
                print("Veuillez entrer un nombre valide.")
    else:
        print("\nVérifiez qu'Albion Online est bien lancé et réessayez.")
