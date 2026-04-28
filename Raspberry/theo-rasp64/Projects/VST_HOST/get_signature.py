import requests
import re
import subprocess
import os


def download_organteq(progress_callback=None) -> str:
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
        f"{base_url}/try?file=organteq_linux_trial_v212.7z",
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
    download_url = api_data["url"].replace("\\/", "/")  # corrige les slashes �chapp�s

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


def install_organteq(progress_callback=None):
    try:
        # 1. Téléchargement via Python (plus de wget)
        download_path = download_organteq(progress_callback)

        script_path = os.path.join(os.path.dirname(__file__), "sh_installation_files", "organteq.sh")

        # 2. Lance le script bash uniquement pour l'installation
        process = subprocess.Popen(
            ["sudo", "bash", script_path, download_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            line = line.strip()
            print(line)
            if progress_callback:
                progress_callback(line)

        process.wait()

        if process.returncode != 0:
            raise RuntimeError("Echec de l'installation de Organteq")

        return True

    except Exception as e:
        raise RuntimeError(f"Erreur : {str(e)}")


install_organteq()