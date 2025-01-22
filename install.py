#!/usr/bin/env python3
"""
Setup script for installing dependencies for profi.
"""

import os
import glob
import sys
import shutil
import logging
import requests
import zipfile
import tarfile
import gzip
from typing import Union
from pathlib import Path

###############################################################################
# LOGGING CONFIG
###############################################################################
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

###############################################################################
# CONFIG & CONSTANTS
###############################################################################
HOME_DIR = Path.home()
# TODO: Take the value from config if exist
TOOLS_DIR = HOME_DIR / ".local" / "share" / "profi" / "tools"

###############################################################################
# UTILITY FUNCTIONS
###############################################################################
def safe_mkdir(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def clean_dir(directory: Path) -> None:
    """Removes all files and subdirectories in the specified directory."""
    logging.info(f"Cleaning directory: {directory}")
    if not directory.exists():
        return
    for item in directory.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

def download_file(url: str, dest_dir: Path) -> None:
    """
    Download a file from the given URL into dest_dir if it does not already exist.
    """
    filename = url.split('/')[-1]
    dest_file = dest_dir / filename

    if dest_file.exists():
        logging.info(f"Skipping {filename} (already downloaded).")
        return

    logging.info(f"Downloading {filename} from {url}")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_file, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        logging.info(f"Downloaded {filename} successfully.")
    except requests.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        if dest_file.exists():
            dest_file.unlink()

def unzip_files(directory: Path) -> None:
    """
    Unzip all .zip files in the directory to subfolders named after
    the file minus the .zip extension. Then remove the .zip file.
    """
    for zip_file in directory.glob("*.zip"):
        target_dir = directory / zip_file.stem
        logging.info(f"Unzipping {zip_file.name} into {target_dir}")
        with zipfile.ZipFile(zip_file, 'r') as z:
            z.extractall(target_dir)
        zip_file.unlink()

def gunzip_files(directory: Path) -> None:
    """
    Gunzip all .gz files in the directory to a file with the same
    name minus .gz. Then remove the .gz file.
    """
    for gz_file in directory.glob("*.gz"):
        target_path = directory / gz_file.stem
        logging.info(f"Decompressing {gz_file.name} to {target_path.name}")
        with gzip.open(gz_file, 'rb') as f_in:
            with open(target_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        gz_file.unlink()

def untar_files(directory: Path) -> None:
    """
    Untar all .tar files in the directory, extracting them in place,
    then remove the tar file.
    """
    for tar_file in directory.glob("*.tar"):
        logging.info(f"Extracting {tar_file.name}")
        with tarfile.open(tar_file, 'r') as t:
            t.extractall(directory)
        tar_file.unlink()

def safe_move_files(pattern: str, src_dir: Path, dest_dir: Path) -> None:
    """
    Moves matching files from `src_dir` to `dest_subdir` (relative to `src_dir`).
    """
    safe_mkdir(dest_dir)
    for matched in src_dir.glob(pattern):
        logging.info(f"Moving {matched.name} to {dest_dir}")
        shutil.move(str(matched), str(dest_dir / matched.name))

###############################################################################
# DEPENDENCY CLASS
###############################################################################
class Dependency:
    """
    A class that encapsulates the data and installation steps for a single dependency.
    - name: name of the dependency (e.g. 'sharphound')
    - version: version or commit hash to include in the URLs or identify
    - urls: a list of URLs to the resource
    - directory: the name of the final directory where tools will reside
    - post_download_function: an optional function that takes (Path to the tools_dir) as argument.
    """
    def __init__(
        self,
        name: str,
        version: str,
        urls: list[str],
        directory: Path,
        post_download_function=None
    ):
        self.name = name
        self.version = version
        self.urls = urls
        self.directory = directory
        self.post_download_function = post_download_function

    def download(self, dest_dir: Path) -> None:
        """Download each URL for this dependency."""
        for url_template in self.urls:
            url = url_template.format(version=self.version)
            download_file(url, dest_dir)

    def post_download(self, dest_dir: Path) -> None:
        """
        Call the custom post_download_function if any.
        """
        # Run any custom post install steps
        if self.post_download_function:
            self.post_download_function(self, dest_dir)

###############################################################################
# CUSTOM POST-INSTALL FUNCTIONS
###############################################################################
def post_install_mimikatz(dep: Dependency, dest_dir: Path):
    unzip_files(dest_dir)
    extracted_dir = dest_dir / "mimikatz_trunk"
    if extracted_dir.is_dir():
        for item in extracted_dir.iterdir():
            logging.debug(f"Moving {item.name} to {dest_dir}")
            shutil.move(str(item), str(dest_dir))
        extracted_dir.rmdir()

def post_install_sysinternals(dep: Dependency, dest_dir: Path):
    unzip_files(dest_dir)
    # Move all files in SysinternalsSuite to the parent directory
    extracted_dir = dest_dir / "SysinternalsSuite"
    if extracted_dir.is_dir():
        for item in extracted_dir.iterdir():
            logging.debug(f"Moving {item.name} to {dest_dir}")
            shutil.move(str(item), str(dest_dir))
        extracted_dir.rmdir()

def post_install_chisel(dep: Dependency, dest_dir: Path):
    gunzip_files(dest_dir)

def post_install_ligolo(dep: Dependency, dest_dir: Path):
    # Agent - Windows
    safe_move_files("ligolo-ng_agent_*_windows_amd64.zip", dest_dir, Path(f"{dest_dir}/agent/windows"))
    unzip_files(Path(f"{dest_dir}/agent/windows"))
    windowsAgentDir = Path(f"{dest_dir}/agent/windows/ligolo-ng_agent_{dep.version}_windows_amd64")
    safe_move_files("*", windowsAgentDir, Path(f"{dest_dir}/agent/windows"))
    Path.rmdir(windowsAgentDir)

    # Proxy - Linux
    safe_move_files("ligolo-ng_proxy_*_linux_amd64.tar.gz", dest_dir, Path(f"{dest_dir}/proxy/linux"))
    gunzip_files(Path(f"{dest_dir}/proxy/linux"))
    untar_files(Path(f"{dest_dir}/proxy/linux"))

def post_install_wintun(dep: Dependency, dest_dir: Path):
    # Agent - Wintun
    safe_move_files(f"wintun-{dep.version}.zip", dest_dir, Path(f"{dest_dir}/agent/wintun"))
    unzip_files(Path(f"{dest_dir}/agent/wintun"))
    wintunAgentDir = Path(f"{dest_dir}/agent/wintun/wintun-{dep.version}")
    safe_move_files("wintun", wintunAgentDir, Path(f"{dest_dir}/agent/wintun"))
    Path.rmdir(wintunAgentDir)

###############################################################################
# DEPENDENCY DEFINITIONS
###############################################################################
DEPENDENCIES = [
    Dependency(
        name="sharphound",
        version="master",
        urls=[
            "https://raw.githubusercontent.com/BloodHoundAD/BloodHound/{version}/Collectors/SharpHound.ps1",
            "https://raw.githubusercontent.com/BloodHoundAD/BloodHound/{version}/Collectors/SharpHound.exe",
        ],
        directory=Path("bloodhound"),
    ),
    Dependency(
        name="mimikatz",
        version="2.2.0-20220919",
        urls=[
            "https://github.com/gentilkiwi/mimikatz/releases/download/{version}/mimikatz_trunk.zip",
            "https://raw.githubusercontent.com/pluggero/Invoke-Mimikatz/main/Invoke-Mimikatz.ps1",
        ],
        directory=Path("mimikatz"),
        post_download_function=post_install_mimikatz
    ),
    Dependency(
        name="sysinternals",
        version="",
        urls=[
            "https://download.sysinternals.com/files/SysinternalsSuite.zip",
        ],
        directory=Path("sysinternals"),
        post_download_function=post_install_sysinternals
    ),
    Dependency(
        name="rubeus",
        version="",
        urls=[
            "https://raw.githubusercontent.com/r3motecontrol/Ghostpack-CompiledBinaries/master/Rubeus.exe",
        ],
        directory=Path("ghostpack"),
    ),
    Dependency(
        name="pspy",
        version="1.2.1",
        urls=[
            "https://github.com/DominicBreuker/pspy/releases/download/v{version}/pspy64",
        ],
        directory=Path("pspy"),
    ),
    Dependency(
        name="linpeas",
        version="20240324-2c3cd766",
        urls=[
            "https://github.com/carlospolop/PEASS-ng/releases/download/{version}/linpeas.sh",
        ],
        directory=Path("linpeas"),
    ),
    Dependency(
        name="winpeas",
        version="20250113-4426d62e",
        urls=[
            "https://github.com/carlospolop/PEASS-ng/releases/download/{version}/winPEAS.bat",
            "https://github.com/carlospolop/PEASS-ng/releases/download/{version}/winPEASx64.exe",
        ],
        directory=Path("winpeas"),
    ),
    Dependency(
        name="chisel",
        version="1.9.1",
        urls=[
            "https://github.com/jpillora/chisel/releases/download/v{version}/chisel_{version}_windows_amd64.gz",
            "https://github.com/jpillora/chisel/releases/download/v{version}/chisel_{version}_linux_amd64.gz",
        ],
        directory=Path("chisel"),
        post_download_function=post_install_chisel
    ),
    Dependency(
        name="ligolo-ng",
        version="0.6.2",
        urls=[
            "https://github.com/nicocha30/ligolo-ng/releases/download/v{version}/ligolo-ng_agent_{version}_windows_amd64.zip",
            "https://github.com/nicocha30/ligolo-ng/releases/download/v{version}/ligolo-ng_proxy_{version}_linux_amd64.tar.gz",
        ],
        directory=Path("ligolo-ng"),
        post_download_function=post_install_ligolo
    ),
    Dependency(
        name="wintun",
        version="0.14.1",
        urls=[
            "https://www.wintun.net/builds/wintun-{version}.zip",
        ],
        directory=Path("ligolo-ng"),
        post_download_function=post_install_wintun
    ),
    Dependency(
        name="printspoofer",
        version="1.0",
        urls=[
            "https://github.com/itm4n/PrintSpoofer/releases/download/v{version}/PrintSpoofer64.exe",
            "https://github.com/itm4n/PrintSpoofer/releases/download/v{version}/PrintSpoofer32.exe",
        ],
        directory=Path("printspoofer"),
    ),
    Dependency(
        name="godpotato",
        version="1.20",
        urls=[
            "https://github.com/BeichenDream/GodPotato/releases/download/V{version}/GodPotato-NET4.exe",
        ],
        directory=Path("godpotato"),
    ),
    Dependency(
        name="uacbypass",
        version="46d9eb3ecf8b655aad9f006559f4362c9da49b95",
        urls=[
            "https://raw.githubusercontent.com/CsEnox/EventViewer-UACBypass/{version}/Invoke-EventViewer.ps1",
        ],
        directory=Path("uacbypass"),
    ),
]

###############################################################################
# MAIN
###############################################################################
def main() -> int:
    # 1) Prepare the tools directory
    safe_mkdir(TOOLS_DIR)
    clean_dir(TOOLS_DIR)

    # 2) Download and setup all dependencies
    for dep in DEPENDENCIES:
        install_dir = TOOLS_DIR / dep.directory
        safe_mkdir(install_dir)
        dep.download(install_dir)
        dep.post_download(install_dir)

    logging.info("Setup completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

