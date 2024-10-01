import os
import subprocess
from http.client import HTTPException

from fastapi.responses import HTMLResponse

def install_requirements():
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        try:
            subprocess.check_call(["pip", "install", "-r", requirements_file])
            print(f"Requirements from {requirements_file} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while installing requirements: {e}")
            raise HTTPException(status_code=500, detail="Could not install requirements.")
    else:
        print(f"{requirements_file} not found.")

# install_requirements()

