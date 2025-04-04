# Guide d'installation du Bot de Récolte Albion

Ce guide vous aidera à installer et configurer correctement le Bot de Récolte Albion, en évitant les problèmes courants.

## Méthode recommandée : Script d'installation automatique

Pour une installation simplifiée, utilisez notre script d'installation :

1. Assurez-vous d'avoir Python 3.8 ou supérieur installé
2. Ouvrez une invite de commande/terminal dans le dossier du bot
3. Exécutez le script d'installation :

```bash
python setup.py
```

Ce script va :
- Vérifier votre version de Python
- Installer les dépendances avec des versions compatibles
- Vérifier si le modèle est présent
- Créer des scripts de lancement rapide

## Installation manuelle

Si vous préférez installer manuellement, voici les étapes à suivre :

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git (pour cloner le dépôt)

### Étapes d'installation

1. **Cloner le dépôt** (si ce n'est pas déjà fait) :
   ```bash
   git clone https://github.com/Michelprogram/albion-gathering-bot.git
   cd albion-gathering-bot
   ```

2. **Installer les dépendances dans le bon ordre** :

   Le bon ordre d'installation est crucial pour éviter les problèmes de compatibilité entre NumPy et OpenCV.

   ```bash
   # D'abord, installer NumPy avec une version spécifique
   pip install numpy==1.26.3

   # Ensuite, installer OpenCV avec une version spécifique
   pip install opencv-python==4.8.1.78

   # Installer les autres dépendances
   pip install -r requirements.txt
   ```

3. **Télécharger le modèle YOLOv5** :

   Si le fichier `best.pt` n'est pas présent dans le dossier racine, vous devez le télécharger depuis [Roboflow](https://universe.roboflow.com/albiononline-c8fxi/albiongathering) et le placer dans le dossier racine.

## Résolution des problèmes courants

### Erreur : `numpy.core.multiarray failed to import`

Cette erreur se produit lorsqu'il y a un conflit entre la version de NumPy et OpenCV. Pour résoudre ce problème :

1. Désinstaller NumPy et OpenCV :
   ```bash
   pip uninstall numpy opencv-python -y
   ```

2. Installer les versions compatibles dans le bon ordre :
   ```bash
   pip install numpy==1.26.3
   pip install opencv-python==4.8.1.78
   ```

### Erreur : `AttributeError: _ARRAY_API not found`

C'est une erreur similaire due à un conflit entre NumPy 2.x et OpenCV. Suivez les mêmes étapes que ci-dessus pour la résoudre.

### Erreur : `ImportError: DLL load failed while importing cv2`

Sur Windows, cette erreur peut survenir si les bibliothèques Visual C++ Redistributable ne sont pas installées :

1. Téléchargez et installez [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Redémarrez votre ordinateur
3. Réinstallez les dépendances comme indiqué ci-dessus

### Erreur : `No module named 'PyQt5'`

Si vous rencontrez cette erreur lors du lancement de l'interface graphique :

```bash
pip install PyQt5
```

## Lancement du bot

Une fois l'installation terminée, vous pouvez lancer le bot de plusieurs façons :

### Avec les scripts de lancement (Recommandé)

Si vous avez utilisé le script d'installation, des scripts de lancement ont été créés :

- **Windows** :
  - `run_gui.bat` - Lance l'interface graphique
  - `run_test.bat` - Lance le mode test
  - `run_gathering.bat` - Lance le mode récolte

- **Linux/Mac** :
  - `./run_gui.sh` - Lance l'interface graphique
  - `./run_test.sh` - Lance le mode test
  - `./run_gathering.sh` - Lance le mode récolte

### Avec les commandes Python

- **Interface graphique** :
  ```bash
  python gui_main.py
  ```

- **Mode test** :
  ```bash
  python main.py --mode test
  ```

- **Mode récolte** :
  ```bash
  python main.py --mode gather
  ```

## Environnements virtuels (Avancé)

Pour une installation plus propre, vous pouvez utiliser un environnement virtuel Python :

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances dans le bon ordre
pip install numpy==1.26.3
pip install opencv-python==4.8.1.78
pip install -r requirements.txt
```

## Support

Si vous rencontrez des problèmes, veuillez ouvrir une issue sur GitHub ou contacter les développeurs.

---

⚠️ **Rappel** : Ce bot est développé à des fins éducatives uniquement. L'utilisation de bots dans Albion Online va à l'encontre des conditions d'utilisation du jeu.
