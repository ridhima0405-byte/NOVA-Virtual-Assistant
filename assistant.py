
import ast
import operator
import webbrowser
import urllib.parse
import json
import re
import uuid
import os

from pathlib import Path
from datetime import datetime, timedelta

import requests
import pyttsx3
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError




# ---------------- OPENAI API CONFIGURATION ----------------

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        try:
            import streamlit as st
            api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
        except Exception:
            api_key = ""
    if not api_key:
        return None
    return OpenAI(api_key=api_key, timeout=30.0, max_retries=1)


def ask_llm(user_input, chat_history=None):
    try:
        client = get_openai_client()
        if client is None:
            return (
                "The OpenAI API key is not configured. Add OPENAI_API_KEY "
                "to your local .env file or Streamlit Cloud Secrets."
            )

        history = []
        for message in (chat_history or [])[-10:]:
            role = message.get("role")
            content = message.get("content", "")
            if role in ("user", "assistant") and content:
                history.append({"role": role, "content": content})

        if not history or history[-1]["content"] != user_input:
            history.append({"role": "user", "content": user_input})

        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=(
                "You are NOVA, a friendly and helpful AI virtual assistant. "
                "Answer clearly and accurately using simple language. "
                "If unsure, say so. Never claim to have performed actions "
                "on the user's device."
            ),
            input=history,
            max_output_tokens=700
        )
        answer = response.output_text
        return answer.strip() if answer else "I couldn't generate a response. Please try again."

    except OpenAIError as error:
        print("OpenAI API error:", repr(error))
        return (
            "NOVA couldn't connect to OpenAI. Check your API key, API billing "
            "or usage limits, and internet connection."
        )
    except Exception as error:
        print("AI response error:", repr(error))
        return "Something went wrong while generating an AI response. Please try again."


# ---------------- FILE STORAGE ----------------

TASK_FILE = Path(__file__).with_name("nova_tasks.json")
REMINDER_FILE = Path(__file__).with_name("nova_reminders.json")


def load_json(file_path):
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        return []
    except (json.JSONDecodeError, OSError) as e:
        print("Storage error:", e)
        return []


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


# ---------------- TEXT TO SPEECH ----------------

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("Voice error:", e)


# ---------------- TASK MANAGER ----------------

def load_tasks():
    return load_json(TASK_FILE)


def manage_tasks(command):

    tasks = load_tasks()

    if command.startswith("add task "):

        task = command.replace("add task ", "", 1).strip()

        if not task:
            return "Please tell me what task to add."

        tasks.append({
            "task": task,
            "completed": False
        })

        save_json(TASK_FILE, tasks)
        return "Task added successfully: " + task

    elif command in [
        "show my tasks", "show tasks",
        "my tasks", "list tasks"
    ]:

        if not tasks:
            return "You don't have any tasks yet."

        answer = "Here are your tasks:\n"

        for i, task in enumerate(tasks, start=1):
            status = "Completed" if task["completed"] else "Pending"
            answer += f"\n{i}. {task['task']} - {status}"

        return answer

    elif command.startswith("remove task "):

        try:
            number = int(command.replace("remove task ", "", 1).strip())

            if number < 1 or number > len(tasks):
                return "Invalid task number."

            removed = tasks.pop(number - 1)
            save_json(TASK_FILE, tasks)

            return "Removed task: " + removed["task"]

        except ValueError:
            return "Please provide a valid task number."

    elif command.startswith("complete task "):

        try:
            number = int(command.replace("complete task ", "", 1).strip())

            if number < 1 or number > len(tasks):
                return "Invalid task number."

            tasks[number - 1]["completed"] = True
            save_json(TASK_FILE, tasks)

            return "Great! Task completed: " + tasks[number - 1]["task"]

        except ValueError:
            return "Please provide a valid task number."

    elif command == "clear all tasks":

        if not tasks:
            return "Your task list is already empty."

        save_json(TASK_FILE, [])
        return "All tasks have been cleared."

    return None


# ---------------- REMINDER MANAGER ----------------

def load_reminders():
    return load_json(REMINDER_FILE)


def get_all_reminders():
    return load_reminders()


def get_due_reminders():

    reminders = load_reminders()
    now = datetime.now()
    due = []

    for reminder in reminders:

        if reminder.get("completed", False):
            continue

        try:
            reminder_time = datetime.fromisoformat(reminder["datetime"])

            if reminder_time <= now:
                due.append(reminder)

        except (ValueError, KeyError):
            continue

    return due


