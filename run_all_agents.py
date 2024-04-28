import subprocess
import time


def run_script_in_new_terminal(script_name):
    """Run a Python script in a new terminal window."""
    try:
        # Command to open a new terminal window and run the script
        terminal_command = ['gnome-terminal', '--', 'bash', '-c', f'python {script_name}; exec bash']
        # Start the new terminal and run the script
        subprocess.Popen(terminal_command)
        print(f"Running {script_name} in a new terminal.")
    except Exception as e:
        print(f"Failed to start {script_name} in a new terminal: {e}")

def main():
    # List of scripts to run
    scripts = ['socket_env.py', "socket_agent.py"]
    
    # Run each script in a new terminal window
    for script in scripts:
        run_script_in_new_terminal(script)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
