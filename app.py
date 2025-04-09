import os
import requests
from datetime import datetime, timedelta
import re
import sys
import json
from openai import OpenAI
import httpx

def get_target_date(args):
    """Determine the target date based on command line arguments."""
    if len(args) > 2 and args[2].lower() == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    return datetime.now().strftime('%Y-%m-%d')

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

def get_tasks_for_date(target_date, debug=False):
    # Get API token from environment variable
    api_token = os.getenv('TODOIST_API_TOKEN')
    if not api_token:
        raise ValueError("TODOIST_API_TOKEN environment variable is not set")
    
    # Set up the API request
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    try:
        # Get all tasks using Sync API
        response = requests.post(
            "https://api.todoist.com/sync/v9/sync",
            headers=headers,
            json={
                "sync_token": "*",  # Get all data
                "resource_types": ["items", "day_orders"]  # Get tasks and their day orders
            },
            verify=False  # Disable SSL verification
        )
        response.raise_for_status()
        data = response.json()
        
        if debug:
            print("\nDebug: Raw JSON response from Todoist:")
            print(json.dumps(data, indent=2))
        
        # Get day orders for sorting
        day_orders = data.get('day_orders', {})
        
        # Filter tasks that are due on target date and add their day_order
        tasks = []
        for task in data.get('items', []):
            if task.get('due') and task['due']['date'] == target_date and not task.get('checked', False):
                # Add day_order to the task object
                task['day_order'] = day_orders.get(task['id'], 999999)
                tasks.append(task)
                
        return tasks
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def get_priority_label(priority):
    # Todoist API uses 1-4 where 4 is highest priority
    # We'll convert to p1-p4 where p1 is highest priority
    priority_map = {4: "p1", 3: "p2", 2: "p3", 1: "p4"}
    return priority_map.get(priority, "p4")  # Default to p4 if priority not found

def test_openai():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set")
        return

    http_client = httpx.Client(verify=False)
    client = OpenAI(api_key=api_key, http_client=http_client)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Fixed model name
            messages=[
                {"role": "system", "content": "You are a helpful task management assistant."},
                {"role": "user", "content": "Say hello and briefly describe what you could help with regarding task management."}
            ]
        )
        print("\nOpenAI Response:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")

def show_help():
    print("Usage: python app.py <command> [tomorrow]")
    print("\nCommands:")
    print("  total    - Show total number of tasks and total time for today/tomorrow")
    print("  list     - Show list of all tasks due today/tomorrow")
    print("  openai   - Test OpenAI integration")
    print("  help     - Show this help message")
    print("\nOptions:")
    print("  tomorrow - Show tasks for tomorrow instead of today")
    print("  -debug   - Show debug information including raw API responses")

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]
    debug = "-debug" in sys.argv
    
    if command == "openai":
        test_openai()
        return

    target_date = get_target_date(sys.argv)
    tasks = get_tasks_for_date(target_date, debug)

    if command == "total":
        total_hours = sum(parse_duration(task['content']) for task in tasks)
        date_label = "tomorrow" if len(sys.argv) > 2 and sys.argv[2].lower() == "tomorrow" else "today"
        print(f"{len(tasks)} tasks remaining {date_label}, totaling {total_hours:.1f} hours")
    elif command == "list":
        # Sort tasks by priority (descending) and day_order (ascending)
        sorted_tasks = sorted(tasks, 
                            key=lambda x: (-x.get('priority', 1), x.get('day_order', 999999)))
        
        if debug:
            print("\nDebug: Sorted tasks:")
            print(json.dumps(sorted_tasks, indent=2))
        
        date_label = "tomorrow" if len(sys.argv) > 2 and sys.argv[2].lower() == "tomorrow" else "today"
        print(f"\nTasks due {date_label}:")
        for task in sorted_tasks:
            priority = get_priority_label(task.get('priority', 1))
            print(f"- [{priority}] {task['content']}")
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    # Suppress only the single InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    main()