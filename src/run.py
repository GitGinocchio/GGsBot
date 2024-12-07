import subprocess
import os

# Define the path to the shell script
script_path = "./src/run.sh"

def run_shell_script():
    """Esegue il file run.sh."""
    if os.path.isfile(script_path):
        try:
            # Esegui il file run.sh
            result = subprocess.run(["bash", script_path], check=True)
            print(f"{script_path} eseguito con successo!")
        except subprocess.CalledProcessError as e:
            print(f"Errore durante l'esecuzione di {script_path}: {e}")
    else:
        print(f"File {script_path} non trovato.")

if __name__ == "__main__":
    run_shell_script()