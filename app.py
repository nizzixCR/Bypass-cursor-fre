import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
import platform
import pyfiglet
from colorama import Fore, Style, init
import requests
import tempfile
import subprocess
import time

init(autoreset=True)

def backup_file(file_path: str):
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)

def get_storage_file():
    system = platform.system()
    if system == "Windows":
        return Path(os.getenv("APPDATA")) / "Cursor" / "User" / "globalStorage" / "storage.json"
    elif system == "Darwin": 
        return Path(os.path.expanduser("~")) / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "storage.json"
    elif system == "Linux":
        return Path(os.path.expanduser("~")) / ".config" / "Cursor" / "User" / "globalStorage" / "storage.json"
    else:
        raise OSError(f"Unsupported operating system: {system}")

def reset_cursor_id():
    storage_file = get_storage_file()
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    backup_file(storage_file)

    if not storage_file.exists():
        data = {}
    else:
        with open(storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

    machine_id = os.urandom(32).hex()
    mac_machine_id = os.urandom(32).hex()
    dev_device_id = str(uuid.uuid4())

    data["telemetry.machineId"] = machine_id
    data["telemetry.macMachineId"] = mac_machine_id
    data["telemetry.devDeviceId"] = dev_device_id

    with open(storage_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print("🎉 Device IDs have been successfully reset. The new device IDs are: \n")
    print(
        json.dumps(
            {
                "machineId": machine_id,
                "macMachineId": mac_machine_id,
                "devDeviceId": dev_device_id,
            },
            indent=2))

def update_telemetry_data(file_path: str, is_cursor: bool = True):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(Fore.RED + f"Error: The file {file_path} was not found.")
        return False
    except json.JSONDecodeError:
        print(Fore.RED + "Error: Failed to decode JSON data from the file.")
        return False

    def generate_random_id():
        return str(uuid.uuid4()).replace('-', '')

    data["telemetry.machineId"] = generate_random_id()
    data["telemetry.sqmId"] = "{" + generate_random_id() + "}"
    data["telemetry.devDeviceId"] = generate_random_id()
    if is_cursor:
        data["telemetry.macMachineId"] = generate_random_id()

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        print(Fore.GREEN + f"Successfully updated the telemetry data for {'Cursor' if is_cursor else 'Windsurf'} AI!")
        return True
    except IOError as e:
        print(Fore.RED + f"Error writing to the file: {e}")
        return False

def cursor_and_windsurf():
    user_home = os.path.expanduser("~")
    cursor = os.path.join(user_home, r'AppData\Roaming\Cursor\User\globalStorage\storage.json')
    windsurf = os.path.join(user_home, r'AppData\Roaming\Windsurf\User\globalStorage\storage.json')

    update_telemetry_data(windsurf, False)
    update_telemetry_data(cursor, True)

def download_and_install_cursor():
    try:
        print(Fore.CYAN + "Téléchargement de Cursor...")
        
        response = requests.get("https://www.cursor.com/api/download?platform=win32-x64&releaseTrack=stable")
        if response.status_code != 200:
            print(Fore.RED + "Erreur lors de la récupération de l'URL de téléchargement")
            return False
            
        download_info = response.json()
        download_url = download_info["downloadUrl"]
        
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "CursorInstaller.exe")
        
        print(Fore.YELLOW + "Téléchargement en cours...")
        response = requests.get(download_url, stream=True)
        if response.status_code != 200:
            print(Fore.RED + "Erreur lors du téléchargement")
            return False
            
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        print(Fore.GREEN + "Téléchargement terminé!")
        print(Fore.YELLOW + "Installation en cours...")
        
        process = subprocess.Popen([installer_path], shell=True)
        process.wait()
        
        while process.poll() is None:
            time.sleep(1)
            
        print(Fore.GREEN + "Installation terminée!")
        
        try:
            os.remove(installer_path)
            print(Fore.GREEN + "Fichiers temporaires nettoyés")
        except:
            print(Fore.YELLOW + "Impossible de nettoyer les fichiers temporaires")
            
        return True
        
    except Exception as e:
        print(Fore.RED + f"Une erreur est survenue: {str(e)}")
        return False

def desinstall_cursor():
    try:
        print(Fore.CYAN + "Désinstallation de Cursor...")
        
        try:
            subprocess.run(["taskkill", "/F", "/IM", "Cursor.exe"], check=True)
            print(Fore.GREEN + "Processus Cursor arrêté")
        except:
            print(Fore.YELLOW + "Aucun processus Cursor en cours d'exécution")

        paths_to_remove = [
            os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Cursor"),
            os.path.expanduser("~\\AppData\\Local\\Programs\\cursor"),
            os.path.expanduser("~\\AppData\\Roaming\\Cursor")
        ]

        for path in paths_to_remove:
            try:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                    print(Fore.GREEN + f"Dossier supprimé: {path}")
                else:
                    print(Fore.YELLOW + f"Dossier non trouvé: {path}")
            except Exception as e:
                print(Fore.RED + f"Erreur lors de la suppression de {path}: {str(e)}")

        print(Fore.GREEN + "Cursor a été désinstallé avec succès!")
        return True
        
    except Exception as e:
        print(Fore.RED + f"Une erreur est survenue lors de la désinstallation: {str(e)}")
        return False

def clean_temp_folder():
    try:
        print(Fore.CYAN + "Nettoyage du dossier temporaire...")
        temp_dir = os.path.expanduser("~\\AppData\\Local\\Temp")
        
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                print(Fore.GREEN + f"Supprimé: {item}")
            except Exception as e:
                print(Fore.RED + f"Erreur lors de la suppression de {item}: {str(e)}")
                
        print(Fore.GREEN + "Dossier temporaire nettoyé avec succès!")
        return True
        
    except Exception as e:
        print(Fore.RED + f"Une erreur est survenue lors du nettoyage: {str(e)}")
        return False

def launch_and_close_cursor():
    try:
        print(Fore.CYAN + "Lancement de Cursor...")
        cursor_path = os.path.expanduser("~\\AppData\\Local\\Programs\\cursor\\Cursor.exe")
        
        if not os.path.exists(cursor_path):
            print(Fore.RED + "Cursor n'est pas installé!")
            return False
            
        try:
            subprocess.run(["taskkill", "/F", "/IM", "Cursor.exe"], check=True)
            print(Fore.YELLOW + "Fermeture de l'instance précédente de Cursor")
        except:
            pass
            
        process = subprocess.Popen([cursor_path])
        print(Fore.GREEN + "Cursor a été lancé")
        
        print(Fore.YELLOW + "Attente de 3 secondes...")
        time.sleep(3)
        
        try:
            subprocess.run(["taskkill", "/F", "/IM", "Cursor.exe"], check=True)
            print(Fore.GREEN + "Cursor a été fermé avec succès")
            return True
        except:
            print(Fore.RED + "Erreur lors de la fermeture de Cursor")
            return False
            
    except Exception as e:
        print(Fore.RED + f"Une erreur est survenue: {str(e)}")
        return False

if __name__ == "__main__":
    launch_and_close_cursor()
    reset_cursor_id()
    cursor_and_windsurf()
    clean_temp_folder()
    desinstall_cursor()
    clean_temp_folder()
    print("Create you an new account cursor with proton mail not an fcking temp mail")
    input("Press [ENTER]")
    download_and_install_cursor()
    clean_temp_folder()
    reset_cursor_id()
    cursor_and_windsurf()
    launch_and_close_cursor()
    reset_cursor_id()
    cursor_and_windsurf()
    print(Fore.GREEN + "Toutes les opérations ont été effectuées avec succès!")