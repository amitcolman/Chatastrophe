import logging
from typing import Optional, List

from enums.owasp_llm import OwaspLLM
from enums.severity import Severity

logger = logging.getLogger(__name__)


class Attack:
    def __init__(self, name: str, description: str, prompt: str, expected_outputs: list, severity: Severity, category: str,
                 ai_analysis_prompt: Optional[str] = None, use_ai_if_bad_output: bool = False):
        self.name: str = name
        self.description: str = description
        self.prompt: str = prompt
        self.expected_outputs: list[str] = expected_outputs
        self.severity: Severity = severity
        self.category: str = category

        self.ai_analysis_prompt: Optional[str] = ai_analysis_prompt
        self.use_ai_if_bad_output: bool = use_ai_if_bad_output
        self.max_retries: int = 1

        # Run-time variables
        self.chatbot_output: List[str] = []
        self.alternative_prompt: Optional[str] = None
        self.retry_count: int = 0

    @staticmethod
    def from_yaml(yaml_data: dict, category: str) -> 'Attack':
        return Attack(
            name=yaml_data["name"],
            description=yaml_data["description"],
            prompt=yaml_data["prompt"],
            expected_outputs=yaml_data.get("expected_outputs", []),
            severity=Severity.get_severity_by_name(yaml_data["severity"]),
            category=category,
            ai_analysis_prompt=yaml_data.get("ai_analysis_prompt", None),
            use_ai_if_bad_output=yaml_data.get("use_ai_if_bad_output", False)
        )


class AttackCategory:
    def __init__(self, name: str, description: str, category: OwaspLLM, mitigations: list[str], attacks: list[Attack]):
        self.name = name
        self.description = description
        self.category = category
        self.mitigations = mitigations
        self.attacks = attacks

    @staticmethod
    def from_yaml(yaml_data: dict) -> Optional['AttackCategory']:
        attacks = [Attack.from_yaml(attack, yaml_data["name"]) for attack in yaml_data.get("attacks", [])]

        if not OwaspLLM.get_category_by_name(yaml_data["category"]):
            logger.error(f"Invalid OWASP category: {yaml_data['category']}")
            return None

        return AttackCategory(
            name=yaml_data["name"],
            description=yaml_data["description"],
            category=OwaspLLM.get_category_by_name(yaml_data["category"]),
            mitigations=yaml_data.get("mitigations", []),
            attacks=attacks
        )
