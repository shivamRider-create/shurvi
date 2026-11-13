
import os
import re
import json
import shutil
import webbrowser
import asyncio
import subprocess
import requests
import sounddevice as sd
import speech_recognition as sr
import edge_tts

from pathlib import Path
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv
from playsound3 import playsound
from google import genai
from google.genai import types
from tavily import TavilyClient


# =========================================================
# SHRUVI 3.0 - CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

USER_NAME = "Shivam"
ASSISTANT_NAME = "SHRUVI"
CREATOR_NAME = "Shivam"

MODEL_NAME = "gemini-3.5-flash-lite"
VOICE = "en-IN-NeerjaNeural"

DEFAULT_WEATHER_LOCATION = "Bengaluru"

MEMORY_FILE = BASE_DIR / "memory.json"
AUDIO_FILE = BASE_DIR / "shruvi_voice.mp3"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from .env")


# =========================================================
# AI CLIENTS
# =========================================================

client = genai.Client(api_key=GEMINI_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

SYSTEM_INSTRUCTION = f"""
You are SHRUVI, a personal AI voice assistant.

IDENTITY:
- Shivam created and developed you.
- Shivam is your creator.
- Google Gemini powers your AI responses.
- Never claim Google created you.

PERSONALITY:
- Friendly, intelligent and respectful.
- Speak naturally and concisely.
- Help with studies, programming, technology,
  motorcycles and everyday questions.
- Never claim to have performed an action you did not perform.
- Never claim to have live internet results unless
  search results are provided.

The user's name is {USER_NAME}.
"""

chat = client.chats.create(
    model=MODEL_NAME,
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION
    )
)


# =========================================================
# GLOBAL VARIABLES
# =========================================================

last_action = None
last_search_query = None
last_weather_city = DEFAULT_WEATHER_LOCATION


# =========================================================
# VOICE SYSTEM
# =========================================================

async def generate_voice(text):
    communicator = edge_tts.Communicate(text, VOICE)
    await communicator.save(str(AUDIO_FILE))


def speak(text):
    print(f"\n{ASSISTANT_NAME}: {text}\n")

    try:
        asyncio.run(generate_voice(text))
        playsound(str(AUDIO_FILE))
    except Exception as error:
        print("Voice error:", error)


# =========================================================
# MICROPHONE SYSTEM
# =========================================================

