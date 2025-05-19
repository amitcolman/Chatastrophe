import argparse
import asyncio
import aiohttp
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn, ProgressColumn, Task, SpinnerColumn
from rich.spinner import Spinner
from rich import box
import time
from time import sleep
import requests
from rich.text import Text
import sys

console = Console()

# Custom spinner column that only shows for incomplete tasks
class TaskSpinnerColumn(SpinnerColumn):
    def __init__(self, spinner_name="dots", style="cyan"):
        super().__init__(spinner_name=spinner_name, style=style)
        
    def render(self, task: Task) -> str:
        """Show spinner only for incomplete tasks. Show green checkmark when complete."""
        if task.completed < task.total:
            return super().render(task)
        return "[bright_green]✔[/bright_green]"  # Bright green checkmark for completed tasks

# Custom column to show the title in blue while in progress and green when complete
class TitleColumn(ProgressColumn):
    def render(self, task: Task) -> Text:
        if task.completed >= task.total:
            return Text(task.description, style="bold green")
        else:
            return Text(task.description, style="bold blue")

# Custom progress column to show completed/total count
class CompletedColumn(ProgressColumn):
    def render(self, task: Task) -> str:
        """Show completed/total as text."""
        if task.description.startswith("Overall"):
            # For overall progress, show completed/total scenarios
            completed_attacks = int(task.fields.get("completed_attacks", 0))
            total_attacks = int(task.fields.get("total_attacks", 0))
            return f"{completed_attacks}/{total_attacks}"
        else:
            # For individual scenarios, show actual attack counts
            completed_attacks = int(task.fields.get("completed_attacks", 0))
            total_attacks = int(task.fields.get("total_attacks", 0))
            return f"{completed_attacks}/{total_attacks}"

ASCII_ART = r"""
   ____ _   _    _  _____  _    ____ _____ ____   ___  ____  _   _ _____ 
  / ___| | | |  / \|_   _|/ \  / ___|_   _|  _ \ / _ \|  _ \| | | | ____|
 | |   | |_| | / _ \ | | / _ \ \___ \ | | | |_) | | | | |_) | |_| |  _|  
 | |___|  _  |/ ___ \| |/ ___ \ ___) || | |  _ <| |_| |  __/|  _  | |___ 
  \____|_| |_/_/   \_\_/_/   \_\____/ |_| |_| \_\\___/|_|   |_| |_|_____|                                                                     
"""

API_BASE_URL = "http://localhost:3333"
DEFAULT_FILENAME = "report.html"
DEFAULT_FORMAT = "html"
AVAILABLE_FORMATS = ["html"]
API_KEY = "chatastrophe_token"

DESCRIPTION = """
This is a client for the chatastrophe API.
It allows you to test your chatbot against a variety of attack scenarios.
Click enter to get started.
"""

def test_url(url):
    try:
        with console.status("Connecting to chatbot URL...", spinner="dots") as status:
            sleep(1)
            requests.get(url, timeout=5)
            status.update("")  
        return True
    except requests.Timeout:
        console.print("[red]Connection to chatbot timed out. Please check if the chatbot is running and accessible.[/red]")
        return False

def get_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--url', help='URL of the chatbot to test')
    parser.add_argument('--scenarios', nargs='+', help='List of scenarios to test')
    parser.add_argument('--filename', help='Output filename for the report', default=DEFAULT_FILENAME)
    parser.add_argument('--format', help='Format of the output report', default=DEFAULT_FORMAT, choices=AVAILABLE_FORMATS)
    return parser.parse_args()


async def get_scenarios():
    headers = {"Authorization": API_KEY}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/get-attack-categories", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                error_text = await response.text()
                console.print(f"[red]The server returned an error while fetching scenarios (status {response.status}): {error_text}[/red]")
                sys.exit(1)
        except aiohttp.ClientConnectionError:
            console.print("[red]Could not connect to the server. Please check your network or try again later.[/red]")
            sys.exit(1)
        except asyncio.TimeoutError:
            console.print("[red]The request to the server timed out. Please try again later.[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]An unexpected error occurred while connecting to the server: {e}[/red]")
            sys.exit(1)


