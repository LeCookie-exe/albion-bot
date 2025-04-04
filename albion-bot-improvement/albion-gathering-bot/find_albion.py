import psutil
import os
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
    import json
    
    config = {
        "process": {
            "pid": process_info['pid'],
            "name": process_info['name'],
            "exe": process_info['exe']
        }
    }
    
    with open('albion_process.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"Informations du processus sauvegardées dans albion_process.json")

if __name__ == "__main__":
    processes = find_albion_process()
    
    if processes:
        if len(processes) == 1:
            # Si un seul processus est trouvé, l'utiliser automatiquement
            process_to_use = processes[0]
            save_process_info(process_to_use)
        else:
            # Si plusieurs processus sont trouvés, demander à l'utilisateur de choisir
            try:
                choice = int(input("\nPlusieurs processus trouvés. Entrez le numéro du processus à utiliser: "))
                if 1 <= choice <= len(processes):
                    process_to_use = processes[choice-1]
                    save_process_info(process_to_use)
                else:
                    print("Choix invalide.")
            except ValueError:
                print("Veuillez entrer un nombre valide.")
    else:
        print("\nVérifiez qu'Albion Online est bien lancé et réessayez.")