import os
import shutil
import subprocess
import requests
import re
import time
import xml.etree.ElementTree as ET


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_SCRIPT_DIR = "sh_installation_files"

class Plugin:
    @classmethod
    def is_installed(cls, command: str) -> bool:
        if "/" in command:
            return os.path.exists(command)
        else:
            return shutil.which(command) is not None
    
    @classmethod
    def install(cls, plugin_name: str, command: str, install_script_args = [], progress_callback=None):

        if cls.is_installed():
            message = f"{plugin_name} est déjà installé ({shutil.which(command)})"
            print(message)
            if progress_callback:
                progress_callback(f"ALREADY_INSTALLED:{message}")
            return False
            
        script_path = os.path.join(BASE_DIR, INSTALL_SCRIPT_DIR, plugin_name.lower() + "_install.sh")

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script introuvable : {script_path}")

        os.chmod(script_path, 0o755)

        process = subprocess.Popen(
            ["sudo", "bash", script_path] + install_script_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            line = line.strip()
            if progress_callback:
                progress_callback(line)

        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"Echec de l'installation de {plugin_name}")

        return True
    
class Modartt(Plugin):

    @classmethod
    def is_installed(cls, command: str) -> bool:
        return super().is_installed(command)

    @classmethod
    def download(cls, file: str, progress_callback=None) -> str:
        base_url = "https://www.modartt.com"
        session  = requests.Session()
        headers  = {
            "User-Agent":   "Mozilla/5.0 (X11; Linux aarch64)",
            "Referer":      f"{base_url}/try?file=organteq_linux_trial_v212.7z",
            "Origin":       base_url,
        }

        # 1. Récupère la page + signature + cookies
        if progress_callback:
            progress_callback("Récupération de la signature...")

        response = session.get(
            f"{base_url}/try?file={file}",
            headers=headers
        )
        html = response.text

        sig_match  = re.search(r'data-mrtc-signature="([^"]+)"', html)
        file_match = re.search(r'data-mrtc-file="([^"]+)"', html)
        csrf_match = re.search(r'meta name="csrf:token" content="([^"]+)"', html)

        if not sig_match or not file_match or not csrf_match:
            raise RuntimeError("Signature, fichier ou CSRF token introuvable")

        signature  = sig_match.group(1)
        file_name  = file_match.group(1)
        csrf_token = csrf_match.group(1)

        if progress_callback:
            progress_callback(f"Signature : {signature}")

        # 2. POST sur le formulaire pour obtenir les cookies de session
        session.post(
            f"{base_url}/download?file={file_name}&signature={signature}",
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            data={
                "file":       file_name,
                "signature":  signature,
                "email_addr": "",
                "continue":   "Download"
            }
        )

        # 3. Appel API pour obtenir l'URL de téléchargement
        if progress_callback:
            progress_callback("Récupération de l'URL de téléchargement...")

        api_response = session.post(
            f"{base_url}/api/0/download",
            headers={
                **headers,
                "Content-Type": "application/json",
                "Csrf-Token":   csrf_token,
                "Accept":       "*/*"
            },
            json={
                "file":      file_name,
                "get":       "url",
                "info":      1,
                "signature": signature
            }
        )

        api_data     = api_response.json()
        download_url = api_data["url"].replace("\\/", "/")  # corrige les slashes Echappés

        if progress_callback:
            progress_callback(f"URL obtenue : {download_url}")

        # 4. Téléchargement du fichier
        download_path = f"/tmp/{file_name}"

        if os.path.exists(download_path):
            os.remove(download_path)

        if progress_callback:
            progress_callback("Téléchargement en cours...")

        with session.get(download_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            total    = int(r.headers.get("content-length", 0))
            received = 0

            with open(download_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    received += len(chunk)

                    if total and progress_callback:
                        percent = int(received * 100 / total)
                        progress_callback(f"Téléchargement : {percent}%")

        # 5. Vérifie le sha1
        import hashlib
        sha1     = hashlib.sha1(open(download_path, "rb").read()).hexdigest()
        expected = api_data["info"]["sha1"]

        if sha1 != expected:
            raise RuntimeError(f"SHA1 invalide : {sha1} != {expected}")

        if progress_callback:
            progress_callback("Téléchargement terminé et vérifié !")

        return download_path

    @classmethod
    def install(cls, plugin_name: str, command: str, prefs_path: str, progress_callback=None):
        try:
            # 1. Téléchargement
            if (plugin_name == "Pianoteq"):
                download_file = "pianoteq_trial_v912.tar.xz"
            elif (plugin_name == "Organteq"):
                download_file = "organteq_linux_trial_v212.7z"
            else:
                return False

            download_path = cls.download(download_file, progress_callback)
            
            status = super().install(plugin_name, command, [download_path], print)

            if status == True:
                process = subprocess.Popen([command, "--headless"])
                time.sleep(10)
                process.terminate()
                process.wait()
            return status

        except Exception as e:
            raise RuntimeError(f"Erreur : {str(e)}")

    @classmethod
    def change_audio_device_prefs(cls, plugin_name: str, prefs_path: str):
        if os.path.exists(prefs_path):
            tree = ET.parse(prefs_path)
            root = tree.getroot()

            audio_setup = None
            for value in root.iter('VALUE'):
                if value.get('name') == 'audio-setup':
                    audio_setup = value
                    break

            if audio_setup is None:
                audio_setup = ET.SubElement(root, 'VALUE', {'name': 'audio-setup'})

            device = audio_setup.find('DEVICESETUP')
            if device is None:
                device = ET.SubElement(audio_setup, 'DEVICESETUP')

            device.set('deviceType', 'JACK')
            device.set('audioOutputDeviceName', 'Auto-connect ON')
            device.set('audioInputDeviceName', '')
            device.set('audioDeviceRate', '48000.0')
            device.set('audioDeviceBufferSize', '1024')
            device.set('forceStereo', '0')

            tree.write(prefs_path, xml_declaration=True, encoding='unicode')
            print("[", plugin_name, "]", " Jack config applied to audio device preferences.")
        else:
            print(prefs_path)
            print("[",plugin_name,"]", "No preferences file.")
