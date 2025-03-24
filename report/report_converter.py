import os

from brain.brain import BrainComponent
from collections import defaultdict

KEY_RECOMMENDATIONS_HTML = r"""<li class="list-group-item">recommendation</li>"""

RESPONSE_BLOCKED_BLOCK = r"""<tr>
                        <td>attack description</td>
                        <td>Blocked</td>
                        <td>message</td>
                    </tr>"""

RESPONSE_BLOCKED_SUCCEEDED = r"""<tr>
                        <td>attack description</td>
                        <td>Succeeded</td>
                        <td>message</td>
                    </tr>"""

MITIGATION_HTML = r"""<li>do this</li>"""

ATTACK_ANALYSIS_HTML = r"""<h3 class="text-left my-4">2.1. {attack_category} - {block_percentage}% Block Rate</h3>
            <p><strong>Description:</strong> 
            <p>{attack_description}</p>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Result</th>
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

            <div class="page-break"></div>"""


def convert_brain_results_to_html(brain: BrainComponent) -> str:
    # 1. Executive Summary values
    total_attacks = len(brain.successful_attacks) + len(brain.failed_attacks)
    blocked_attacks = len(brain.failed_attacks)
    succeeded_attacks = len(brain.successful_attacks)
    overall_score = int((blocked_attacks / total_attacks) * 100) if total_attacks > 0 else 0

    # 2. Key Recommendations (you can customize logic here)
    key_recommendations_html = KEY_RECOMMENDATIONS_HTML  # Placeholder

    # 3. Attack block/success analysis per category
    category_data = defaultdict(lambda: {
        "blocked": 0,
        "succeeded": 0,
        "responses": [],
        "description": ""
    })

    for category in brain.attack_categories:
        category_data[category.name]["description"] = category.description

    for attack in brain.successful_attacks:
        for category in brain.attack_categories:
            if attack in category.attacks:
                category_data[category.name]["succeeded"] += 1
                response_html = RESPONSE_BLOCKED_SUCCEEDED.replace("attack description", attack.description).replace(
                    "message", attack.chatbot_output[-1] if attack.chatbot_output else "N/A")
                category_data[category.name]["responses"].append(response_html)

    for attack in brain.failed_attacks:
        for category in brain.attack_categories:
            if attack in category.attacks:
                category_data[category.name]["blocked"] += 1
                response_html = (RESPONSE_BLOCKED_BLOCK.replace("attack description", attack.description)
                                 .replace("message", attack.chatbot_output[-1] if attack.chatbot_output else "N/A"))
                category_data[category.name]["responses"].append(response_html)

    # Prepare chart data
    attack_labels = []
    blocked_data = []
    succeeded_data = []

    detailed_analysis_html = ""

    for category_name, data in category_data.items():
        total = data["blocked"] + data["succeeded"]
        block_percentage = int((data["blocked"] / total) * 100) if total > 0 else 0

        attack_labels.append(category_name)
        blocked_data.append(data["blocked"])
        succeeded_data.append(data["succeeded"])

        attack_html = ATTACK_ANALYSIS_HTML.format(
            attack_category=category_name,
            block_percentage=block_percentage,
            attack_description=data["description"],
            response_blocks="\n".join(data["responses"]),
            mitigations=MITIGATION_HTML  # You can dynamically generate mitigations here if needed
        )

        detailed_analysis_html += attack_html

    # Final HTML with placeholders filled
    with open(os.path.join(os.path.dirname(__file__), "template_to_format.html"), "r") as f:
        template = f.read()

    report_html = (template
                   .replace("{chatastrophe_overall_score}", str(overall_score))
                   .replace("{chatastrophe_key_recommendations}", key_recommendations_html)
                   .replace("{chatastrophe_detailed_attacks_analysis}", detailed_analysis_html)
                   .replace("{chatastrophe_attack_labels}", str(attack_labels))
                   .replace("{chatastrophe_blocked_data}", str(blocked_data))
                   .replace("{chatastrophe_succeeded_data}", str(succeeded_data))
                   .replace("{chatastrophe_blocked_attacks_number}", str(blocked_attacks))
                   .replace("{chatastrophe_succeeded_attacks_number}", str(succeeded_attacks))
                   )

    # Debug
    with open("report.html", "w") as f:
        f.write(report_html)

    return report_html
