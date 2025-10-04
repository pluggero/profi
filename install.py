#!/usr/bin/env python3
"""
Setup script for installing dependencies for profi.
"""

import glob
import gzip
import logging
import os
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Union

import requests

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
    filename = url.split("/")[-1]
    dest_file = dest_dir / filename

    if dest_file.exists():
        logging.info(f"Skipping {filename} (already downloaded).")
        return

    logging.info(f"Downloading {filename} from {url}")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_file, "wb") as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        logging.info(f"Downloaded {filename} successfully.")
    except requests.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        if dest_file.exists():
            dest_file.unlink()
        raise


def zip_path(
    source: Path,
    destination: Path,
    compression: int = zipfile.ZIP_DEFLATED,
    flatten_root: bool = False,
) -> None:
    """
    Zips either a single file or a directory (recursively) into the specified
    destination archive, using the given compression method.

    :param source:       Path to a file or directory to zip.
    :param destination:  Path to the resulting archive (e.g. 'archive.zip').
    :param compression:  A zipfile compression constant (default ZIP_DEFLATED).
                         Other valid constants include ZIP_STORED, ZIP_BZIP2,
                         ZIP_LZMA (availability varies by Python version).
    :param flatten_root:  If True and 'source' is a directory, the files inside
                          'source' will appear at the top level of the zip
                          (i.e., the source folder name is not included).
                          If False, the source folder's name is included.
    """
    if not source.exists():
        logging.error(f"Source '{source}' does not exist.")
        return

    # Create parent directories for destination if necessary
    safe_mkdir(destination.parent)

    try:
        with zipfile.ZipFile(destination, mode="w", compression=compression) as zf:
            # If it's just a single file, zip it with its base name as arcname
            if source.is_file():
                logging.info(f"Zipping file '{source}' to '{destination}'.")
                zf.write(source, arcname=source.name)
            else:
                # It's a directory; zip all files inside (recursive)
                logging.info(f"Zipping directory '{source}' to '{destination}'.")

                # Use rglob('*') to find all files/folders under `source`
                for item in source.rglob("*"):
                    # Only add files, not directories (zipfile can handle dirs,
                    # but typically we skip empty folders to avoid empty entries).
                    if item.is_file():
                        # Determine arcname depending on whether we flatten the root directory
                        if flatten_root:
                            # Store files relative to 'source'
                            # Example: If item is /path/Release/sub/file.txt, arcname becomes sub/file.txt
                            arcname = item.relative_to(source)
                        else:
                            # Preserve the top directory name
                            # Example: arcname is Release/sub/file.txt
                            arcname = item.relative_to(source.parent)
                        zf.write(item, arcname=arcname)

    except Exception as e:
        logging.exception(f"An error occurred while zipping '{source}': {e}")
        raise


def unzip_files(directory: Path, create_subfolder: bool = True) -> None:
    """
    Unzip all *.zip files in the specified directory.

    If create_subfolders is True, each .zip file is extracted
    into a subfolder named after the file (minus the .zip extension).
    If create_subfolders is False, the contents are extracted
    directly into the directory.

    After a file is successfully unzipped, the original .zip
    is deleted.

    :param directory:        Path object pointing to the directory
                             containing .zip files
    :param create_subfolders: If True (default), each .zip is extracted
                             into its own subfolder. If False, the .zip
                             is extracted directly into `directory`.
    """
    if not directory.is_dir():
        logging.error(f"Directory {directory} does not exist.")
        return

    zip_files = list(directory.glob("*.zip"))
    if not zip_files:
        logging.debug(f"No zip files found in {directory}")
        return

    for zip_file in zip_files:
        try:
            if create_subfolder:
                # Create a subfolder matching the zip file name
                target_dir = directory / zip_file.stem
                target_dir.mkdir(parents=True, exist_ok=True)
            else:
                # Extract the contents directly into the directory
                target_dir = directory

            logging.info(f"Unzipping {zip_file.name} into {target_dir}")

            with zipfile.ZipFile(zip_file, "r") as zf:
                zf.extractall(target_dir)

            # Remove the .zip file after successful extraction
            zip_file.unlink()
            logging.debug(f"Removed zip file '{zip_file.name}' after extraction.")

        except Exception as e:
            logging.error(f"Failed to unzip {zip_file.name}: {e}")
            raise


