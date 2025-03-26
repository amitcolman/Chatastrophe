
from enum import Enum
from typing import Optional


class Severity(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    @staticmethod
    def get_all_severities() -> list[str]:
        return [severity.value for severity in Severity]

    @staticmethod
    def get_severity_by_name(name: str) -> Optional['Severity']:
        return next((severity for severity in Severity if severity.name == name), None)

    @staticmethod
    def get_severity_by_value(value: str) -> Optional['Severity']:
        return next((severity for severity in Severity if severity.value == value), None)

