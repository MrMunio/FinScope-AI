import datetime
from langchain_core.tools import tool
import os

directory="logs"
os.makedirs(directory,exist_ok=True)
filename_1="agent_scratch_pad_1.txt"
filename_2="agent_scratch_pad_2.txt"

@tool
def scratch_pad_1(text:str ):
    """Use this tool as a scratch pad. Log internal thoughts before responding to users.ss
    Purpose: Record reasoning, analysis, and decision-making process to avoid
    premature responses. Use this to think through complex problems step-by-step."""
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create the header with timestamp
    header = f"\n--- {timestamp} ---\n"

    # Append to file (creates file if it doesn't exist)
    with open(filename_1, "a", encoding="utf-8") as file:
        file.write(header)
        file.write(text)
        file.write("\n")
    
    print(f"Agent thoughts appended to {filename_1}")

@tool
def scratch_pad_2(text:str ):
    """Use this tool as a scratch pad. Log internal thoughts before responding to users.ss
    Purpose: Record reasoning, analysis, and decision-making process to avoid
    premature responses. Use this to think through complex problems step-by-step."""
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create the header with timestamp
    header = f"\n--- {timestamp} ---\n"

    # Append to file (creates file if it doesn't exist)
    with open(filename_2, "a", encoding="utf-8") as file:
        file.write(header)
        file.write(text)
        file.write("\n")
    
    print(f"Agent thoughts appended to {filename_2}")