def add_reminder(command):

    match = re.search(
        r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        command,
        re.IGNORECASE
    )

    if not match:
        return "Please include a time. Example: Remind me to study at 7 PM."

    task_match = re.search(
        r"remind me to\s+(.+?)\s+at\s+",
        command,
        re.IGNORECASE
    )

    if not task_match:
        return "Please tell me what I should remind you about."

    task = task_match.group(1).strip()

    if not task:
        return "Please provide a reminder task."

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3).lower()

    if hour < 1 or hour > 12 or minute > 59:
        return "Please provide a valid time."

    if period == "pm" and hour != 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0

    now = datetime.now()

    if "tomorrow" in command:
        reminder_date = (now + timedelta(days=1)).date()
    else:
        reminder_date = now.date()

    reminder_time = datetime.combine(
        reminder_date,
        datetime.min.time()
    ).replace(hour=hour, minute=minute)

    if reminder_time <= now:
        if "tomorrow" in command:
            return "That time has already passed tomorrow. Please choose a later time."
        reminder_time += timedelta(days=1)

    reminders = load_reminders()

    reminder = {
        "id": str(uuid.uuid4()),
        "task": task,
        "datetime": reminder_time.isoformat(timespec="minutes"),
        "completed": False
    }

    reminders.append(reminder)
    save_json(REMINDER_FILE, reminders)

    return (
        "Reminder saved successfully!\n"
        f"Task: {task}\n"
        f"Time: {reminder_time.strftime('%d %B %Y at %I:%M %p')}"
    )


def manage_reminders(command):

    reminders = load_reminders()

    if command.startswith("remind me to "):
        return add_reminder(command)

    elif command in [
        "show my reminders",
        "show reminders",
        "my reminders",
        "list reminders"
    ]:

        if not reminders:
            return "You don't have any reminders yet."

        answer = "Here are your reminders:\n"

        for i, reminder in enumerate(reminders, start=1):

            status = (
                "Completed" if reminder["completed"]
                else "Pending"
            )

            try:
                time_text = datetime.fromisoformat(
                    reminder["datetime"]
                ).strftime("%d %b %Y, %I:%M %p")
            except (ValueError, KeyError):
                time_text = "Invalid date"

            answer += (
                f"\n{i}. {reminder['task']}"
                f" - {time_text} - {status}"
            )

        return answer

    elif command.startswith("delete reminder "):

        try:
            number = int(
                command.replace("delete reminder ", "", 1).strip()
            )

            if number < 1 or number > len(reminders):
                return "Invalid reminder number."

            removed = reminders.pop(number - 1)
            save_json(REMINDER_FILE, reminders)

            return "Deleted reminder: " + removed["task"]

        except ValueError:
            return "Please provide a valid reminder number."

    elif command.startswith("complete reminder "):

        try:
            number = int(
                command.replace("complete reminder ", "", 1).strip()
            )

            if number < 1 or number > len(reminders):
                return "Invalid reminder number."

            reminders[number - 1]["completed"] = True
            save_json(REMINDER_FILE, reminders)

            return "Reminder completed: " + reminders[number - 1]["task"]

        except ValueError:
            return "Please provide a valid reminder number."

    return None


# ---------------- SAFE CALCULATOR ----------------

def calculate(expression):

    expression = expression.lower().strip()

    prefixes = [
        "what is", "what's", "calculate",
        "solve", "compute", "how much is"
    ]

    for prefix in prefixes:
        if expression.startswith(prefix):
            expression = expression[len(prefix):].strip()
            break

    replacements = {
        "multiplied by": "*",
        "divided by": "/",
        "into": "*",
        "times": "*",
        "plus": "+",
        "minus": "-",
        "^": "**"
    }

    for old, new in replacements.items():
        expression = expression.replace(old, new)

    expression = expression.replace(" x ", " * ")
    expression = expression.rstrip(" =?").strip()

    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod
    }

    def evaluate(node):

        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in operations:

            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("Exponent too large")

            return operations[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):

            value = evaluate(node.operand)

            if isinstance(node.op, ast.UAdd):
                return value

            return -value

        raise ValueError("Invalid calculation")

    return evaluate(ast.parse(expression, mode="eval").body)