def listen():
    recognizer = sr.Recognizer()

    print("\nListening...")

    try:
        audio_data = sd.rec(
            int(7 * 16000),
            samplerate=16000,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        audio = sr.AudioData(
            audio_data.tobytes(),
            16000,
            2
        )

        try:
            command = recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            print("You:", command)
            return command.lower().strip()

        except sr.UnknownValueError:
            print("SHRUVI: I couldn't understand that.")
            return ""

        except sr.RequestError as error:
            print("Speech recognition error:", error)
            return ""

    except Exception as error:
        print("Microphone error:", error)
        return ""


# =========================================================
# MEMORY SYSTEM
# =========================================================

def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            return data.get("facts", [])

        except (json.JSONDecodeError, OSError):
            return []

    return []


def save_memory(facts):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump({"facts": facts}, file, indent=4)


def remember_fact(fact):
    facts = load_memory()

    if fact not in facts:
        facts.append(fact)
        save_memory(facts)
        return "I'll remember that."

    return "I already remember that."


def recall_memory():
    facts = load_memory()

    if not facts:
        return "I don't have anything saved in my memory yet."

    return "Here is what I remember: " + ". ".join(facts)


def forget_memory(target):
    facts = load_memory()

    remaining = [
        fact for fact in facts
        if target.lower() not in fact.lower()
    ]

    if len(remaining) == len(facts):
        return "I couldn't find that information in my memory."

    save_memory(remaining)
    return "I have removed that information from my memory."


def clear_memory():
    save_memory([])
    return "My saved memory has been cleared."


# =========================================================
# GEMINI RESPONSE EXTRACTION
# =========================================================

def extract_response_text(response):
    try:
        collected_text = []

        for candidate in response.candidates or []:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        collected_text.append(part.text)

        return "\n".join(collected_text).strip()

    except Exception as error:
        print("Response extraction error:", error)
        return ""


# =========================================================
# GEMINI AI
# =========================================================

def ask_gemini(prompt):
    try:
        facts = load_memory()

        memory_context = "\n".join(
            f"- {fact}" for fact in facts
        )

        full_prompt = f"""
        Saved information about the user:
        {memory_context}

        User's message:
        {prompt}

        You are SHRUVI, created by Shivam.
        Google Gemini powers your intelligence.
        Answer naturally and briefly.
        """

        response = chat.send_message(message=full_prompt)
        answer = extract_response_text(response)

        if answer:
            return answer

        return "I couldn't generate a response. Please try again."

    except Exception as error:
        print("Gemini error:", error)

        if "503" in str(error) or "UNAVAILABLE" in str(error):
            return "My AI service is temporarily busy. Please try again shortly."

        return "I'm having trouble connecting to my AI service."


# =========================================================
# DYNAMIC INTERNET SEARCH - TAVILY
# =========================================================

def search_internet(query):
    global last_search_query

    query = query.strip()

    if not query:
        return "Please tell me what you want me to search for."

    print(f"\nSHRUVI is searching for: {query}")

    try:
        topic = (
            "news"
            if any(
                word in query.lower()
                for word in ["news", "latest", "today", "recent"]
            )
            else "general"
        )

        response = tavily_client.search(
            query=query,
            topic=topic,
            search_depth="basic",
            max_results=5
        )

        results = response.get("results", [])

        if not results:
            return "I couldn't find any useful search results."

        search_context = []

        print("\n========== SEARCH SOURCES ==========")

        for index, result in enumerate(results, start=1):
            title = result.get("title", "Untitled")
            content = result.get("content", "")
            url = result.get("url", "")

            print(f"{index}. {title}")
            print(url)

            search_context.append(
                f"Title: {title}\n"
                f"Information: {content}\n"
                f"Source: {url}"
            )

        print("====================================\n")

        summary_prompt = f"""
        The user asked:
        {query}

        These are live internet search results:
        {chr(10).join(search_context)}

        Give a useful and accurate summary answering the user's question.

        Rules:
        - Use the supplied results.
        - Do not invent information.
        - Mention uncertainty if sources disagree.
        - Keep the answer concise for voice.
        - Do not claim to have personally visited the websites.
        """

        answer = ask_gemini(summary_prompt)
        last_search_query = query

        return answer

    except Exception as error:
        print("Tavily error:", error)
        return "I couldn't retrieve live search results. Please check your internet connection and Tavily API key."


# =========================================================
# GOOGLE / CHROME SEARCH
# =========================================================

def find_chrome():
    possible_paths = [
        shutil.which("chrome"),
        os.path.expandvars(
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
        ),
        os.path.expandvars(
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
        ),
        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    ]

    for path in possible_paths:
        if path and os.path.isfile(path):
            return path

    return None


def search_in_chrome(query):
    url = "https://www.google.com/search?q=" + quote(query)
    chrome_path = find_chrome()

    try:
        if chrome_path:
            subprocess.Popen([chrome_path, url])
        else:
            webbrowser.open(url)

        return f"Searching Google for {query}."

    except Exception as error:
        print("Chrome search error:", error)
        return "I couldn't open the search in your browser."


# =========================================================
# WEATHER - OPEN METEO
# =========================================================

def get_weather(city=DEFAULT_WEATHER_LOCATION):
    global last_weather_city

    print(f"\nFetching weather for {city}...")

    try:
        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=15
        )

        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return f"I couldn't find the city {city}."

        place = geo_data["results"][0]

        latitude = place["latitude"]
        longitude = place["longitude"]

        city_name = place["name"]
        country = place.get("country", "")

        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "timezone": "auto"
            },
            timeout=15
        )

        weather_response.raise_for_status()

        data = weather_response.json()
        current = data["current"]
        daily = data["daily"]

        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snowfall",
            73: "Moderate snowfall",
            75: "Heavy snowfall",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm"
        }

        condition = weather_codes.get(
            current["weather_code"],
            "Unknown conditions"
        )

        last_weather_city = city_name

        return (
            f"Here is the current weather for {city_name}, {country}. "
            f"The temperature is {current['temperature_2m']} degrees Celsius. "
            f"It feels like {current['apparent_temperature']} degrees. "
            f"Conditions are {condition}. "
            f"Humidity is {current['relative_humidity_2m']} percent. "
            f"Wind speed is {current['wind_speed_10m']} kilometres per hour. "
            f"Today's high is {daily['temperature_2m_max'][0]} degrees "
            f"and low is {daily['temperature_2m_min'][0]} degrees. "
            f"Maximum chance of rain is "
            f"{daily['precipitation_probability_max'][0]} percent."
        )

    except Exception as error:
        print("Weather error:", error)
        return "I couldn't retrieve the weather right now."


# =========================================================
# DATE AND TIME
# =========================================================

