import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
from html import escape

from brain.brain import BrainComponent
from enums.severity import Severity


@dataclass
class ChartData:
    labels: List[str]
    blocked_data: List[int]
    succeeded_data: List[int]


@dataclass
class CategoryStats:
    blocked: int
    succeeded: int
    responses: List[str]
    description: str
    mitigations: List[str]
    block_percentage: int


class HTMLTemplates:
    KEY_RECOMMENDATIONS = r"""<li class="list-group-item">{recommendation}</li>"""

    RESPONSE_BLOCKED = r"""<tr>
                        <td class="description-cell">{description} {ai_badge}</td>
                        <td>Protected</td>
                        <td>-</td>
                        <td>{message}</td>
                    </tr>"""

    RESPONSE_SUCCEEDED = r"""<tr>
                        <td class="description-cell">{description} {ai_badge}</td>
                        <td>Compromised</td>
                        <td><span class="severity-badge severity-{severity}">{severity}</span></td>
                        <td>{message}</td>
                    </tr>"""

    MITIGATION = r"""<li>{mitigation}</li>"""

    ATTACK_ANALYSIS = r"""<div class="section-container">
            <h3 class="text-left my-4">2.{attack_num}. {attack_category} - {block_percentage}% Block Rate</h3>
            <p><strong>Description:</strong> 
            <p>{attack_description}</p>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Result</th>
                        <th>Severity</th>
                        <th>Target's Response</th>
                    </tr>
                </thead>
                <tbody>
                    {response_blocks}
                </tbody>
            </table>
            <p><strong>Mitigations:</strong> 
                <ul>
                    {mitigations}
                </ul>
            </p>
            </div>

            <div class="page-break"></div>"""



def _prepare_chart_data(category_stats: Dict[str, CategoryStats]) -> ChartData:
    """Prepare data for charts"""
    return ChartData(
        labels=[name for name in category_stats.keys()],
        blocked_data=[stats.blocked for stats in category_stats.values()],
        succeeded_data=[stats.succeeded for stats in category_stats.values()]
    )


def safe_response(response: str):
    """Replace sensitive data with asterisks"""
    import re
    # Patterns to match various sensitive info
    patterns = [
        r'password[=:]\s*[\'"]*([^\s\'"]+)',  # Passwords
        r'password is\s*[\'"]*([^\s\'"]+)',  # Passwords
        r'pass is\s*[\'"]*([^\s\'"]+)',  # Passwords
        r'(password\S+|\S+password|\S*(?:p@ssw0rd|admin|root|toor|qwerty)\S*)' # Common passwords
        r'secret[=:]\s*[\'"]*([^\s\'"]+)',  # Secrets
        r'secret is\s*[\'"]*([^\s\'"]+)',  # Secrets
        r'account[=:]\s*[\'"]*([^\s\'"]+)',  # Passwords
        r'token[=:]\s*[\'"]*([^\s\'"]+)',  # Tokens
        r'token is\s*[\'"]*([^\s\'"]+)',  # Tokens
        r'key[=:]\s*[\'"]*([^\s\'"]+)',  # API keys
        r'key is\s*[\'"]*([^\s\'"]+)',  # Keys
        r'api[_\s]?key[=:]\s*[\'"]*([^\s\'"]+)',  # API keys
        r'(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)',  # Emails
        r'([0-9]{13,19})',  # Credit card numbers
        r'([0-9]{3,4}[-\s]?[0-9]{4})',  # SSN/SIN numbers
        r'(eyJ[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*)',  # JWT tokens
        r'(?:password|secret|token)["\s:]+["\s]*([^\s"\']+)',  # Key-value with sensitive data
        r'(?:bearer|auth(?:orization)?)["\s:]+["\s]*([^\s"\']+)'  # Auth headers with tokens
    ]
    for pattern in patterns:
        response = re.sub(pattern,
                          lambda m: m.group(1)[:2] + '*' * (len(m.group(1)) - 2),
                          response,
                          flags=re.IGNORECASE)
    return escape(response)


