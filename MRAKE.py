import os
import subprocess
import json
import ollama
import pyttsx3
import ast
import torch
import logging

# Initialize logging
logging.basicConfig(filename="command_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 170)  # Adjust speaking speed

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()
    print(f"Assistant: {text}")

# Load Command Mappings from JSON
def load_command_map(file_path=r"C:\Users\krsna\Documents\jarvis\cmd_execution_dataset.json"):
    """Load predefined command mappings from JSON safely."""
    try:
        with open(file_path, "r") as file:
            commands = json.load(file)
            return {cmd["input"].lower(): cmd["output"] for cmd in commands}
    except (FileNotFoundError, json.JSONDecodeError):
        print("❌ Error: Command dataset file not found or invalid JSON format.")
        return {}

command_map = load_command_map()

# Set up the device (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Process user input with Ollama AI
def process_with_ollama(user_input):
    """Use Ollama AI to generate a system command based on user input."""
    try:
        response = ollama.chat(
            model="iio",  # Change to your Ollama model
            messages=[{"role": "user", "content": user_input}]
        )

        # Extract AI-generated command
        reply = response.get("message", {}).get("content", "").strip()

        # Stop at '###' if found (for safety)
        if "###" in reply:
            reply = reply.split("###")[0].strip()

        # Extract only valid system commands
        valid_cmd = None
        for line in reply.split("\n"):
            if "subprocess.Popen" in line or "os.system" in line or "nircmd" in line:
                valid_cmd = line.strip()
                break  # Use the first valid command found

        if not valid_cmd:
            print("⚠️ No valid command detected in AI response.")
            return None

        # Remove Python code block markers
        return valid_cmd.replace("```python", "").replace("```", "").strip()

    except Exception as e:
        print(f"❌ Error processing with Ollama: {e}")
        return None

# Secure Execution of Commands
def execute_secure_command(command_code):
    """Executes a validated system command securely after user confirmation."""
    try:
        if "subprocess.Popen" in command_code:
            cmd_str = command_code.split("subprocess.Popen(")[1].split(")")[0].strip()
            cmd_list = ast.literal_eval(cmd_str)

            if not isinstance(cmd_list, list):
                print("❌ Invalid command format detected. Skipping execution.")
                return

            # Ask for user confirmation
            confirm = input(f"⚠️ Confirm execution: {cmd_list} (Y/N)? ").strip().lower()
            if confirm == "y":
                print(f"✅ Executing: {cmd_list}")
                subprocess.Popen(cmd_list, shell=True)
                logging.info(f"Executed: {cmd_list}")
            else:
                print("❌ Execution canceled.")

        elif "os.system" in command_code:
            cmd = command_code.split("os.system(")[1].split(")")[0].strip().replace("'", "").replace('"', "")

            confirm = input(f"⚠️ Confirm execution: {cmd} (Y/N)? ").strip().lower()
            if confirm == "y":
                print(f"✅ Executing: {cmd}")
                os.system(cmd)
                logging.info(f"Executed: {cmd}")
            else:
                print("❌ Execution canceled.")

        elif "nircmd" in command_code or "nircmd.exe" in command_code:
            cmd = command_code.split("nircmd")[1].strip().replace("'", "").replace('"', "")
            full_cmd = f"nircmd{cmd}"

            confirm = input(f"⚠️ Confirm execution: {full_cmd} (Y/N)? ").strip().lower()
            if confirm == "y":
                print(f"✅ Executing: {full_cmd}")
                os.system(full_cmd)
                logging.info(f"Executed: {full_cmd}")
            else:
                print("❌ Execution canceled.")

        else:
            print("❌ Invalid command format. Skipping execution.")

    except Exception as e:
        print(f"❌ Error executing command: {e}")

# Main loop to listen for commands
while True:
    user_command = input("\nEnter command (or type 'exit' to quit): ").strip()

    if user_command.lower() == "exit":
        print("👋 Exiting the assistant. Goodbye!")
        break

    # Check if the command exists in the predefined command map
    if user_command.lower() in command_map:
        ai_command = command_map[user_command.lower()]
        execute_secure_command(ai_command)
        continue

    # Otherwise, process with AI
    ai_generated_command = process_with_ollama(user_command)
    
    if ai_generated_command:
        execute_secure_command(ai_generated_command)
