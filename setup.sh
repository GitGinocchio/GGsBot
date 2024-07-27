#!/bin/bash

# Constants
REPO_URL="GitGinocchio/GGsBot"
MAIN_SCRIPT="main.py"

clone_or_update_repo() {
    # Check if .git directory exists in the current directory
    if [ -d ".git" ]; then
        # Check if .git-credentials exists in the current directory
        if [ ! -f ".git-credentials" ]; then
            read -p "Enter your repository username: " username
            read -s -p "Enter your repository password/token: " password
            echo

            credentials="https://$username:$password@github.com"

            echo $credentials > .git-credentials
            echo "Created .git-credentials"
        fi

        # Set Git config for pull.rebase to false
        git config pull.rebase false
        if [ $? -ne 0 ]; then
            echo "Error setting git config"
            exit 1
        else
            echo "Git pull rebase strategy set to false"
        fi

        # Pull updates if .git-credentials exists
        git pull
        if [ $? -ne 0 ]; then
            echo "Error updating repository"
            exit 1
        else
            echo "Repository updated successfully"
        fi
    else
        # Clone repository with credentials included in URL
        read -p "Enter your repository username: " username
        read -s -p "Enter your repository password/token: " password
        echo

        clone_url="https://$username:$password@github.com/$REPO_URL"
        git clone $clone_url .
        if [ $? -ne 0 ]; then
            echo "Error cloning repository"
            exit 1
        else
            echo "Repository cloned successfully"

            # Create .git-credentials file
            credentials="https://$username:$password@github.com"
            echo $credentials > .git-credentials
            echo "Created .git-credentials"

            # Set Git config for pull.rebase to false
            git config pull.rebase false
            if [ $? -ne 0 ]; then
                echo "Error setting git config"
                exit 1
            else
                echo "Git pull rebase strategy set to false"
            fi
        fi
    fi
}

install_requirements() {
    # Check if REQUIREMENTS_FILE exists in the current directory
    if [ -f "requirements.txt" ]; then
        echo "Installing requirements..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "Error installing requirements"
            exit 1
        else
            echo "Requirements installed successfully"
        fi
    else
        echo "Requirements file requirements.txt not found"
    fi
}

main() {
    echo "Starting setup..."
    clone_or_update_repo
    install_requirements
    echo "Setup completed successfully"
}

main
