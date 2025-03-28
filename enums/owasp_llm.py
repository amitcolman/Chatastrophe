
from enum import Enum
from typing import Optional


class OwaspLLM(Enum):
    PROMPT_INJECTION = "LLM01:2025 Prompt Injection"
    SENSITIVE_INFORMATION_DISCLOSURE = "LLM02:2025 Sensitive Information Disclosure"
    SUPPLY_CHAIN = "LLM03:2025 Supply Chain"
    DATA_AND_MODEL_POISONING = "LLM04:2025 Data and Model Poisoning"
    IMPROPER_OUTPUT_HANDLING = "LLM05:2025 Improper Output Handling"
    EXCESSIVE_AGENCY = "LLM06:2025 Excessive Agency"
    SYSTEM_PROMPT_LEAKAGE = "LLM07:2025 System Prompt Leakage"
    VECTOR_AND_EMBEDDING_WEAKNESSES = "LLM08:2025 Vector and Embedding Weaknesses"
    MISINFORMATION = "LLM09:2025 Misinformation"
    UNBOUNDED_CONSUMPTION = "LLM10:2025 Unbounded Consumption"
    TEST = "TEST"

    @staticmethod
    def get_all_categories() -> list[str]:
        return [category.value for category in OwaspLLM]
    
    @staticmethod
    def get_category_by_name(name: str) -> Optional['OwaspLLM']:
        return next((category for category in OwaspLLM if category.name == name), None)
    
    @staticmethod
    def get_category_by_value(value: str) -> Optional['OwaspLLM']:
        return next((category for category in OwaspLLM if category.value == value), None)