def get_current_date():
    return datetime.now().strftime(
        "Today is %A, %d %B %Y."
    )


def get_current_time():
    return datetime.now().strftime(
        "The current time is %I:%M %p."
    )


# =========================================================
# APPLICATION CONTROL
# =========================================================

def open_application(app_name):
    app_name = app_name.lower().strip()

    if app_name in ["calculator", "calc"]:
        os.startfile("calc.exe")
        return "Opening calculator."

    elif app_name in ["notepad", "notes"]:
        os.startfile("notepad.exe")
        return "Opening Notepad."

    elif app_name in ["chrome", "google chrome"]:
        chrome_path = find_chrome()

        if chrome_path:
            os.startfile(chrome_path)
            return "Opening Google Chrome."

        return "I couldn't find Google Chrome."

    elif app_name in ["vscode", "vs code", "visual studio code"]:
        if shutil.which("code"):
            subprocess.Popen(["code"])
            return "Opening Visual Studio Code."

        return "I couldn't find Visual Studio Code."

    elif app_name == "youtube":
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."

    elif app_name == "google":
        webbrowser.open("https://www.google.com")
        return "Opening Google."

    elif app_name == "gmail":
        webbrowser.open("https://mail.google.com")
        return "Opening Gmail."

    elif app_name in ["whatsapp", "whats app"]:
        whatsapp_paths = [
            os.path.expandvars(
                r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles%\WhatsApp\WhatsApp.exe"
            )
        ]

        for path in whatsapp_paths:
            if os.path.isfile(path):
                os.startfile(path)
                return "Opening WhatsApp desktop application."

        webbrowser.open("https://web.whatsapp.com")
        return "Opening WhatsApp Web."

    elif app_name == "telegram":
        webbrowser.open("https://web.telegram.org")
        return "Opening Telegram Web."

    elif app_name == "spotify":
        webbrowser.open("https://open.spotify.com")
        return "Opening Spotify."

    elif app_name == "discord":
        webbrowser.open("https://discord.com/app")
        return "Opening Discord."

    return "That application is not in my allowed application list."


# =========================================================
# COMMAND PROCESSING
# =========================================================