def interactive_input(scenarios):
    console.print(f"[bold bright_green]{ASCII_ART}[/bold bright_green]")
    console.print("[bold bright_green][Enter Chatbot Details][/bold bright_green]")

    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        url = Prompt.ask(
            f"[pale_green1]Enter chatbot URL [/pale_green1]"
        )
        if test_url(url):
            break
        if attempt < max_attempts:
            pass
        else:
            console.print("[red]Maximum attempts reached. Exiting...[/red]")
            sys.exit(1)
        attempt += 1

    filename = Prompt.ask(
        "[pale_green1]Enter report file path[/pale_green1]",
        default=DEFAULT_FILENAME
    )
    format = Prompt.ask(
        "[pale_green1]Enter report format[/pale_green1]",
        default=DEFAULT_FORMAT,
        choices=AVAILABLE_FORMATS
    )
    console.print("\n[bold bright_green]Available Attack Scenarios:[/bold bright_green]")
    for i, scenario in enumerate(scenarios, 1):
        console.print(f"[pale_green1]{i}. {scenario}[/pale_green1]")
    input_scenarios = Prompt.ask(
        "[bright_green]Select attack scenarios (comma-separated numbers, or 0 for all)[/bright_green]",
        default="0",
    )
    while True:
        if input_scenarios == '0':
            selected_scenarios = scenarios
        else:
            selected_scenarios = []
            for i in input_scenarios.split(","):
                if not(i.isdigit()):
                    console.print(f"[red]Invalid scenarios. Please try again.[/red]")
                    input_scenarios = Prompt.ask(
                        "[bright_green]Select attack scenarios (comma-separated numbers, or 0 for all)[/bright_green]",
                        default="0",
                    )
                    break
                if  1 <= int(i) <= len(scenarios):
                    selected_scenarios.append(scenarios[int(i) - 1])
        return url, selected_scenarios, filename, format
  

async def perform_attack(url, scenarios):
    headers = {"Authorization": API_KEY}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                    f"{API_BASE_URL}/perform-attack",
                    json={"url": url, "attack_types": scenarios},
                    headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("attack_id")
                error_text = await response.text()
                console.print(f"[red]The server returned an error while starting the attack (status {response.status}): {error_text}[/red]")
                sys.exit(1)
        except aiohttp.ClientConnectionError:
            console.print("[red]Could not connect to the server. Please check your network or if the server is running.[/red]")
            sys.exit(1)
        except asyncio.TimeoutError:
            console.print("[red]The request to the server timed out. Please try again later.[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]An unexpected error occurred while starting the attack: {e}[/red]")
            sys.exit(1)


