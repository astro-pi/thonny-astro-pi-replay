from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Any, Iterable, Optional
from unittest.mock import patch, MagicMock
import logging
import os

from thonnycontrib.thonny_astro_pi_replay import generate_script

from astro_pi_replay.configuration import CONFIG_FILE_NAME, CONFIG_FILE_ENV_VAR
import pytest


logger = logging.getLogger(__name__)

@dataclass
class ThonnyMocks:
    runner: MagicMock
    get_runner: MagicMock
    generate_script: MagicMock
    get_workbench: MagicMock
    generated_script: Optional[str] = None

@pytest.fixture(autouse=True)
def mock_config_filepath(tmp_path: Path) -> Generator[Path, Any, Any]:
    test_config_path: Path = tmp_path / CONFIG_FILE_NAME
    with patch("astro_pi_replay.configuration.CONFIG_FILE", test_config_path):
        yield test_config_path


@pytest.fixture(autouse=True)
def set_config_dir(mock_config_filepath) -> Iterable:
    """
    Sets/unsets the CONFIG_FILE_ENV_VAR before and
    after each test
    """
    logger.debug(f"Setting {CONFIG_FILE_ENV_VAR} to {mock_config_filepath}")
    os.environ[CONFIG_FILE_ENV_VAR] = str(mock_config_filepath)

    yield
    logger.debug(f"Unsetting {CONFIG_FILE_ENV_VAR}")
    os.environ.pop(str(CONFIG_FILE_ENV_VAR), None)


@pytest.fixture
def thonny_mocks() -> Generator[ThonnyMocks, Any, Any]:

    mocks: Optional[ThonnyMocks] = None

    def call_real_generate_script(args):
        logging.debug("Generated")
        generated = generate_script(args)
        if mocks:
            mocks.generated_script = generated
        return generated

    with patch("thonnycontrib.thonny_astro_pi_replay.get_runner", autospec=True) as mock_get_runner, \
            patch("thonnycontrib.thonny_astro_pi_replay.generate_script", side_effect=call_real_generate_script) as mock_generate_script, \
        patch("thonnycontrib.thonny_astro_pi_replay.get_workbench", autospec=True) as mock_get_workbench, \
        patch("thonnycontrib.thonny_astro_pi_replay.sys.path", ["MOCK_PATH"]):

        mocks = ThonnyMocks(
            mock_get_runner.return_value,
            mock_get_runner,
            mock_generate_script,
            mock_get_workbench
        )
        yield mocks

