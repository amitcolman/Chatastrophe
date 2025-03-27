import argparse
import asyncio
import aiohttp 
import json
from rich.console import Console
from rich.prompt import Prompt

console = Console()
API_BASE_URL = "https://localhost:1234" # TODO replace with actual address
DEFAULT_FILENAME = "report.html"
DEFAULT_FORMAT = "html"
DESCRIPTION="""
This is a client for the chatastrophe API.
It allows you to test your chatbot against a variety of attack scenarios.
Click enter to get started.
"""
ASCII_ART = """

 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░▒▓████████▓▒░▒▓██████▓▒░ ░▒▓███████▓▒░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░      ░▒▓████████▓▒░▒▓████████▓▒░ ░▒▓█▓▒░  ░▒▓████████▓▒░░▒▓██████▓▒░   ░▒▓█▓▒░   ░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓████████▓▒░▒▓██████▓▒░   
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░   ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ 
                                                                                                                                                                                                                                                                                                                                                                                                                                                        
"""


async def get_scenarios():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{API_BASE_URL}/list-scenarios") as response:
                    return await response.json() # TODO format based on the API response
            except Exception as e:
                return []
                
async def get_chatbot_types():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/get-available-chatbots") as response:
                chatbots = await response.json()
                chatbot_types = [chatbot["name"] for chatbot in chatbots]
                return chatbot_types
                
        except Exception as e:
            return []

def get_args():
    parser = argparse.ArgumentParser(description="Automatic testing for your AI chatbot")
    parser.add_argument("--url", type=str, help="Chatbot URL")
    parser.add_argument("--api-key", type=str, help="API key")
    parser.add_argument("--type", type=str, help="type of the chatbot's type")
    parser.add_argument("--file-name", type=str, nargs='?', help="path of the file the report will be saved to", default=DEFAULT_FILENAME)
    parser.add_argument("--format", type=str, nargs='?', help="format of the report", choices=["html"], default=DEFAULT_FORMAT) 
    parser.add_argument("--scenarios", nargs="*", help="scenarios to test") 
    return parser.parse_args()

def interactive_input(scenarios, chatbot_types):
    console.print(ASCII_ART)
    console.print("[bold cyan]Enter Chatbot Details[/bold cyan]")
    type = Prompt.ask("Enter chatbot type", choices=chatbot_types)
    url = Prompt.ask("Enter chatbot URL")
    api_key = Prompt.ask("Enter API key")
    filename = Prompt.ask("Enter report file path", default=DEFAULT_FILENAME)
    format = Prompt.ask("Enter report format", default=DEFAULT_FORMAT)
    console.print("\n[bold yellow]Available Attack Scenarios:[/bold yellow]") # TODO change colors
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
    return type, url, api_key, selected_scenarios, filename, format

async def run_scenarios(type, url, api_key, scenarios):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE_URL}/perform-attack", json={"url": url, "name": type, "api_key": api_key, "attack_types": scenarios}) as response:
                status = await response.status()
                if status == 200:
                    return await get_report()
                else: # TODO handle errors with request
                    return None
        except Exception as e:
            return None

async def get_report():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/get-report") as response:
                status = await response.status()
                if status == 200:
                    return await response.read()
                else: # TODO handle errors with request
                    return None
        except Exception as e:
            return None


async def main():
    args = get_args()
    available_scenarios = get_scenarios()
    available_chatbot_types = get_chatbot_types()
    # available_scenarios = ["scenario1", "scenario2", "scenario3"] # temp - for testing purpouses
    # available_chatbot_types = ["chatbot1", "chatbot2", "chatbot3"]
    if args.url and args.api_key and args.type:
        url, api_key, type = args.url, args.api_key, args.type
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
        type, url, api_key, scenarios, filename, format = interactive_input(available_scenarios, available_chatbot_types)
    
    console.print(f"\n[bold green]Testing your chatbot at {url}")
    
    async with open(filename, "wb") as f: # TODO handle errors with file   
        data = await run_scenarios(type, url, api_key, scenarios)
        f.write(data)

    console.print(f"\n[bold green]saved report to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
