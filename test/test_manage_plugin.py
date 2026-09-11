from pathlib import Path
from thonny.shell import ToplevelCommand
from thonnycontrib.thonny_astro_pi_replay import load_config, save_config, open_manage_astro_pi_replay
from tkinter import ttk
from unittest.mock import patch
import logging
import subprocess
import sys
import tkinter as tk

import pytest

from conftest import ThonnyMocks
from utils import get_test_resource

logger = logging.getLogger(__name__)

class TestManagePluginLogic:

    def test_load_config_sets_default_photography_type(
        self
    ) -> None:
        assert load_config()["photography_type"] == "VIS"

    def test_load_config_corrupted_json_default_photography_type(
        self, mock_config_filepath: Path
    ) -> None:
        mock_config_filepath.write_text("Not json!")

        assert load_config()["photography_type"] == "VIS"

    @pytest.mark.parametrize("photography_type", [
        ("VIS"),
        ("IR"),
    ])
    def test_set_config_calls_replay_tool_CLI(
        self, photography_type: str, thonny_mocks: ThonnyMocks
    ) -> None:
        # when
        save_config(photography_type)

        # then
        script_output = thonny_mocks.generated_script
        assert isinstance(script_output, str)
        assert script_output.strip() == get_test_resource(
            f"expected_generated_script_{photography_type}.txt"
        ).read_text().strip()
        thonny_mocks.runner.send_command.assert_called_once_with(
            ToplevelCommand("execute_source",
                            source=script_output)
        )

def patch_run_replay(args: list[str]):
    subprocess.run([
        sys.executable, "-m", "astro_pi_replay.main"
    ] + args, check=True, text=True)

class TestManagePluginUI:

    @pytest.fixture
    def tk_root(self, monkeypatch):
        root = tk.Tk()
        ui_mode = False
        if ui_mode:
            root.geometry("500x500+0+0")
        else:
            root.withdraw()
        monkeypatch.setattr(
            "thonnycontrib.thonny_astro_pi_replay.get_workbench",
            lambda: root
        )
        yield root
        root.destroy()

    @patch("thonnycontrib.thonny_astro_pi_replay.run_replay", side_effect=patch_run_replay)
    def test_ui_interactivity(
        self, mock_run_replay, tk_root
    ) -> None:

        # WHEN
        open_manage_astro_pi_replay()

        # THEN
        assert len(tk_root.children) == 1
        assert "!toplevel" in tk_root.children
        top_level = tk_root.children.get("!toplevel")
        assert len(top_level.children) == 1
        assert "!frame" in top_level.children
        frame = top_level.children["!frame"]
        assert len(frame.children) == 3

        assert "!label" in frame.children
        label = frame.children["!label"]
        assert isinstance(label, ttk.Label)
        assert label.cget("text") == \
            "Select the photography type for the Astro Pi Replay tool."

        assert "!combobox" in frame.children
        combobox = frame.children["!combobox"]
        assert isinstance(combobox, ttk.Combobox)

        assert "!button" in frame.children
        button = frame.children["!button"]
        assert isinstance(button, ttk.Button)
        assert button.cget("text") == "Save"

        # Verify initial value loaded from config
        assert combobox.get() == "VIS"

        # Simulate user selection and clicking Save
        combobox.set("IR")
        logger.debug("Invoking")
        button.invoke()
        logger.debug("invoked")

        # Verify saved state on disk
        logger.debug("Loading")
        updated_config = load_config()
        assert updated_config["photography_type"] == "IR"

