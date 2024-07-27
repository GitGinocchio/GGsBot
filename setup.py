import subprocess
import getpass
import sys
import os

# Constants
REPO_URL = "GitGinocchio/GGsBot"
MAIN_SCRIPT = "main.py"

def clone_or_update_repo():
    # Check if .git directory exists in the current directory
    git_dir = os.path.join(".git")
    if os.path.exists(git_dir):
        # Check if .git-credentials exists in the current directory
        credentials_file = os.path.join(".git-credentials")
        if not os.path.exists(credentials_file):
            print("Enter your repository username: ")
            username = input()
            print("Enter your repository password/token: ")
            password = getpass.getpass()

            credentials = f"https://{username}:{password}@github.com\n"

            with open(credentials_file, 'w') as file:
                file.write(credentials)
            print("Created .git-credentials")

        # Set Git config for pull.rebase to false
        try:
            subprocess.run(["git", "config", "pull.rebase", "false"], check=True)
            print("Git pull rebase strategy set to false")
        except subprocess.CalledProcessError as e:
            print(f"Error setting git config: {e}")

        # Pull updates if .git-credentials exists
        try:
            subprocess.run(["git", "pull"], check=True)
            print("Repository updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error updating repository: {e}")
    else:
        # Clone repository with credentials included in URL
        print("Enter your repository username: ")
        username = input()
        print("Enter your repository password/token: ")
        password = getpass.getpass()

        clone_url = f"https://{username}:{password}@github.com/{REPO_URL}"
        clone_command = f"git clone {clone_url} ."
        try:
            subprocess.run(clone_command, shell=True, check=True)
            print("Repository cloned successfully")

            # Create .git-credentials file
            credentials = f"https://{username}:{password}@github.com\n"
            credentials_file = os.path.join(".git-credentials")
            with open(credentials_file, 'w') as file:
                file.write(credentials)
            print("Created .git-credentials")

            # Set Git config for pull.rebase to false
            try:
                subprocess.run(["git", "config", "pull.rebase", "false"], check=True)
                print("Git pull rebase strategy set to false")
            except subprocess.CalledProcessError as e:
                print(f"Error setting git config: {e}")

        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")

def install_requirements():
    # Check if REQUIREMENTS_FILE exists in the current directory
    requirements_file_path = "requirements.txt"
    if os.path.exists(requirements_file_path):
        print("Installing requirements...")
        try:
            subprocess.run(["pip", "install", "-r", requirements_file_path], check=True)
            print("Requirements installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
    else:
        print(f"Requirements file requirements.txt not found")

def main():
    print("Starting setup...")
    clone_or_update_repo()
    install_requirements()
    print("Setup completed successfully")

if __name__ == "__main__":
    main()
