from app.bootstrap.container import create_container
from tests.validation import VALIDATION_SETTINGS


def test_production_container_graph_is_valid() -> None:
    """Прод-граф собирается без конфликтов фабрик."""
    container = create_container(VALIDATION_SETTINGS)

    assert container is not None
