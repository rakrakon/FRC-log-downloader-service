import os
import time
import shutil
from pathlib import Path
from loguru import logger
from git import Repo
import wmi


REPO_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # TODO: change
LOGS_DIR = REPO_PATH / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def commit_log(repo, log_file):
    try:
        repo.index.add([str(log_file)])
        repo.index.commit(f"Add log file: {log_file.name}")
        logger.info(f"Committed {log_file.name} to repository")
    except Exception as e:
        logger.info(f"Error committing {log_file.name}: {e}")


def get_file_signature(file_path):
    return file_path.name, file_path.stat().st_size


def is_file_downloaded(log_file):
    file_name = log_file.name
    file_size = log_file.stat().st_size

    for existing_file in LOGS_DIR.glob("*.wpilog"):
        if (existing_file.name == file_name and
                existing_file.stat().st_size == file_size):
            return True
    return False

def get_usb_drives():
    drives = set()
    c = wmi.WMI()

    for drive in c.Win32_LogicalDisk():
        if drive.DriveType == 2: # removable
            drives.add(Path(f"{drive.DeviceID}/"))

    return drives

def download_logs(drive_path, repo):
    try:
        for log_file in drive_path.glob("**/*.wpilog"):
            if not is_file_downloaded(log_file):
                dest_path = LOGS_DIR / log_file.name
                logger.info(f"Copying {log_file.name} ({log_file.stat().st_size} bytes)")
                shutil.copy2(log_file, dest_path)
                commit_log(repo, dest_path)
            else:
                logger.info(f"Skipping {log_file.name} - already exists")
    except Exception as e:
        logger.info(f"Error accessing {drive_path}: {e}")


def monitor_drives():
    logger.info(f"Monitoring for USB drives. Saving logs to {LOGS_DIR}")
    previous_drives = set()

    try:
        repo = Repo(REPO_PATH)
        logger.info("Git repository initialized")
    except Exception as e:
        logger.info(f"Error initializing git repository: {e}")
        return

    while True:
        current_drives = get_usb_drives()

        new_drives = current_drives - previous_drives
        for drive in new_drives:
            logger.info(f"New drive detected: {drive}")
            download_logs(drive, repo)

        previous_drives = current_drives
        time.sleep(1)


if __name__ == "__main__":
    logger.add("logfile.log")
    monitor_drives()