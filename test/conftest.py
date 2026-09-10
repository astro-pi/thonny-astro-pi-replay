from pathlib import Path
from unittest.mock import patch
import logging
from typing import Generator, Any, Iterable
import os

import pytest

from astro_pi_replay.configuration import CONFIG_FILE_NAME, CONFIG_FILE_ENV_VAR


logger = logging.getLogger(__name__)


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

