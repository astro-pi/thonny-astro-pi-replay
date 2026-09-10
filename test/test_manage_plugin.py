from pathlib import Path
from thonnycontrib.thonny_astro_pi_replay import load_config, save_config, open_manage_astro_pi_replay
from tkinter import ttk
from unittest.mock import patch
import tkinter as tk
import time

import pytest


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
        self, photography_type: str
    ) -> None:
        with patch("thonnycontrib.thonny_astro_pi_replay.subprocess") as mock_subprocess:
            mock_subprocess.run.return_value = None
            save_config(photography_type)

            mock_subprocess.run.assert_called_once_with(
                [
                    "Astro-Pi-Replay",
                    "configure",
                    "--photography-type", photography_type
                ],
                check=True
            )


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

    def test_ui_interactivity(self, tk_root):

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
            "Select the photography type for the Astro Pi Replay."

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
        print("Invoking")
        button.invoke()
        print("invoked")

        # Verify saved state on disk
        print("Loading")
        updated_config = load_config()
        assert updated_config["photography_type"] == "IR"

