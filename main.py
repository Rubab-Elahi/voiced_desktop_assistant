import os
import webbrowser
import subprocess
import speech_recognition as sr
import pyttsx3
import shutil
import glob
import dotenv

dotenv.load_dotenv()

from agents import Agent, Runner, function_tool

# =========================
# CONFIG
# =========================
API_KEY= os.getenv("OPENAI_API_KEY")



# =========================
# TEXT TO SPEECH
# =========================
tts = pyttsx3.init()
tts.setProperty("rate", 175)

def speak(text: str):
    print("Assistant:", text)
    tts.say(text)
    tts.runAndWait()

# =========================
# SPEECH TO TEXT
# =========================
recognizer = sr.Recognizer()

def listen() -> str | None:
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print("User:", text)
        return text
    except sr.UnknownValueError:
        speak("Sorry, I didn't understand.")
        return None

# =========================
# TOOLS (FUNCTION DECORATOR)
# =========================
@function_tool
def open_chrome():
    """Open Google Chrome browser. Do NOT use this if you are also calling search_google."""
    webbrowser.open("https://www.google.com")
    return "Chrome opened"

@function_tool
def search_google(query: str):
    """Search something on Google"""
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searched for {query}"

@function_tool
def open_application(app_name: str):
    """Open a desktop application"""
    if os.name == "nt":  # Windows
        subprocess.Popen(app_name)
    else:  # macOS / Linux
        subprocess.Popen(["open", "-a", app_name])
    return f"Opened {app_name}"

@function_tool
def list_directory(path: str = ".") -> str:
    """List files and directories in a given path. Defaults to current directory."""
    try:
        items = os.listdir(path)
        if not items:
            return "Directory is empty."
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@function_tool
def read_file(path: str) -> str:
    """Read the content of a file"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@function_tool
def write_to_file(path: str, content: str) -> str:
    """Write content to a file. Creates if not exists, overwrites if exists."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Typically wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

@function_tool
def delete_item(path: str) -> str:
    """Delete a file or directory"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"Deleted file {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Deleted directory {path}"
        else:
            return "Path not found"
    except Exception as e:
        return f"Error deleting item: {str(e)}"

@function_tool
def move_item(src: str, dst: str) -> str:
    """Move or rename a file or directory"""
    try:
        shutil.move(src, dst)
        return f"Moved {src} to {dst}"
    except Exception as e:
        return f"Error moving item: {str(e)}"

@function_tool
def create_directory(path: str) -> str:
    """Create a new directory"""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created directory {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@function_tool
def search_files(pattern: str, path: str = ".") -> str:
    """Search for files matching a glob pattern in a path (recursive)"""
    try:
        full_pattern = os.path.join(path, "**", pattern)
        matches = glob.glob(full_pattern, recursive=True)
        if not matches:
            return "No matches found"
        return "\n".join(matches[:20]) # Limit to 20 results
    except Exception as e:
        return f"Error searching files: {str(e)}"

# =========================
# AGENT
# =========================
assistant = Agent(
    name="Desktop Voice Assistant",
    instructions=(
        "You are a desktop voice assistant. "
        "Understand the user's voice command and call the correct tool. "
        "You can manage files, run apps, and browse the web. "
        "If the user asks to search for something, use 'search_google' ONLY. Do NOT call 'open_chrome' in addition to search. "
        "Do not explain your reasoning."
    ),
    model="gpt-4.1-mini",
    tools=[
        open_chrome,
        search_google,
        open_application,
        list_directory,
        read_file,
        write_to_file,
        delete_item,
        move_item,
        create_directory,
        search_files,
    ],
)

# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":
    speak("Desktop assistant activated")

    # Change working directory to Desktop
    try:
        desktop_path = os.path.expanduser("~/Desktop")
        os.chdir(desktop_path)
        print(f"Working directory set to: {desktop_path}")
    except Exception as e:
        print(f"Failed to set working directory: {e}")

    while True:
        user_input = listen()
        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "stop"]:
            speak("Goodbye")
            break

        result = Runner.run_sync(
            assistant,
            user_input
        )

        if result.final_output:
            speak(result.final_output)

