import logging
from typing import Optional

from enums.owasp_llm import OwaspLLM

logger = logging.getLogger(__name__)


class Attack:
    def __init__(self, name: str, description: str, prompt: str, expected_outputs: list, severity: int,
                 use_ai_if_bad_output: bool = False, use_ai_if_inconclusive_output: bool = False):
        self.name: str = name
        self.description: str = description
        self.prompt: str = prompt
        self.expected_outputs: list[str] = expected_outputs
        self.severity: int = severity

        # If the output contains known strings indicating the chatbot actively refused to answer, use AI to generate
        # a follow-up prompt
        self.use_ai_if_bad_output: bool = use_ai_if_bad_output

        # If the output is inconclusive (e.g. "I'm not sure" or "I don't know" or we didn't find bad output),
        # use AI to generate a follow-up prompt
        self.use_ai_if_inconclusive_output: bool = use_ai_if_inconclusive_output

    @staticmethod
    def from_yaml(yaml_data: dict) -> 'Attack':
        return Attack(
            name=yaml_data["name"],
            description=yaml_data["description"],
            prompt=yaml_data["prompt"],
            expected_outputs=yaml_data["expected_outputs"],
            severity=yaml_data["severity"],
            use_ai_if_bad_output=yaml_data.get("use_ai_if_bad_output", False),
            use_ai_if_inconclusive_output=yaml_data.get("use_ai_if_inconclusive_output", False)
        )


class AttackCategory:
    def __init__(self, name: str, description: str, category: OwaspLLM, attacks: list[Attack]):
        self.name = name
        self.description = description
        self.category = category
        self.attacks = attacks

    @staticmethod
    def from_yaml(yaml_data: dict) -> Optional['AttackCategory']:
        attacks = [Attack.from_yaml(attack) for attack in yaml_data.get("attacks", [])]

        if not OwaspLLM.get_category_by_name(yaml_data["category"]):
            logger.error(f"Invalid OWASP category: {yaml_data['category']}")
            return None

        return AttackCategory(
            name=yaml_data["name"],
            description=yaml_data["description"],
            category=OwaspLLM.get_category_by_name(yaml_data["category"]),
            attacks=attacks
        )