def gunzip_files(directory: Path) -> None:
    """
    Gunzip all .gz files in the directory to a file with the same
    name minus .gz. Then remove the .gz file.
    """
    for gz_file in directory.glob("*.gz"):
        target_path = directory / gz_file.stem
        logging.info(f"Decompressing {gz_file.name} to {target_path.name}")
        with gzip.open(gz_file, "rb") as f_in:
            with open(target_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        gz_file.unlink()


def untar_files(directory: Path) -> None:
    """
    Untar all .tar files in the directory, extracting them in place,
    then remove the tar file.
    """
    for tar_file in directory.glob("*.tar"):
        logging.info(f"Extracting {tar_file.name}")
        with tarfile.open(tar_file, "r") as t:
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
        post_download_function=None,
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
def post_install_sharphound(dep: Dependency, dest_dir: Path):
    unzip_files(dest_dir, create_subfolder=False)

def post_install_mimikatz(dep: Dependency, dest_dir: Path):
    unzip_files(dest_dir, create_subfolder=False)


def post_install_sysinternals(dep: Dependency, dest_dir: Path):
    unzip_files(dest_dir, create_subfolder=False)


def post_install_chisel(dep: Dependency, dest_dir: Path):
    gunzip_files(dest_dir)


def post_install_ligolo(dep: Dependency, dest_dir: Path):
    # Agent - Windows
    safe_move_files(
        "ligolo-ng_agent_*_windows_amd64.zip",
        dest_dir,
        Path(f"{dest_dir}/agent/windows"),
    )
    unzip_files(Path(f"{dest_dir}/agent/windows"))
    windowsAgentDir = Path(
        f"{dest_dir}/agent/windows/ligolo-ng_agent_{dep.version}_windows_amd64"
    )
    safe_move_files("*", windowsAgentDir, Path(f"{dest_dir}/agent/windows"))
    Path.rmdir(windowsAgentDir)

    # Proxy - Linux
    safe_move_files(
        "ligolo-ng_proxy_*_linux_amd64.tar.gz",
        dest_dir,
        Path(f"{dest_dir}/proxy/linux"),
    )
    gunzip_files(Path(f"{dest_dir}/proxy/linux"))
    untar_files(Path(f"{dest_dir}/proxy/linux"))


def post_install_wintun(dep: Dependency, dest_dir: Path):
    # Agent - Wintun
    safe_move_files(
        f"wintun-{dep.version}.zip", dest_dir, Path(f"{dest_dir}/agent/wintun")
    )
    unzip_files(Path(f"{dest_dir}/agent/wintun"))
    wintunAgentDir = Path(f"{dest_dir}/agent/wintun/wintun-{dep.version}")
    safe_move_files("wintun", wintunAgentDir, Path(f"{dest_dir}/agent/wintun"))
    Path.rmdir(wintunAgentDir)


def post_install_ysoserial_net(dep: Dependency, dest_dir: Path):
    unzip_files(dest_dir, create_subfolder=False)
    release_dir = Path(f"{dest_dir}/Release")
    zip_path(release_dir, Path(f"{release_dir}.zip"), flatten_root=True)
    shutil.rmtree(release_dir)


def post_install_pingcastle(dep: Dependency, dest_dir: Path):
    unzip_files(dest_dir, create_subfolder=False)


###############################################################################
# DEPENDENCY DEFINITIONS
###############################################################################
DEPENDENCIES = [
    Dependency(
        name="sharphound",
        version="2.7.2",
        urls=[
            "https://github.com/SpecterOps/SharpHound/releases/download/v{version}/SharpHound_v{version}_windows_x86.zip"
        ],
        directory=Path("bloodhound"),
        post_download_function=post_install_sharphound,
    ),
    Dependency(
        name="mimikatz",
        version="2.2.0-20220919",
        urls=[
            "https://github.com/gentilkiwi/mimikatz/releases/download/{version}/mimikatz_trunk.zip",
            "https://raw.githubusercontent.com/pluggero/Invoke-Mimikatz/main/Invoke-Mimikatz.ps1",
        ],
        directory=Path("mimikatz"),
        post_download_function=post_install_mimikatz,
    ),
    Dependency(
        name="sysinternals",
        version="",
        urls=[
            "https://download.sysinternals.com/files/SysinternalsSuite.zip",
        ],
        directory=Path("sysinternals"),
        post_download_function=post_install_sysinternals,
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
        version="20251004-69861b97",
        urls=[
            "https://github.com/peass-ng/PEASS-ng/releases/download/{version}/linpeas.sh",
        ],
        directory=Path("linpeas"),
    ),
    Dependency(
        name="winpeas",
        version="20251004-69861b97",
        urls=[
            "https://github.com/peass-ng/PEASS-ng/releases/download/{version}/winPEAS.bat",
            "https://github.com/peass-ng/PEASS-ng/releases/download/{version}/winPEASx64.exe",
        ],
        directory=Path("winpeas"),
    ),
    Dependency(
        name="chisel",
        version="1.10.1",
        urls=[
            "https://github.com/jpillora/chisel/releases/download/v{version}/chisel_{version}_windows_amd64.gz",
            "https://github.com/jpillora/chisel/releases/download/v{version}/chisel_{version}_linux_amd64.gz",
        ],
        directory=Path("chisel"),
        post_download_function=post_install_chisel,
    ),
    Dependency(
        name="ligolo-ng",
        version="0.8.2",
        urls=[
            "https://github.com/nicocha30/ligolo-ng/releases/download/v{version}/ligolo-ng_agent_{version}_windows_amd64.zip",
            "https://github.com/nicocha30/ligolo-ng/releases/download/v{version}/ligolo-ng_proxy_{version}_linux_amd64.tar.gz",
        ],
        directory=Path("ligolo-ng"),
        post_download_function=post_install_ligolo,
    ),
    Dependency(
        name="wintun",
        version="0.14.1",
        urls=[
            "https://www.wintun.net/builds/wintun-{version}.zip",
        ],
        directory=Path("ligolo-ng"),
        post_download_function=post_install_wintun,
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
    Dependency(
        name="ysoserial-net",
        version="1.36",
        urls=[
            "https://github.com/pwntester/ysoserial.net/releases/download/v{version}/ysoserial-1dba9c4416ba6e79b6b262b758fa75e2ee9008e9.zip",
        ],
        directory=Path("ysoserial-net"),
        post_download_function=post_install_ysoserial_net,
    ),
    Dependency(
        name="pingcastle",
        version="3.4.1.38",
        urls=[
            "https://github.com/netwrix/pingcastle/releases/download/{version}/PingCastle_{version}.zip",
        ],
        directory=Path("pingcastle"),
        post_download_function=post_install_pingcastle,
    ),
]


###############################################################################
# MAIN
###############################################################################
def main() -> int:
    errors: list[str] = []

    # 1) Prepare the tools directory
    safe_mkdir(TOOLS_DIR)
    clean_dir(TOOLS_DIR)

    # 2) Download and setup all dependencies
    for dep in DEPENDENCIES:
        install_dir = TOOLS_DIR / dep.directory
        safe_mkdir(install_dir)
        try:
            dep.download(install_dir)
            dep.post_download(install_dir)
        except Exception as e:
            errors.append(f"{dep.name}: {e}")

    if errors:
        for msg in errors:
            logging.error(msg)
        logging.error("Setup failed due to errors.")
        return 1

    logging.info("Setup completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
