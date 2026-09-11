from pathlib import Path

CURRENT_DIR = Path(__file__).parent

RESOURCES_DIR = CURRENT_DIR / "resources"

def get_test_resource(resource_name: str) -> Path:
    resource = RESOURCES_DIR / resource_name
    if not resource.exists():
        raise FileNotFoundError()
    return resource
