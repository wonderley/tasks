import os
import requests
from datetime import datetime
import re
import sys

def parse_duration(task_content):
    # Find duration in format [Xh] or [Xm]
    match = re.search(r'\[(\d+)([hm])\]', task_content)
    if match:
        value, unit = match.groups()
        if unit == 'h':
            return float(value)
        elif unit == 'm':
            return float(value) / 60
    return 0.0

def get_today_tasks():
    # Get API token from environment variable
    api_token = os.getenv('TODOIST_API_TOKEN')
    if not api_token:
        raise ValueError("TODOIST_API_TOKEN environment variable is not set")
    
    # Set up the API request
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    try:
        # Get all tasks
        response = requests.get(
            "https://api.todoist.com/rest/v2/tasks",
            headers=headers,
            verify=False  # Disable SSL verification
        )
        response.raise_for_status()
        tasks = response.json()
        
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Filter tasks that are due today
        return [task for task in tasks if task.get('due') and task['due']['date'] == today]
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def show_help():
    print("Usage: python app.py <command>")
    print("\nCommands:")
    print("  total    - Show total number of tasks and total time for today")
    print("  list     - Show list of all tasks due today")
    print("  help     - Show this help message")

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]
    today_tasks = get_today_tasks()

    if command == "total":
        total_hours = sum(parse_duration(task['content']) for task in today_tasks)
        print(f"{len(today_tasks)} tasks remaining today, totaling {total_hours:.1f} hours")
    elif command == "list":
        print(f"\nTasks due today:")
        for task in today_tasks:
            print(f"- {task['content']}")
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    # Suppress only the single InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    main()