async def get_report(attack_id, scenarios):
    headers = {"Authorization": API_KEY}
    
    # Create progress bars for each category and overall progress
    with Progress(
        TaskSpinnerColumn(spinner_name="point", style="bright_cyan"),
        TitleColumn(),
        BarColumn(bar_width=50),
        CompletedColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console,
        expand=True
    ) as progress:
        try:
            # Create a task for each scenario
            scenario_tasks = {}
            for scenario in scenarios:
                scenario_tasks[scenario] = progress.add_task(
                    scenario,  # No [cyan] markup
                    total=100, 
                    completed=0,
                    completed_attacks=0,
                    total_attacks=0
                )
            
            progress.print("\n")
            
            # Create overall progress task
            overall_task = progress.add_task(
                "Overall Progress", 
                total=100, 
                completed=0,
                completed_attacks=0,
                total_attacks=0
            )
            
            # Track the total progress
            check_count = 0
            
            while True:
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(
                                f"{API_BASE_URL}/get-report",
                                json={"attack_id": attack_id},
                                headers=headers
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if data.get("status") == "completed":
                                    # Handle completed state
                                    overall_completed_attacks = 0
                                    overall_total_attacks = 0
                                    progress_data = data.get("progress", {})
                                    
                                    # First pass - get the correct totals
                                    for scenario in scenarios:
                                        if scenario in progress_data:
                                            total_attacks = progress_data[scenario].get("total_attacks", 0)
                                            overall_total_attacks += total_attacks
                                    
                                    # Process progress data if available
                                    if progress_data:
                                        for scenario, scenario_progress in progress_data.items():
                                            if scenario in scenario_tasks:
                                                # Get final counts - ensure completed matches total for completed state
                                                total_attacks = scenario_progress.get("total_attacks", 0)
                                                completed_attacks = total_attacks  # At completion, all attacks should show as complete
                                                
                                                # Update progress bar
                                                progress.update(
                                                    scenario_tasks[scenario],
                                                    completed=100,  # Always 100% at completion
                                                    completed_attacks=completed_attacks,
                                                    total_attacks=total_attacks
                                                )
                                                
                                                # Add to overall totals
                                                overall_completed_attacks += completed_attacks
                                    
                                    # Update overall progress - ensure values are consistent at completion
                                    progress.update(
                                        overall_task,
                                        completed=100,  # Always 100% at completion
                                        completed_attacks=overall_total_attacks,  # At completion, these should match
                                        total_attacks=overall_total_attacks
                                    )
                                    
                                    # Allow a moment to see final state
                                    await asyncio.sleep(1)
                                    return data.get("report").encode()
                                    
                                elif data.get("status") == "Attack in progress":
                                    # Handle in-progress state
                                    if "progress" in data:
                                        progress_data = data["progress"]
                                        overall_completed_attacks = 0
                                        overall_total_attacks = 0
                                        
                                        # First, calculate the total attacks across all categories
                                        for scenario in scenarios:
                                            if scenario in progress_data:
                                                overall_total_attacks += progress_data[scenario].get("total_attacks", 0)
                                        
                                        # Update progress for each category
                                        for scenario, scenario_progress in progress_data.items():
                                            if scenario in scenario_tasks:
                                                # Get percentage completion
                                                completed_percent = scenario_progress.get("completed", 0)
                                                
                                                # Get attack counts
                                                completed_attacks = scenario_progress.get("completed_attacks", 0)
                                                total_attacks = scenario_progress.get("total_attacks", 0)
                                                
                                                # Add to overall completed count
                                                overall_completed_attacks += completed_attacks
                                                
                                                # Update the progress bar
                                                progress.update(
                                                    scenario_tasks[scenario],
                                                    completed=completed_percent,
                                                    completed_attacks=completed_attacks,
                                                    total_attacks=total_attacks
                                                )
                                        
                                        # Calculate overall percentage based on completed/total attacks
                                        if overall_total_attacks > 0:
                                            overall_percent = (overall_completed_attacks / overall_total_attacks) * 100
                                        else:
                                            # Simple average if no attack counts yet
                                            overall_percent = sum(
                                                progress_data[s].get("completed", 0) for s in scenarios if s in progress_data
                                            ) / len(scenarios) if scenarios else 0
                                        
                                        # Update overall progress
                                        progress.update(
                                            overall_task,
                                            completed=overall_percent,
                                            completed_attacks=overall_completed_attacks,
                                            total_attacks=overall_total_attacks
                                        )
                                    else:
                                        # No progress data yet, show a simple animation
                                        check_count += 1
                                        tick = check_count % 10
                                        for scenario in scenarios:
                                            progress.update(scenario_tasks[scenario], 
                                                           completed=tick * 3,  # Just for animation
                                                           refresh=True)
                                        progress.update(overall_task, 
                                                       completed=tick * 3,  # Just for animation
                                                       refresh=True)
                                    
                                    # Check more frequently for updates
                                    await asyncio.sleep(1)
                                else:
                                    console.print(f"[red]Error: {data.get('status')}[/red]")
                                    sys.exit(1)
                            else:
                                error_text = await response.text()
                                console.print(f"[red]The server returned an error while fetching the report (status {response.status}): {error_text}[/red]")
                                sys.exit(1)
                    except aiohttp.ClientConnectionError:
                        console.print("[red]Could not connect to the server. Please check your network or if the server is running.[/red]")
                        sys.exit(1)
                    except asyncio.TimeoutError:
                        console.print("[red]The request to the server timed out. Please try again later.[/red]")
                        sys.exit(1)
                    except Exception as e:
                        console.print(f"[red]An unexpected error occurred while fetching the report: {e}[/red]")
                        sys.exit(1)
        except Exception as e:
            console.print(f"[red]An unexpected error occurred: {e}[/red]")
            sys.exit(1)


async def main():
    args = get_args()
    available_scenarios = await get_scenarios()

    if not available_scenarios:
        console.print("[red]Failed to get required data from API. Exiting...[/red]")
        return

    if args.url:
        url = args.url
        if not test_url(url):
            console.print("[red]Invalid URL. Please try again.[/red]")
            return
        filename = args.filename if args.filename else DEFAULT_FILENAME
        format = args.format if args.format else DEFAULT_FORMAT
        if args.scenarios:
            for scenario in args.scenarios:
                if scenario not in available_scenarios:
                    console.print(
                        f"[red]Error: {scenario} is not a valid scenario number.\nValid scenarios:[/red]")
                    console.print(f"[red]0. All Scenarios[/red]")
                    for i, scenario in enumerate(available_scenarios, 1):
                        console.print(f"[red]{i}. {scenario}[/red]")
                    return
            scenarios = args.scenarios
        else:
            scenarios = available_scenarios
    else:
        url, scenarios, filename, format = interactive_input(available_scenarios)

    console.print(f"\n[bold bright_green]Testing your chatbot at {url}[/bold bright_green]")

    # Perform attack and get report
    attack_id = await perform_attack(url, scenarios)
    if not attack_id:
        console.print("[red]Failed to start attack. Exiting...[/red]")
        return

    # Wait for report and save it
    report_data = await get_report(attack_id, scenarios)

    if report_data:
        with open(filename, "wb") as f:
            f.write(report_data)
        console.print(f"\n[bold bright_green]Report saved to {filename}[/bold bright_green]")
    else:
        console.print("[red]Failed to get report. Exiting...[/red]")


if __name__ == "__main__":
    asyncio.run(main())
