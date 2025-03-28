import argparse
import asyncio
import aiohttp
from rich.console import Console
from rich.prompt import Prompt
import time

console = Console()

ASCII_ART = """
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░▒▓████████▓▒░▒▓██████▓▒░ ░▒▓███████▓▒░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░      ░▒▓████████▓▒░▒▓████████▓▒░ ░▒▓█▓▒░  ░▒▓████████▓▒░░▒▓██████▓▒░   ░▒▓█▓▒░   ░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓██████▓▒░   
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░   ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░ 
"""

API_BASE_URL = "http://localhost:3333"
DEFAULT_FILENAME = "report.html"
DEFAULT_FORMAT = "html"
API_KEY = "chatastrophe_token"

DESCRIPTION = """
This is a client for the chatastrophe API.
It allows you to test your chatbot against a variety of attack scenarios.
Click enter to get started.
"""

def get_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--url', help='URL of the chatbot to test')
    parser.add_argument('--type', help='Type of chatbot to test')
    parser.add_argument('--scenarios', nargs='+', help='List of scenarios to test')
    parser.add_argument('--filename', help='Output filename for the report')
    parser.add_argument('--format', help='Format of the output report')
    return parser.parse_args()

async def get_scenarios():
    headers = {"Authorization": API_KEY}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/get-attack-categories", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                console.print(f"[red]Error getting scenarios: {await response.text()}[/red]")
                return []
        except Exception as e:
            console.print(f"[red]Error getting scenarios: {str(e)}[/red]")
            return []

async def get_chatbot_types():
    headers = {"Authorization": API_KEY}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/get-available-chatbots", headers=headers) as response:
                if response.status == 200:
                    chatbots = await response.json()
                    return [chatbot.get("name") for chatbot in chatbots.get("available_chatbots", [])]
                console.print(f"[red]Error getting chatbot types: {await response.text()}[/red]")
                return []
        except Exception as e:
            console.print(f"[red]Error getting chatbot types: {str(e)}[/red]")
            return []

def interactive_input(scenarios, chatbot_types):
    console.print(ASCII_ART)
    console.print("[bold cyan]Enter Chatbot Details[/bold cyan]")
    type = Prompt.ask("Enter chatbot type", choices=chatbot_types)
    url = Prompt.ask("Enter chatbot URL")
    filename = Prompt.ask("Enter report file path", default=DEFAULT_FILENAME)
    format = Prompt.ask("Enter report format", default=DEFAULT_FORMAT)
    console.print("\n[bold yellow]Available Attack Scenarios:[/bold yellow]")
    for i, scenario in enumerate(scenarios, 1):
        console.print(f"{i}. {scenario}")
    input_scenarios = Prompt.ask("Select attack scenarios (comma-separated numbers, or 0 for all)", default=0)
    if input_scenarios == '0':
        selected_scenarios = scenarios
    else:
        selected_scenarios = []
        for i in input_scenarios.split(","):
            if i.isdigit() and 1 <= int(i) <= len(scenarios):
                selected_scenarios.append(scenarios[int(i) - 1])
    return type, url, selected_scenarios, filename, format

async def perform_attack(type, url, scenarios):
    headers = {"Authorization": API_KEY}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{API_BASE_URL}/perform-attack",
                json={"url": url, "name": type, "attack_types": scenarios},
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("attack_id")
                console.print(f"[red]Error performing attack: {await response.text()}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Error performing attack: {str(e)}[/red]")
            return None

async def get_report(attack_id):
    headers = {"Authorization": API_KEY}
    with console.status("[bold green]Generating report...") as status:
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
                                return data.get("report").encode()
                            elif data.get("status") == "Attack in progress":
                                status.update("[bold yellow]Attack in progress...")
                                await asyncio.sleep(2)  # Wait 2 seconds before checking again
                            else:
                                console.print(f"[red]Error: {data.get('status')}[/red]")
                                return None
                        else:
                            console.print(f"[red]Error getting report: {await response.text()}[/red]")
                            return None
                except Exception as e:
                    console.print(f"[red]Error getting report: {str(e)}[/red]")
                    return None

async def main():
    args = get_args()
    available_scenarios = await get_scenarios()
    available_chatbot_types = await get_chatbot_types()
    
    if not available_scenarios or not available_chatbot_types:
        console.print("[red]Failed to get required data from API. Exiting...[/red]")
        return

    if args.url and args.type:
        url, type = args.url, args.type
        if type not in available_chatbot_types:
            console.print(f"[bold red]Error: Invalid chatbot type. Please choose from: {', '.join(available_chatbot_types)}")
            return
        filename = args.filename if args.filename else DEFAULT_FILENAME
        format = args.format if args.format else DEFAULT_FORMAT
        if args.scenarios:
            for scenario in args.scenarios:
                if scenario not in available_scenarios:
                    console.print(f"[bold red]Error: {scenario} is not a valid scenario. Please choose from: {', '.join(available_scenarios)}")
                    return
            scenarios = args.scenarios
        else:
            scenarios = available_scenarios 
    else:
        type, url, scenarios, filename, format = interactive_input(available_scenarios, available_chatbot_types)
    
    console.print(f"\n[bold green]Testing your chatbot at {url}[/bold green]")
    
    # Perform attack and get report
    attack_id = await perform_attack(type, url, scenarios)
    if not attack_id:
        console.print("[red]Failed to start attack. Exiting...[/red]")
        return

    # Wait for report and save it
    report_data = await get_report(attack_id)
    
    if report_data:
        with open(filename, "wb") as f:
            f.write(report_data)
        console.print(f"\n[bold green]Report saved to {filename}[/bold green]")
    else:
        console.print("[red]Failed to get report. Exiting...[/red]")

if __name__ == "__main__":
    asyncio.run(main())
