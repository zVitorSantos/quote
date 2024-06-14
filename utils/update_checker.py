import requests
import os
import subprocess
from packaging import version

GITHUB_API_URL = "https://api.github.com/repos/zVitorSantos/quote/releases/latest"
CURRENT_VERSION = "1.0.0"

def get_latest_version():
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        latest_release = response.json()
        return latest_release["tag_name"], latest_release["assets"][0]["browser_download_url"]
    except requests.RequestException as e:
        print(f"Erro ao verificar atualizações: {e}")
        return None, None

def check_for_updates(current_version):
    latest_version, download_url = get_latest_version()
    if latest_version and version.parse(latest_version) > version.parse(current_version):
        return latest_version, download_url
    return None, None

def download_installer(download_url, installer_path):
    response = requests.get(download_url)
    response.raise_for_status()
    with open(installer_path, 'wb') as file:
        file.write(response.content)

def update_application(current_version):
    latest_version, download_url = check_for_updates(current_version)
    if latest_version:
        installer_path = os.path.join(os.getenv('TEMP'), 'QuotesInstaller.exe')
        download_installer(download_url, installer_path)
        subprocess.Popen([installer_path], shell=True)
        return True
    return False
