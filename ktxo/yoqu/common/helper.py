#
# Bunch of helper function
#
import json
from datetime import datetime
import logging
import os
import psutil
import re
from typing import Any
import uuid


logger = logging.getLogger("ktxo.yoqu")


def build_filename(filename: str,
                   folder: str = None,
                   unique: bool = False,
                   add_timestamp: bool = False,
                   override: bool = False):
    filename_, fileext_ = os.path.splitext(filename)
    if unique:
        filename_ += f"_{str(uuid.uuid4())}"
    if add_timestamp:
        filename_ += f"_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    filename_ = f"{filename_}{fileext_}"
    if folder:
        filename_ = os.path.join(folder, filename_)

    i = 1
    filename_aux = filename_
    if not override:
        while os.path.exists(filename_aux):
            filename_aux = filename_.replace(fileext_, f"-{i:02d}{fileext_}")
            i += 1
        filename_ = filename_aux
    return os.path.abspath(filename_)


def normalize_url(url):
    return re.sub(":|/|&|%|\.|\?", "_", url)


def build_folders(*folder: str):
    folder = os.path.abspath(os.path.join(*folder))
    if os.path.exists(folder):
        return folder
    try:
        os.makedirs(folder, exist_ok=True)
        return folder
    except Exception as e:
        return None


def write_json(data: dict, filename: str, folder: str = None, unique: bool = False, add_timestamp: bool = False):
    filename = build_filename(filename, folder, unique, add_timestamp, False)
    with open(filename, "w", encoding="utf-8") as fd:
        json.dump(data, fd, indent=4, ensure_ascii=False, default=str)
    return filename


def write_binary(data: Any, filename: str, folder: str = None, unique: bool = False, add_timestamp: bool = False):
    filename = build_filename(filename, folder, unique, add_timestamp, False)
    with open(filename, "wb") as fd:
        fd.write(data)
    return filename


class ProcessHelper():
    @staticmethod
    def start_process(command: list[str] | str) -> int:
        if isinstance(command, str):
            command = command.split()
        logger.debug(f"Starting process with '{command}'")
        return psutil.Popen(command).pid

    @staticmethod
    def get_process(command: list[str] | str) -> psutil.Process:
        command_line = command
        if isinstance(command, str):
            command_line = [c.strip() for c in command.split()]
        for process_ in psutil.process_iter():
            if process_.cmdline() == command_line:
                return process_
        return None

    @staticmethod
    def process_exist(command: list[str] | str, pid:int) -> int:
        command_line = command
        if isinstance(command, str):
            command_line = [c.strip() for c in command.split()]
        try:
            logger.debug(f"Checking '{' '.join(command_line)}'")
            processes = psutil.process_iter()
            process = None
            for process_ in processes:
                try:
                    if process_.pid == pid and process_.status() == psutil.STATUS_ZOMBIE:
                        logger.warning(f"Process pid={process_.pid} zombie, waiting 1 sec, rc={process_.wait(1)}")
                    if process_.cmdline() == command_line:
                        process = process_
                        break
                except psutil.NoSuchProcess:
                    try:
                        logger.warning(f"Process pid={process_.pid} zombie, waiting 1 sec, rc={process_.wait(1)}")
                    except:
                        pass
            if process is None:
                return -1

            if process.status() == psutil.STATUS_ZOMBIE:
                logger.warning(f"Process pid={process.pid} zombie, waiting 1 sec")
                process.wait(1)
                return -1
            logger.debug(f"Process pid={process.pid} {process.status()}")
            return process.pid
        except psutil.NoSuchProcess as nsp:
            logger.error(nsp)
            return -1
        except Exception as e:
            logger.error(e)
            return -1

