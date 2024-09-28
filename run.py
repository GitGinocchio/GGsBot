import os
import subprocess
import getpass
import sys

# Constants
REPO_URL = "GitGinocchio/GGsBot"
MAIN_SCRIPT = "main.py"

def clone_or_update_repo():
    """Clona o aggiorna il repository."""
    if os.path.isdir(".git"):
        # Check if .git-credentials exists in the current directory
        if not os.path.isfile(".git-credentials"):
            username = input("Enter your repository username: ")
            password = getpass.getpass("Enter your repository password/token: ")

            credentials = f"https://{username}:{password}@github.com"
            with open(".git-credentials", "w") as cred_file:
                cred_file.write(credentials)
            print("Created .git-credentials")

        # Set Git config for pull.rebase to false
        try:
            subprocess.check_call(["git", "config", "pull.rebase", "false"])
            print("Git pull rebase strategy set to false")
        except subprocess.CalledProcessError:
            print("Error setting git config")
            sys.exit(1)

        # Pull updates
        try:
            subprocess.check_call(["git", "pull"])
            print("Repository updated successfully")
        except subprocess.CalledProcessError:
            print("Error updating repository")
            sys.exit(1)
    else:
        username = input("Enter your repository username: ")
        password = getpass.getpass("Enter your repository password/token: ")

        clone_url = f"https://{username}:{password}@github.com/{REPO_URL}"
        try:
            subprocess.check_call(["git", "clone", clone_url, "."])
            print("Repository cloned successfully")

            credentials = f"https://{username}:{password}@github.com"
            with open(".git-credentials", "w") as cred_file:
                cred_file.write(credentials)
            print("Created .git-credentials")

            subprocess.check_call(["git", "config", "pull.rebase", "false"])
            print("Git pull rebase strategy set to false")
        except subprocess.CalledProcessError:
            print("Error cloning repository")
            sys.exit(1)

def install_requirements():
    """Installa i pacchetti dalla requirements.txt."""
    if os.path.isfile("requirements.txt"):
        print("Installing requirements...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Requirements installed successfully")
        except subprocess.CalledProcessError:
            print("Error installing requirements")
            sys.exit(1)
    else:
        print("Requirements file requirements.txt not found")

def run_main_script():
    """Esegue lo script principale."""
    if os.path.isfile(MAIN_SCRIPT):
        print(f"Running {MAIN_SCRIPT}...")
        try:
            subprocess.Popen([sys.executable, MAIN_SCRIPT])
            print(f"{MAIN_SCRIPT} executed successfully")
        except subprocess.CalledProcessError:
            print(f"Error running {MAIN_SCRIPT}")
            sys.exit(1)
    else:
        print(f"{MAIN_SCRIPT} not found")
        sys.exit(1)

def main():
    """Funzione principale per gestire il setup."""
    print("Starting setup...")
    clone_or_update_repo()
    install_requirements()
    run_main_script()
    print("Setup completed successfully")

if __name__ == "__main__":
    main()

