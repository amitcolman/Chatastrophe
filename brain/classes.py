
class Attack:
    def __init__(self, name: str, description: str, prompt: str, expected_outputs: list, severity: int,
                 use_ai_if_bad_output: bool = False, use_ai_if_inconclusive_output: bool = False):
        self.name = name
        self.description = description
        self.prompt = prompt
        self.expected_outputs = expected_outputs
        self.severity = severity
        self.use_ai_if_bad_output = use_ai_if_bad_output
        self.use_ai_if_inconclusive_output = use_ai_if_inconclusive_output

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
    def __init__(self, name: str, description: str, category: str, attacks: list[Attack]):
        self.name = name
        self.description = description
        self.category = category
        self.attacks = attacks

    @staticmethod
    def from_yaml(yaml_data: dict) -> 'AttackCategory':
        attacks = [Attack.from_yaml(attack) for attack in yaml_data.get("attacks", [])]
        return AttackCategory(
            name=yaml_data["name"],
            description=yaml_data["description"],
            category=yaml_data["category"],
            attacks=attacks
        )