class ReportGenerator:
    def __init__(self, brain: BrainComponent):
        self.brain = brain
        self.templates = HTMLTemplates()

    def generate_report(self) -> str:
        """Main method to generate the complete HTML report"""
        summary_stats = self._calculate_summary_stats()
        category_stats = self._analyze_categories()
        chart_data = _prepare_chart_data(category_stats)
        detailed_analysis = self._generate_detailed_analysis(category_stats)

        return self._fill_template(
            summary_stats,
            self._generate_recommendations(),
            detailed_analysis,
            chart_data
        )

    def _calculate_summary_stats(self) -> Dict[str, int]:
        """Calculate overall statistics"""
        overall_score = self._calculate_weighted_score()
        # Always use individual attack counts for stats
        total = len(self.brain.successful_attacks) + len(self.brain.failed_attacks)
        blocked = len(self.brain.failed_attacks)
        succeeded = len(self.brain.successful_attacks)

        return {
            "total": total,
            "blocked": blocked,
            "succeeded": succeeded,
            "score": overall_score
        }

    def _calculate_weighted_score(self) -> int:
        """Calculate a weighted score that takes into account severity and categories"""
        severity_weights = {
            Severity.get_severity_by_name("CRITICAL"): 1.2,
            Severity.get_severity_by_name("HIGH"): 1,
            Severity.get_severity_by_name("MEDIUM"): 0.6,
            Severity.get_severity_by_name("LOW"): 0.3,
            Severity.get_severity_by_name("INFORMATIONAL"): 0.1
        }

        if len(self.brain.failed_attacks) == 0:
            return 100

        if len(self.brain.successful_attacks) == 0:
            return 0

        weighted_attacks = sum(severity_weights[attack.severity] for attack in self.brain.successful_attacks)
        attacks_p =  weighted_attacks / (len(self.brain.successful_attacks) + len(self.brain.failed_attacks))
        categories_p = len(self.brain.successful_attack_categories) / len(self.brain.attack_categories)

        penalty = 0.7 * attacks_p + 0.3 * categories_p
        penalty = max(0.01, min(0.99, penalty))
        score = 100 * (1 - penalty)

        return int(score)

    def _analyze_categories(self) -> Dict[str, CategoryStats]:
        """Analyze attack results by category"""
        category_data = defaultdict(lambda: CategoryStats(0, 0, [], "", [], 0))

        for category in self.brain.attack_categories:
            if any(attack in category.attacks for attack in self.brain.successful_attacks + self.brain.failed_attacks):
                category_data[category.name].description = category.description
                category_data[category.name].mitigations = category.mitigations

        for attack in self.brain.successful_attacks:
            for category in self.brain.attack_categories:
                if attack in category.attacks:
                    stats = category_data[category.name]
                    stats.succeeded += 1
                    stats.responses.append(self._format_response(attack, succeeded=True))

        for attack in self.brain.failed_attacks:
            for category in self.brain.attack_categories:
                if attack in category.attacks:
                    stats = category_data[category.name]
                    stats.blocked += 1
                    stats.responses.append(self._format_response(attack, succeeded=False))

        for stats in category_data.values():
            total = stats.blocked + stats.succeeded
            stats.block_percentage = int((stats.blocked / total) * 100) if total > 0 else 0

        return category_data

    def _format_response(self, attack, succeeded: bool) -> str:
        """Format a single attack response"""
        template = self.templates.RESPONSE_SUCCEEDED if succeeded else self.templates.RESPONSE_BLOCKED
        message = attack.chatbot_output[-1] if attack.chatbot_output else "N/A"
        
        # Add an AI badge if the attack uses AI analysis
        tooltip_text = "This attack was analyzed using AI techniques to evaluate the response"
        ai_badge = f'<span class="ai-badge" data-tooltip="{tooltip_text}">AI</span>' if attack.use_ai_if_bad_output else ''
        
        if succeeded:
            severity = attack.severity.name
            return template.format(
                description=attack.description,
                message=safe_response(message),
                severity=severity,
                ai_badge=ai_badge
            )
        else:
            return template.format(
                description=attack.description,
                message=safe_response(message),
                ai_badge=ai_badge
            )

    def _generate_detailed_analysis(self, category_stats: Dict[str, CategoryStats]) -> str:
        """Generate the detailed analysis HTML"""
        analysis_sections = []
        for attack_num, (category_name, stats) in enumerate(category_stats.items(), 1):
            analysis_sections.append(
                self.templates.ATTACK_ANALYSIS.format(
                    attack_num=attack_num,
                    attack_category=category_name,
                    block_percentage=stats.block_percentage,
                    attack_description=stats.description,
                    response_blocks="\n".join(stats.responses),
                    mitigations="\n".join(
                        self.templates.MITIGATION.format(mitigation=mitigation) for mitigation in stats.mitigations)
                )
            )
        return "\n".join(analysis_sections)

    def _generate_recommendations(self) -> str:
        """Generate recommendations HTML"""
        # TODO: Actually generate recommendations based on the analysis
        return self.templates.KEY_RECOMMENDATIONS.format(recommendation="Implement proper security controls")

    def _fill_template(self, summary_stats: Dict[str, int], recommendations: str,
                       detailed_analysis: str, chart_data: ChartData) -> str:
        """Fill the HTML template with all generated content"""
        with open(os.path.join(os.path.dirname(__file__), "template_to_format.html"), "r") as f:
            template = f.read()

        # Add the current date to the template
        current_date = datetime.now().strftime("%B %d, %Y")
        
        report_html = (template
                       .replace("{chatastrophe_overall_score}", str(summary_stats["score"]))
                       .replace("{chatastrophe_key_recommendations}", recommendations)
                       .replace("{chatastrophe_detailed_attacks_analysis}", detailed_analysis)
                       .replace("{chatastrophe_attack_labels}", str(chart_data.labels))
                       .replace("{chatastrophe_blocked_data}", str(chart_data.blocked_data))
                       .replace("{chatastrophe_succeeded_data}", str(chart_data.succeeded_data))
                       .replace("{chatastrophe_blocked_attacks_number}", str(summary_stats["blocked"]))
                       .replace("{chatastrophe_succeeded_attacks_number}", str(summary_stats["succeeded"]))
                       .replace("{current_date}", current_date)
                       .replace("{chatbot_url}", self.brain.chatbot_endpoint)
                       )

        with open("report.html", "w", encoding="utf-8", errors="backslashreplace") as f:
            f.write(report_html)

        return report_html

