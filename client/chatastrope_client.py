import argparse
import asyncio
import aiohttp
from rich.console import Console
from rich.prompt import Prompt

console = Console()
API_BASE_URL = "https://localhost:1234" # TODO replace with actual address
DEFAULT_FILENAME = "report.pdf"


async def get_scenarios():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{API_BASE_URL}/list-scenarios") as response:
                    return await response.json() # TODO format based on the API response
            except Exception as e:
                return []


def get_args(scenarios):
    parser = argparse.ArgumentParser(description="Automatic testing for your AI chatbot")
    parser.add_argument("--url", type=str, help="Chatbot URL")
    parser.add_argument("--filename", type=str, choices=scenarios, help="path of the file the report will be saved to") 
    parser.add_argument("--scenarios", nargs="*", choices=scenarios, help="scenarios to test") # TODO handle errors with scenarios
    return parser.parse_args()

async def send_request(url, data):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                return await response.json()
        except Exception as e:
            return None

def interactive_input(scenarios):
    console.print("[bold cyan]Interactive Mode: Enter Chatbot Details[/bold cyan]")
    url = Prompt.ask("Enter chatbot URL")
    filename = Prompt.ask("Enter report file path (default: report.pdf)")
    if not filename:
        filename = DEFAULT_FILENAME
    console.print("\n[bold yellow]Available Attack Scenarios:[/bold yellow]") # TODO change colors
    scenarios = get_scenarios()
    for i, scenario in enumerate(scenarios, 1):
        console.print(f"{i}. {scenario}")
    inptut_scenarios = Prompt.ask("Select attack scenarios (comma-separated numbers, or 0 for all)", default=0)
    if inptut_scenarios == '0':
        selected_scenarios = scenarios
    else:
        selected_scenarios_str = inptut_scenarios.split(",")
        for i in selected_scenarios_str:
            if i.isdigit() and 1 <= int(i) <= len(scenarios):
                selected_scenarios.append(scenarios[int(i) - 1])
    return url, selected_scenarios, filename

async def run_scenarios(url, scenarios):
    response = await send_request(API_BASE_URL, {"url": url, "scenario": scenarios}) #TODO format based on the API response
    if response:
        return response

async def main():
    available_scenarios = get_scenarios()
    args = get_args(available_scenarios)
    
    if args.url and args.scenarios and args.filename:
        url, scenarios, filename = args.url, args.scenarios, args.filename
    elif args.url and args.scenarios:
        url, scenarios, filename = args.url, args.scenarios, DEFAULT_FILENAME
    elif args.url:
        url, scenarios, filename = args.url, available_scenarios, DEFAULT_FILENAME
    else:
        url, scenarios, filename = interactive_input(available_scenarios)
    
    console.print(f"\n[bold green]Testing your chatbot at {url}")
    
    async with open(filename, "wb") as f: # TODO handle errors with file   
        f.write(await run_scenarios(url, scenarios))

    console.print(f"\n[bold green]saved report to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
