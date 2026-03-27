import os
import pytest


@pytest.fixture(autouse=True)
def clean_settings():
    """Reset global settings singleton between tests."""
    import bctone.config as config_module
    config_module.settings = None
    yield
    config_module.settings = None
