# 🌿 Green Travel Recommendation System

A **Django-based web application** that provides travel recommendations with a focus on eco-friendly and sustainable choices.  
Users can sign up, log in, view personalized recommendations, track history, and explore green travel options.

---

## 🧠 Project Overview

This system suggests *environmentally conscious travel options* based on user inputs such as destination, preferences, and travel criteria.  
It aims to promote **green travel alternatives** while offering a clean and intuitive user experience.

---

## ✨ Key Features

✔ User authentication (signup/login/logout)  
✔ AI-driven recommendation generation  
✔ Travel history tracking  
✔ Search and filter for recommended routes  
✔ Clean, responsive interface (HTML + CSS)  
✔ Template-based rendering for dynamic content  

---
## Requirements
GREEN TRAVEL RECOMMENDATION SYSTEM
SYSTEM & SOFTWARE REQUIREMENTS
================================

1. OPERATING SYSTEM
-------------------
- Windows 10 / 11
- macOS
- Linux

2. PROGRAMMING LANGUAGE
-----------------------
- Python version 3.10 or higher
- Python must be added to system PATH

3. WEB FRAMEWORK
----------------
- Django (installed via requirements.txt)

4. VERSION CONTROL
------------------
- Git (for cloning and managing the repository)

5. DATABASE
-----------
- SQLite3 (default Django database)
- No separate installation required

6. PYTHON DEPENDENCIES
---------------------
The following Python libraries are required:

- Django
- requests
- googlemaps
- python-dotenv

(All dependencies can be installed using:
 pip install -r requirements.txt)

7. API REQUIREMENTS
-------------------
- Google Maps API Key (for distance calculation and routing)
- Required Google APIs:
  - Distance Matrix API
  - Geocoding API

The API key should be stored in a .env file as:
GOOGLE_MAPS_API_KEY=your_api_key_here

8. DEVELOPMENT TOOLS (RECOMMENDED)
----------------------------------
- VS Code or any Python IDE
- Web browser (Chrome / Edge / Firefox)

9. PROJECT SETUP REQUIREMENTS
-----------------------------
- Virtual Environment (recommended)
- Apply database migrations
- Run Django development server

Required commands:
- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver

10. BROWSER REQUIREMENT
----------------------
- Any modern web browser to access the application

11. OPTIONAL FOR PRODUCTION
---------------------------
- PostgreSQL or MySQL database
- DEBUG = False in Django settings
- Proper ALLOWED_HOSTS configuration

================================
END OF REQUIREMENTS FILE
