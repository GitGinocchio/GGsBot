#!/bin/bash

# Constants
REPO_URL="https://github.com/GitGinocchio/GGsBot.git"
REPO_DIR="GGsBot"
MAIN_SCRIPT="main.py"

# Function to prompt for username and password/token
prompt_credentials() {
  read -p "Enter your repository username: " USERNAME
  read -s -p "Enter your repository password/token: " PASSWORD
  echo ""
}

# Function to clone or update the repository
clone_or_update_repo() {
  # Check if REPO_DIR exists, create it if not
  if [ ! -d "$REPO_DIR" ]; then
    mkdir -p "$REPO_DIR"
  fi

  # Check if .git directory exists in REPO_DIR
  if [ -d "$REPO_DIR/.git" ]; then
    # Check if .git-credentials exists in REPO_DIR
    if [ ! -f "$REPO_DIR/.git-credentials" ]; then
      prompt_credentials
      CREDENTIALS="https://$USERNAME:$PASSWORD@github.com"
      echo "$CREDENTIALS" > "$REPO_DIR/.git-credentials"
      echo "Created .git-credentials"
    fi

    # Set Git config for pull.rebase to false
    git -C "$REPO_DIR" config pull.rebase false
    if [ $? -eq 0 ]; then
      echo "Git pull rebase strategy set to false"
    else
      echo "Error setting git config"
    fi

    # Pull updates if .git-credentials exists
    git -C "$REPO_DIR" pull
    if [ $? -eq 0 ]; then
      echo "Repository updated successfully"
    else
      echo "Error updating repository"
    fi
  else
    # Clone repository with credentials included in URL
    prompt_credentials
    CLONE_URL="https://$USERNAME:$PASSWORD@github.com/$REPO_URL"
    git clone "$CLONE_URL" "$REPO_DIR"
    if [ $? -eq 0 ]; then
      echo "Repository cloned successfully"
      CREDENTIALS="https://$USERNAME:$PASSWORD@github.com"
      echo "$CREDENTIALS" > "$REPO_DIR/.git-credentials"
      echo "Created .git-credentials"
      git -C "$REPO_DIR" config pull.rebase false
      if [ $? -eq 0 ]; then
        echo "Git pull rebase strategy set to false"
      else
        echo "Error setting git config"
      fi
    else
      echo "Error cloning repository"
    fi
  fi
}

# Function to install requirements
install_requirements() {
  REQUIREMENTS_FILE="$REPO_DIR/requirements.txt"
  if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing requirements..."
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -eq 0 ]; then
      echo "Requirements installed successfully"
    else
      echo "Error installing requirements"
    fi
  else
    echo "Requirements file requirements.txt not found in $REPO_DIR"
  fi
}

# Main function
main() {
  echo "Starting setup..."
  clone_or_update_repo
  install_requirements
  echo "Setup completed successfully"
}

# Execute the main function
main
