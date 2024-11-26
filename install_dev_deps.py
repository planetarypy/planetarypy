#!/usr/bin/env python
from pathlib import Path
import tomlkit
import sh
import sys

# Define packages that should be installed via pip instead of conda
PIP_PACKAGES = {'build', 'pip-tools'}

def install_dev_deps():
    # Read pyproject.toml
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path) as f:
        pyproject = tomlkit.load(f)
    
    # Get dev dependencies
    dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
    
    # Split dependencies into conda and pip packages
    conda_deps = [dep for dep in dev_deps if dep not in PIP_PACKAGES]
    pip_deps = [dep for dep in dev_deps if dep in PIP_PACKAGES]
    
    # Install conda packages
    if conda_deps:
        try:
            print(f"Installing with mamba: {' '.join(conda_deps)}")
            sh.mamba("install", "-y", "-c", "conda-forge", *conda_deps, 
                    _err=sys.stderr, _out=sys.stdout)
            print("Conda installation completed successfully!")
        except sh.ErrorReturnCode as e:
            print("Error installing conda packages!")
            print(f"Exit code: {e.exit_code}")
            print(f"Stdout: {e.stdout.decode() if e.stdout else 'No stdout'}")
            print(f"Stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
            sys.exit(1)
    
    # Install pip packages
    if pip_deps:
        try:
            print(f"\nInstalling with pip: {' '.join(pip_deps)}")
            sh.pip("install", *pip_deps, _err=sys.stderr, _out=sys.stdout)
            print("Pip installation completed successfully!")
        except sh.ErrorReturnCode as e:
            print("Error installing pip packages!")
            print(f"Exit code: {e.exit_code}")
            print(f"Stdout: {e.stdout.decode() if e.stdout else 'No stdout'}")
            print(f"Stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
            sys.exit(1)

if __name__ == "__main__":
    install_dev_deps() 