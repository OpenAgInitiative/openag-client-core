"""
Tests the dictionary abstraction of the persistent global configuration
"""
import tempfile

from openag_lib.config import Config

def test_config():
    with tempfile.NamedTemporaryFile() as f:
        config = Config(f.name)
        config["test"]["test"] = "test"
        assert config._data == {"test": {"test": "test"}}
        del config["test"]["test"]
        assert config._data == {}
        assert not config["test2"]
        assert list(config) == []
        config["test"] = "test"
        assert list(config) == ["test"]
        assert list(config.items()) == [("test", "test")]
