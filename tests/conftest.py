import pytest
import os
import json
from pathlib import Path

@pytest.fixture(scope="session")
def test_config():
    config_path = Path(__file__).parent / "config" / "test_config.json"
    with open(config_path) as f:
        return json.load(f)

@pytest.fixture(autouse=True)
def setup_test_env(test_config):
    # Set environment variables for testing
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["RABBITMQ_HOST"] = "localhost"
    os.environ["NEWS_API_KEY"] = test_config["news_api_key"]
    yield
