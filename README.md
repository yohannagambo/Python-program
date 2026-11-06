# PyRemoteLab

PyRemoteLab is a Python-based Windows administration
and cybersecurity laboratory application.

## Features

- Administrator authentication
- Windows system information
- CPU monitoring
- RAM monitoring
- Disk monitoring
- Restricted file management
- File upload
- File download
- SQLite audit logging
- Web administrator dashboard

## Technologies

- Python
- FastAPI
- Uvicorn
- SQLite
- JavaScript
- HTML
- CSS
- psutil

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- PowerShell
- VS Code (recommended)

## Installation

Create a virtual environment:

    python -m venv venv

Activate it:

    .\venv\Scripts\Activate.ps1

Copy environment configuration:

    Copy-Item .env.example .env

Install dependencies:

    pip install -r backend\requirements.txt

## Start the application

    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

## Access the dashboard

    http://127.0.0.1:8000/

## API documentation

    http://127.0.0.1:8000/docs

## Health check

    http://127.0.0.1:8000/health

## Run tests

    pytest -q

## Security

The application requires administrator authentication.

File operations are restricted to the configured
lab_files directory.

Do not expose the development server directly
to the public internet.

For remote administration, configure a private
VPN such as Tailscale and appropriate access controls.

This project does not implement covert monitoring,
hidden persistence or secret keystroke capture.