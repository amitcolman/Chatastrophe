import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

from brain.brain import BrainComponent


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
                        <td>{description}</td>
                        <td>Protected</td>
                        <td>-</td>
                        <td>{message}</td>
                    </tr>"""

    RESPONSE_SUCCEEDED = r"""<tr>
                        <td>{description}</td>
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


class ReportGenerator:
    def __init__(self, brain: BrainComponent):
        self.brain = brain
        self.templates = HTMLTemplates()

    def generate_report(self) -> str:
        """Main method to generate the complete HTML report"""
        summary_stats = self._calculate_summary_stats()
        category_stats = self._analyze_categories()
        chart_data = self._prepare_chart_data(category_stats)
        detailed_analysis = self._generate_detailed_analysis(category_stats)

        return self._fill_template(
            summary_stats,
            self._generate_recommendations(),
            detailed_analysis,
            chart_data
        )

    def _calculate_summary_stats(self) -> Dict[str, int]:
        """Calculate overall statistics"""
        total_attacks = len(self.brain.successful_attacks) + len(self.brain.failed_attacks)
        blocked_attacks = len(self.brain.failed_attacks)
        succeeded_attacks = len(self.brain.successful_attacks)
        overall_score = int((blocked_attacks / total_attacks) * 100) if total_attacks > 0 else 0

        return {
            "total": total_attacks,
            "blocked": blocked_attacks,
            "succeeded": succeeded_attacks,
            "score": overall_score
        }

    def _analyze_categories(self) -> Dict[str, CategoryStats]:
        """Analyze attack results by category"""
        category_data = defaultdict(lambda: CategoryStats(0, 0, [], "", [], 0))

        # Set descriptions and mitigations
        for category in self.brain.attack_categories:
            if any(attack in category.attacks for attack in self.brain.successful_attacks + self.brain.failed_attacks):
                category_data[category.name].description = category.description
                category_data[category.name].mitigations = category.mitigations

        # Analyze successful attacks
        for attack in self.brain.successful_attacks:
            for category in self.brain.attack_categories:
                if attack in category.attacks:
                    stats = category_data[category.name]
                    stats.succeeded += 1
                    stats.responses.append(self._format_response(attack, succeeded=True))

        # Analyze failed attacks
        for attack in self.brain.failed_attacks:
            for category in self.brain.attack_categories:
                if attack in category.attacks:
                    stats = category_data[category.name]
                    stats.blocked += 1
                    stats.responses.append(self._format_response(attack, succeeded=False))

        # Calculate block percentages
        for stats in category_data.values():
            total = stats.blocked + stats.succeeded
            stats.block_percentage = int((stats.blocked / total) * 100) if total > 0 else 0

        return category_data

    def _format_response(self, attack, succeeded: bool) -> str:
        """Format a single attack response"""
        template = self.templates.RESPONSE_SUCCEEDED if succeeded else self.templates.RESPONSE_BLOCKED
        message = attack.chatbot_output[-1] if attack.chatbot_output else "N/A"
        
        if succeeded:
            severity = attack.severity.name
            return template.format(
                description=attack.description,
                message=message,
                severity=severity
            )
        else:
            return template.format(
                description=attack.description,
                message=message
            )

    def _prepare_chart_data(self, category_stats: Dict[str, CategoryStats]) -> ChartData:
        """Prepare data for charts"""
        return ChartData(
            labels=[name for name in category_stats.keys()],
            blocked_data=[stats.blocked for stats in category_stats.values()],
            succeeded_data=[stats.succeeded for stats in category_stats.values()]
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

        # Add current date to the template
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
                       )

        with open("report.html", "w", encoding="utf-8", errors="backslashreplace") as f:
            f.write(report_html)

        return report_html