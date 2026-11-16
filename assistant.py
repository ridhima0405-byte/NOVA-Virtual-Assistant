
import os
import ast
import operator
import webbrowser
from datetime import datetime
import requests

import pyttsx3
from dotenv import load_dotenv

load_dotenv()

# Text-to-speech
def speak(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("Voice error:", e)


# Safe calculator

def calculate(expression):
    expression = expression.lower()

    # Convert spoken multiplication and division
    expression = expression.replace("into", "*")
    expression = expression.replace("multiplied by", "*")
    expression = expression.replace("times", "*")
    expression = expression.replace("x", "*")
    expression = expression.replace("divided by", "/")
    expression = expression.replace("plus", "+")
    expression = expression.replace("minus", "-")

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
            return operations[type(node.op)](
                evaluate(node.left),
                evaluate(node.right)
            )

        raise ValueError("Invalid calculation")

    return evaluate(ast.parse(expression, mode="eval").body)


# Main assistant

def wikipedia_answer(question):
    try:
        search_url = "https://en.wikipedia.org/w/api.php"

        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": question,
            "format": "json"
        }

        response = requests.get(
            search_url,
            params=search_params,
            headers={"User-Agent": "NOVA-Assistant/1.0"},
            timeout=10
        )

        response.raise_for_status()
        results = response.json()["query"]["search"]

        if not results:
            return None

        title = results[0]["title"]

        extract_params = {
            "action": "query",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "titles": title,
            "format": "json"
        }

        response = requests.get(
            search_url,
            params=extract_params,
            headers={"User-Agent": "NOVA-Assistant/1.0"},
            timeout=10
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



def get_response(user_input):
    import urllib.parse

    command = user_input.lower().strip()

    if command in ["hi", "hello", "hey"]:
        return "Hello! I am NOVA. How can I help you?"

    elif "your name" in command:
        return "My name is NOVA, your virtual assistant."

    elif "time" in command:
        return datetime.now().strftime("The time is %I:%M %p")

    elif "date" in command or "today" in command:
        return datetime.now().strftime("Today's date is %d %B %Y")

    elif "youtube" in command:
        query = command.replace("youtube", "").strip()

        if query and query != "open":
            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
            webbrowser.open(url)
            return "Searching YouTube for " + query

        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."

    elif command.startswith("open google"):
        webbrowser.open("https://www.google.com")
        return "Opening Google."

    elif command.startswith("search"):
        query = command.replace("search", "", 1).strip()

        if query:
            url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
            webbrowser.open(url)
            return "Searching Google for " + query

        return "Please tell me what to search."

    elif command.startswith("calculate"):
        try:
            expression = command.replace("calculate", "", 1).strip()
            return "The answer is " + str(calculate(expression))
        except Exception:
            return "Sorry, invalid calculation."

    elif command in ["bye", "goodbye"]:
        return "Goodbye! Have a nice day."

    else:
        answer = wikipedia_answer(user_input)

        if answer:
            return answer

        return "Sorry, I couldn't find an answer. Try asking another question."

