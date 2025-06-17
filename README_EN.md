# Denkwürfel

A simple note and task manager built with Python and PyQt6.  
This project provides a GUI for creating, editing, and storing notes and tasks, working with a remote PostgreSQL database using psycopg2 and supporting Excel import/export via openpyxl.

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation and Launch](#installation-and-launch)
  - [Clone the Repository](#clone-the-repository)
  - [Create a Virtual Environment](#create-a-virtual-environment)
  - [Install Dependencies](#install-dependencies)
  - [Configure Database Connection](#configure-database-connection)
  - [Run the Application](#run-the-application)
- [Project Structure](#project-structure)
- [Using the Application](#using-the-application)

---

## Introduction

Novamind is a desktop application for managing notes and tasks with a PyQt6 GUI.  
Data is stored on a remote PostgreSQL database accessed via the psycopg2 library. Excel file import and export is supported using openpyxl.

The application is designed for users who need centralized storage of tasks and notes on a server, with the convenience of local interaction through an intuitive interface.

---

## Features

- PyQt6-based GUI for cross-platform desktop experience  
- Data stored in a remote PostgreSQL database via psycopg2  
- Create, edit, and delete tasks  
- Task priorities indicated by colored markers  
- Task statuses (e.g., “New”, “In Progress”, “Completed”)  
- Filter tasks by priority, status, tags, and date  
- Reminders (if client-side notifications are implemented)  
- Create, edit, and delete notes with optional Markdown support  
- Import/export tasks and notes to/from Excel using openpyxl  
- Database connection configured via external config file

---

## Requirements

- **Python**: version 3.8 or higher  
- **pip**: latest version recommended  
- **PyQt6**: for the GUI  
- **psycopg2**: for PostgreSQL connectivity  
- **openpyxl**: for Excel file support

---

## Installation and Launch

### Clone the Repository

Open a terminal (Git Bash, PowerShell, CMD) and run:
```bash
git clone https://github.com/FlexEbat/Denkwurfel.git
cd Novamind
```

### Create a Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate
```

### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure Database Connection
Create a config.ini file in the root directory:
```bash
[database]
host = your_db_host_or_ip
port = 5432
dbname = your_database_name
user = your_username
password = your_password
sslmode = require
```

### Run the Application
```bash
python main.py
```

---

## Project Structure
```bash
Denkwurfel/
```

---

## Using the Application
**Working with Tasks**

- **Create:** Click + `New Task`, fill in the data.
- **Edit:** Double-click on a task to edit it.
- **Delete:** Select and click "Delete".
- **Filter:** By tags, priority, or status.
- **Search:** By title or description.

**Working with Notes**

- **Create:** Click  `+ New Note`, enter text.
- **Edit:** Double-click a note to edit it.
- **Delete:** Click "Delete".
- **Formatting:** Markdown support.

---
Add comment
