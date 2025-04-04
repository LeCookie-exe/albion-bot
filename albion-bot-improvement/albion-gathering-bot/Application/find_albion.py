import psutil
import os
import json
import time

def find_albion_process():
    print("Recherche des processus Albion...")
    found_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            proc_info = proc.info
            process_name = proc_info['name'].lower() if proc_info['name'] else ""
            
            # Recherche par nom de processus
            if 'albion' in process_name:
                found_processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'exe': proc_info['exe'] if 'exe' in proc_info and proc_info['exe'] else "Inconnu"
                })
                
            # Recherche alternative par chemin d'exécution
            elif proc_info['exe'] and 'albion' in proc_info['exe'].lower():
                found_processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'exe': proc_info['exe']
                })
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if found_processes:
        print(f"Trouvé {len(found_processes)} processus liés à Albion :")
        for i, proc in enumerate(found_processes, 1):
            print(f"{i}. PID: {proc['pid']}, Nom: {proc['name']}, Exécutable: {proc['exe']}")
        return found_processes
    else:
        print("Aucun processus Albion trouvé.")
        return []

def save_process_info(process_info):
    """Sauvegarde les informations du processus dans un fichier de configuration"""
    config = {
        "process": {
            "pid": process_info['pid'],
            "name": process_info['name'],
            "exe": process_info['exe']
        },
        "capture_mode": "process",
        "timestamp": time.time()
    }
    
    # Sauvegarder dans le dossier racine
    with open('albion_process.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    # Sauvegarder également dans le dossier Application pour assurer la synchronisation
    os.makedirs('Application', exist_ok=True)
    with open('Application/albion_process.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    # Créer un fichier de configuration globale
    config_global = {
        "albion_pid": process_info['pid'],
        "capture_mode": "process",
        "last_update": time.time()
    }
    
    with open('config.json', 'w') as f:
        json.dump(config_global, f, indent=4)
    
    print(f"Informations du processus sauvegardées dans plusieurs fichiers de configuration")
    
    # Créer un fichier README qui explique comment utiliser la configuration
    with open('CAPTURE_CONFIG.txt', 'w') as f:
        f.write(f"""
===== CONFIGURATION DE CAPTURE ALBION =====

PID trouvé: {process_info['pid']}
Nom du processus: {process_info['name']}
Chemin: {process_info['exe']}

Cette configuration a été générée le {time.ctime()}
Le bot utilisera ce PID pour détecter la fenêtre de jeu.

Si le jeu n'est toujours pas détecté:
1. Fermez et relancez Albion Online
2. Exécutez à nouveau find_albion.py
3. Relancez le bot
""")

if __name__ == "__main__":
    processes = find_albion_process()
    
    if processes:
        if len(processes) == 1:
            # Si un seul processus est trouvé, l'utiliser automatiquement
            process_to_use = processes[0]
            save_process_info(process_to_use)
            print("\nConfiguration sauvegardée ! Vous pouvez maintenant lancer run_gui.bat")
        else:
            # Si plusieurs processus sont trouvés, demander à l'utilisateur de choisir
            try:
                choice = int(input("\nPlusieurs processus trouvés. Entrez le numéro du processus à utiliser: "))
                if 1 <= choice <= len(processes):
                    process_to_use = processes[choice-1]
                    save_process_info(process_to_use)
                    print("\nConfiguration sauvegardée ! Vous pouvez maintenant lancer run_gui.bat")
                else:
                    print("Choix invalide.")
            except ValueError:
                print("Veuillez entrer un nombre valide.")
    else:
        print("\nVérifiez qu'Albion Online est bien lancé et réessayez.")