def is_calculation(command):

    command = command.lower().strip()

    for prefix in [
        "what is", "what's", "calculate",
        "solve", "compute", "how much is"
    ]:

        if command.startswith(prefix):
            command = command[len(prefix):].strip()
            break

    if any(symbol in command for symbol in ["+", "*", "/", "%", "^"]):
        return True

    if "-" in command and any(char.isdigit() for char in command):
        return True

    math_words = [
        "plus", "minus", "times", "into",
        "multiplied by", "divided by"
    ]

    return any(word in command for word in math_words)


# ---------------- WIKIPEDIA SEARCH ----------------

def wikipedia_answer(question):

    try:

        search_url = "https://en.wikipedia.org/w/api.php"

        params = {
            "action": "query",
            "list": "search",
            "srsearch": question,
            "format": "json"
        }

        response = requests.get(
            search_url,
            params=params,
            headers={"User-Agent": "NOVA-Assistant/1.0"},
            timeout=5
        )

        response.raise_for_status()

        results = response.json()["query"]["search"]

        if not results:
            return None

        title = results[0]["title"]

        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "titles": title,
            "format": "json"
        }

        response = requests.get(
            search_url,
            params=params,
            headers={"User-Agent": "NOVA-Assistant/1.0"},
            timeout=5
        )

        response.raise_for_status()

        pages = response.json()["query"]["pages"]

        for page in pages.values():

            answer = page.get("extract", "")

            if answer:
                return answer[:1200]

        return None

    except Exception as e:

        print("Wikipedia error:", e)
        return None


# ---------------- MAIN ASSISTANT ----------------

def get_response(user_input, chat_history=None):

    command = user_input.lower().strip()

    if not command:
        return "Please enter something."

    # Greetings
    if command in [
        "hi", "hii", "hiii", "hello",
        "hey", "hey nova", "good morning",
        "good evening", "good afternoon"
    ]:
        return "Hello! I am NOVA. How can I help you?"

    # Assistant name
    elif "your name" in command:
        return "My name is NOVA, your virtual assistant."

    # Reminders
    elif (
        command.startswith("remind me to ")
        or command in [
            "show my reminders", "show reminders",
            "my reminders", "list reminders"
        ]
        or command.startswith("delete reminder ")
        or command.startswith("complete reminder ")
    ):
        return manage_reminders(command)

    # Tasks
    elif (
        command.startswith("add task ")
        or command in [
            "show my tasks", "show tasks",
            "my tasks", "list tasks"
        ]
        or command.startswith("remove task ")
        or command.startswith("complete task ")
        or command == "clear all tasks"
    ):
        return manage_tasks(command)

    # Calculator
    elif is_calculation(command):

        try:
            result = calculate(command)
            return "The answer is " + str(result)

        except Exception as e:
            print("Calculator error:", repr(e))
            return "Sorry, I couldn't calculate that. Please check your expression."

    # Date and time
    elif "time" in command and (
        "date" in command or "today" in command
    ):

        return datetime.now().strftime(
            "Today's date is %d %B %Y.\nThe time is %I:%M %p."
        )

    elif "time" in command:
        return datetime.now().strftime("The time is %I:%M %p")

    elif "date" in command or "today" in command:
        return datetime.now().strftime("Today's date is %d %B %Y")

    # YouTube
    elif "youtube" in command:

        query = command.replace("youtube", "").replace("open", "").strip()

        if query:

            url = (
                "https://www.youtube.com/results?search_query="
                + urllib.parse.quote_plus(query)
            )

            webbrowser.open(url)
            return "Searching YouTube for " + query

        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."

    # Google
    elif command.startswith("open google"):

        webbrowser.open("https://www.google.com")
        return "Opening Google."

    # Google search
    elif command.startswith("search"):

        query = command.replace("search", "", 1).strip()

        if query:

            url = (
                "https://www.google.com/search?q="
                + urllib.parse.quote_plus(query)
            )

            webbrowser.open(url)
            return "Searching Google for " + query

        return "Please tell me what to search."

    # Goodbye
    elif command in ["bye", "goodbye"]:
        return "Goodbye! Have a nice day."

    # Wikipedia lookup first; use the LLM for general questions and conversation.
    else:
        answer = wikipedia_answer(user_input)
        if answer:
            return answer
        return ask_llm(user_input, chat_history)
