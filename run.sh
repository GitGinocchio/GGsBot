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

        # Pull updates
        git reset --hard HEAD
        git clean -fd
        git pull
        git pull
        if [ $? -ne 0 ]; then
            echo "Error updating repository"
            exit 1
        else
            echo "Repository updated successfully"
        fi
    else
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

            credentials="https://$username:$password@github.com"
            echo $credentials > .git-credentials
            echo "Created .git-credentials"

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

run_main_script() {
    # Run the main script if it exists
    if [ -f "$MAIN_SCRIPT" ]; then
        echo "Running $MAIN_SCRIPT..."
        python $MAIN_SCRIPT
        if [ $? -ne 0 ]; then
            echo "Error running $MAIN_SCRIPT"
            exit 1
        else
            echo "$MAIN_SCRIPT executed successfully"
        fi
    else
        echo "$MAIN_SCRIPT not found"
        exit 1
    fi
}

main() {
    echo "Starting setup..."
    clone_or_update_repo
    install_requirements
    run_main_script
    echo "Setup completed successfully"
}

main
