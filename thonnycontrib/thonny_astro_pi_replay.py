from json.decoder import JSONDecodeError
from pathlib import Path
from tkinter import ttk
from tkinter.messagebox import showinfo
from typing import Any
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import tkinter as tk

from astro_pi_replay.configuration import get_config_file_path
from thonny import get_workbench, THONNY_USER_DIR
from thonny.shell import ToplevelCommand, get_runner


CURRENT_DIR = Path(__file__).parent
ICON_DIR = CURRENT_DIR / "res"
PLUGIN_NAME: str = Path(__file__).name
PROGRAM_NAME: str = "Astro-Pi-Replay"

# To be translated
SAVE_FIRST_WINDOW_NAME: str = "Please save"
SAVE_FIRST_MESSAGE: str = (
    "Please save your file before running it " + f"with {PROGRAM_NAME}"
)
NO_EXECUTABLE_DETECTED_MESSAGE: str = "Don't know how to locate Python venv executable"
CAPTION: str = "Run the current file with Astro-Pi-Replay"

logger = logging.getLogger("thonny_astro_pi_replay")

def setup_logger():
    logger.setLevel(logging.DEBUG)
    log_path = os.path.join(THONNY_USER_DIR, "astro_pi_plugin.log")
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 2**20, # 5 MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

def get_project_directory():
    workbench = get_workbench()

    editor = workbench.get_editor_notebook().get_current_editor()
    if editor:
        filename = editor.get_filename()
        if filename:
            return os.path.dirname(filename)

    cwd = workbench.get_local_cwd()
    if cwd and cwd != "/":
        return cwd

    return os.path.expanduser("~")

def generate_script(args: list[str]) -> str:
    frontend_paths = sys.path
    joined_frontend_paths = os.pathsep.join(frontend_paths)

    merged_args: list[str] = [
        "Astro-Pi-Replay",
    ] + args
    workdir = get_project_directory()

    logger.debug(f"frontend_paths: {frontend_paths}")
    logger.debug(f"merged_args: {merged_args}")
    logger.debug(f"workdir: {workdir}")

    return f"""
import sys
import os

sys.path.extend({repr(frontend_paths)})

from astro_pi_replay.main import main

existing_pythonpath = os.environ.get("PYTHONPATH", "")

# Setup the environment
if existing_pythonpath:
    os.environ["PYTHONPATH"] = f"{joined_frontend_paths}{os.pathsep}{{existing_pythonpath}}"
else:
    os.environ["PYTHONPATH"] = "{joined_frontend_paths}"
os.environ["FORCE_COLOR"] = "1"

# Mock the command line arguments
sys.argv = {merged_args}

os.chdir({repr(workdir)})

try:
    main()
except SystemExit as e:
    if str(e) != "0":
        print(f"\\nExited with code: {{e}}", file=sys.stderr)
"""



def run_replay(args: list[str]):
    workbench = get_workbench()
    if not workbench.get_option("shell.terminal_emulation"):
        print("Note: Enable 'Terminal emulation' in Tools -> Options -> Shell for colors.")

    runner = get_runner()
    if not runner:
        return

    script = generate_script(args)
    logger.debug(f"script: {script}")

    # Dispatch in-memory execution request directly
    cmd = ToplevelCommand("execute_source", source=script)
    runner.send_command(cmd)


def load_config() -> dict[str,Any]:
    logger.debug("Loading config")
    config: dict[str,Any] = {
        "photography_type": "VIS"
    }
    config_path = get_config_file_path()

    try:
        config |= json.loads(config_path.read_text())
    except (JSONDecodeError, FileNotFoundError, IOError):
        pass
    return config


def save_config(photography_type: str) -> None:
    run_replay([
        "configure", "--photography-type", photography_type
    ])


def open_manage_astro_pi_replay():
    """Handler for the Tools > Manage Astro Pi Replay menu item."""
    config = load_config()
    current_type: str = config["photography_type"]

    # Open window
    workbench = get_workbench()
    window = tk.Toplevel(workbench)
    window.title("Manage Astro Pi Replay")

    window.transient(workbench)
    window.resizable(False, False)

    # main_frame = ttk.Frame(window, padding="15 15 15 15")
    main_frame = ttk.Frame(window, padding="15")
    main_frame.pack(fill="both", expand=True)

    # Description
    desc_text = "Select the photography type for the Astro Pi Replay tool."
    desc_label = ttk.Label(
            main_frame, text=desc_text, wraplength=260,
            justify="center")
    desc_label.pack(pady=10, padx=10)

    # Dropdown between IR and VIS
    selected_type = tk.StringVar(value=current_type)
    dropdown = ttk.Combobox(
        main_frame,
        textvariable=selected_type,
        values=("VIS", "IR"),
        state="readonly"
    )
    dropdown.pack(pady=5)

    def do_save_and_close():
        save_config(str(selected_type.get()))
        window.destroy()

    # Save button
    save_button = ttk.Button(main_frame, text="Save", command=do_save_and_close)
    save_button.pack(pady=15)


def run_with_astro_pi_replay():
    """
    Executes the current file with the Astro-Pi-Replay tool.
    Requires the current file to be saved.
    """
    logger.debug(f"{PLUGIN_NAME} called")

    editor = get_workbench().get_editor_notebook().get_current_editor()
    if not editor:
        logger.debug(f"editor: {str(editor)}")
        return

    if not (filename := editor.get_filename()) or editor.is_modified():
        showinfo(SAVE_FIRST_WINDOW_NAME, SAVE_FIRST_MESSAGE)
        return
    logger.debug(f"filename: {filename}")
    run_replay(["run", filename])


def load_plugin():
    setup_logger()

    logger.debug(f"Loading plugin {PROGRAM_NAME}...")
    get_workbench().add_command(
        command_id="astro_pi_replay",
        menu_name="run",
        command_label=PROGRAM_NAME,
        handler=run_with_astro_pi_replay,
        caption=CAPTION,
    )
    get_workbench().add_command(
        command_id="manage_astro_pi_replay",
        menu_name="tools",
        command_label="Manage Astro Pi Replay plugin",
        handler=open_manage_astro_pi_replay,
        caption="Configure Astro Pi Replay settings"
    )

