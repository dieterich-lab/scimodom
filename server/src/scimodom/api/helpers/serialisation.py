"""JSON serialisation of API responses."""

from decimal import Decimal
from typing import Any

from flask import Flask
from flask.json.provider import DefaultJSONProvider


class ScimodomJSONProvider(DefaultJSONProvider):
    """Flask JSON provider to write 'Decimal' as a JSON number."""

    @staticmethod
    def default(o: Any) -> Any:
        if isinstance(o, Decimal):
            return float(o)
        return DefaultJSONProvider.default(o)


def set_json_provider(app: Flask) -> None:
    """Set JSON provider."""
    app.json = ScimodomJSONProvider(app)
