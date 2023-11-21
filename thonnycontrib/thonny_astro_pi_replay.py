import logging
from pathlib import Path
from tkinter.messagebox import showinfo

from thonny import get_runner, get_shell, get_workbench

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


def astro_pi_replay():
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
        handler=astro_pi_replay,
        caption=CAPTION,
    )
