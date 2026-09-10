from json.decoder import JSONDecodeError
from pathlib import Path
from tkinter import ttk
from tkinter.messagebox import showinfo
from typing import Any
import json
import logging
import subprocess
import tkinter as tk

from thonny import get_runner, get_shell, get_workbench

from astro_pi_replay.configuration import get_config_file_path

logger = logging.getLogger(__name__)


PLUGIN_NAME: str = Path(__file__).name
PROGRAM_NAME: str = "Astro-Pi-Replay"

# To be translated
SAVE_FIRST_WINDOW_NAME: str = "Please save"
SAVE_FIRST_MESSAGE: str = (
    "Please save your file before running it " + f"with {PROGRAM_NAME}"
)
NO_EXECUTABLE_DETECTED_MESSAGE: str = "Don't know how to locate Python venv executable"
CAPTION: str = "Run the current file with Astro-Pi-Replay"

def load_config() -> dict[str,Any]:
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
    args = [
        "Astro-Pi-Replay", "configure",
        "--photography-type", photography_type
    ]
    args_string = " ".join(args)
    logger.debug(f"Executing '{args_string}'")

    subprocess.run(args, check=True)


def open_manage_astro_pi_replay():
    """Handler for the Tools > Manage Astro Pi Replay menu item."""
    config = load_config()
    current_type: str = config["photography_type"]

    # Open window
    window = tk.Toplevel(get_workbench())
    window.title("Manage Astro Pi Replay")

    main_frame = ttk.Frame(window, padding="15 15 15 15")
    main_frame.pack(fill="both", expand=True)

    # Description
    desc_text = "Select the photography type for the Astro Pi Replay."
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

    executor: str = PROGRAM_NAME
    if get_runner().using_venv():
        logger.debug("Detected venv")
        proxy = get_runner().get_backend_proxy()
        executable = proxy.get_target_executable()
        if executable is None:
            raise RuntimeError(NO_EXECUTABLE_DETECTED_MESSAGE)
        executor_path = Path(executable).parent / executor
        logger.debug(f"executor_path: {str(executor_path)}")
        if not executor_path.exists():
            raise RuntimeError(f"Cannot find {executor} in venv")
        executor = str(executor_path)

    command: str = f'!"{executor}" run "{filename}"'
    logger.debug(f"Executing {command}")
    get_shell().submit_magic_command(command)


def load_plugin():
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
        command_label="Manage Astro Pi Replay",
        handler=open_manage_astro_pi_replay,
        caption="Configure Astro Pi Replay settings"
    )