def process_command(command):
    global last_action
    global last_search_query
    global last_weather_city

    command = command.lower().strip()

    # Remove common conversational starter words
    command = re.sub(
        r"^(hey|okay|ok|and|also|then)\s+",
        "",
        command
    ).strip()

    command = re.sub(r"\s+", " ", command)

    if not command:
        return True

    # -----------------------------------------------------
    # GOODBYE
    # -----------------------------------------------------

    if command in [
        "goodbye", "good bye", "bye", "bye bye",
        "exit", "quit", "shut down"
    ]:
        speak("Goodbye! Talk to you soon.")
        return False

    # -----------------------------------------------------
    # IDENTITY
    # -----------------------------------------------------

    if re.search(
        r"\bwho (?:created|made|developed) you\b",
        command
    ):
        speak(
            "I was created and developed by Shivam. "
            "He is my creator and developer."
        )
        return True

    if re.search(
        r"\bwho (?:powers|provides) your intelligence\b",
        command
    ):
        speak("My intelligence is powered by Google Gemini.")
        return True

    if command in [
        "who are you",
        "what is your name",
        "what's your name"
    ]:
        speak(
            "I am SHRUVI, your personal AI assistant, "
            "created by Shivam."
        )
        return True

    # -----------------------------------------------------
    # FOLLOW-UP SEARCH
    # -----------------------------------------------------

    if command in [
        "go ahead", "do it", "search it",
        "continue", "yes"
    ]:
        if last_search_query:
            speak(search_internet(last_search_query))
        else:
            speak(
                "What would you like me to search for?"
            )

        last_action = "search"
        return True

    # -----------------------------------------------------
    # TRY AGAIN
    # -----------------------------------------------------

    if command in ["try again", "check again", "repeat that"]:

        if last_action == "time":
            speak(get_current_time())

        elif last_action == "date":
            speak(get_current_date())

        elif last_action == "weather":
            speak(get_weather(last_weather_city))

        elif last_action == "search" and last_search_query:
            speak(search_internet(last_search_query))

        else:
            speak("What would you like me to try again?")

        return True

    # -----------------------------------------------------
    # MEMORY
    # -----------------------------------------------------

    if command.startswith("remember that "):
        fact = command.replace(
            "remember that ", "", 1
        ).strip()

        speak(remember_fact(fact))
        return True

    if command in [
        "what do you remember",
        "what do you remember about me",
        "show my memory",
        "recall my memory"
    ]:
        speak(recall_memory())
        return True

    if command.startswith("forget that "):
        target = command.replace(
            "forget that ", "", 1
        ).strip()

        speak(forget_memory(target))
        return True

    if command in ["forget everything", "clear my memory"]:

        speak(
            "Are you sure you want to clear all saved memories?"
        )

        confirmation = listen()

        if confirmation and confirmation in [
            "yes", "confirm", "clear it", "yes clear it"
        ]:
            speak(clear_memory())
        else:
            speak("Okay, I won't clear your memory.")

        return True

    # -----------------------------------------------------
    # CHROME + ANY SEARCH QUERY
    # -----------------------------------------------------

    chrome_match = re.match(
        r"^open\s+(?:google\s+)?chrome\s+"
        r"(?:and\s+)?"
        r"(?:search(?:\s+(?:for|about))?|"
        r"type(?:\s+of)?|look\s+up)\s+(.+)$",
        command
    )

    if chrome_match:
        query = chrome_match.group(1).strip()

        speak(search_in_chrome(query))
        last_action = "open"
        return True

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    date_patterns = [
        r"^what is the date$",
        r"^what's the date$",
        r"^what is today's date$",
        r"^what's today's date$",
        r"^what's the date today$",
        r"^what is the date today$",
        r"^what date is it today$",
        r"^today's date$",
        r"^date today$",
        r"^tell me the date$"
    ]

    if any(re.match(pattern, command) for pattern in date_patterns):
        last_action = "date"
        speak(get_current_date())
        return True

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    time_patterns = [
        r"^what time is it$",
        r"^what time is now$",
        r"^what time now$",
        r"^what's the time$",
        r"^what is the time$",
        r"^what's time now$",
        r"^what's the time now$",
        r"^what is the time now$",
        r"^tell me the time$",
        r"^current time$",
        r"^time now$",
        r"^what is time now$"
    ]

    if any(re.match(pattern, command) for pattern in time_patterns):
        last_action = "time"
        speak(get_current_time())
        return True

    # -----------------------------------------------------
    # WEATHER
    # -----------------------------------------------------

    if "weather" in command or "temperature" in command:

        city_match = re.search(
            r"(?:weather|temperature)\s+"
            r"(?:in|of|for)\s+(.+)",
            command
        )

        city = (
            city_match.group(1).strip()
            if city_match
            else DEFAULT_WEATHER_LOCATION
        )

        last_action = "weather"
        speak(get_weather(city))
        return True

    # -----------------------------------------------------
    # GOOGLE SEARCH
    # -----------------------------------------------------

    if command.startswith("google search for "):
        query = command.replace(
            "google search for ", "", 1
        ).strip()

        speak(search_in_chrome(query))
        last_action = "open"
        return True

    # -----------------------------------------------------
    # OPEN APPLICATIONS
    # -----------------------------------------------------

    if command.startswith(("open ", "launch ")):

        app_name = command.split(" ", 1)[1].strip()

        speak(open_application(app_name))
        last_action = "open"
        return True

    # -----------------------------------------------------
    # DYNAMIC INTERNET SEARCH
    # -----------------------------------------------------

    search_patterns = [
        r"^search the internet for\s+(.+)$",
        r"^search internet for\s+(.+)$",
        r"^search the web for\s+(.+)$",
        r"^search the web\s+(.+)$",
        r"^search for\s+(.+)$",
        r"^search about\s+(.+)$",
        r"^search\s+(.+)$",
        r"^look up\s+(.+)$",
        r"^find information about\s+(.+)$",
        r"^find information on\s+(.+)$"
    ]

    for pattern in search_patterns:

        match = re.match(pattern, command)

        if match:
            query = match.group(1).strip()

            if query:
                last_search_query = query
                last_action = "search"

                speak(search_internet(query))
                return True

    # -----------------------------------------------------
    # NORMAL GEMINI CONVERSATION
    # -----------------------------------------------------

    answer = ask_gemini(command)

    speak(answer)

    last_action = "chat"

    return True


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    speak(
        f"Hello {USER_NAME}! I am SHRUVI. "
        "Your personal assistant is ready. "
        "How can I help you?"
    )

    try:

        while True:

            command = listen()

            if not command:
                continue

            should_continue = process_command(command)

            if not should_continue:
                break

    except KeyboardInterrupt:
        print("\nSHRUVI stopped.")

    finally:
        client.close()


# =========================================================
# START SHRUVI
# =========================================================

if __name__ == "__main__":
    main()
