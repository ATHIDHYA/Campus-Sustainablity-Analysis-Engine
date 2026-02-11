# Campus-Sustainablity-Analysis-Engine
🌱 Campus Sustainability Analytics Engine

A web-based analytics system developed using Flask (Python) to monitor, analyze, and visualize campus sustainability metrics including Energy, Water, Waste, and Greenery data.

This project enables institutions to track environmental performance through dashboards, automated scoring, bulk data uploads, and PDF report generation.

📌 Project Overview

The Campus Sustainability Analytics Engine provides:

📊 Interactive dashboard with visual sustainability scores

📤 Excel-based bulk data upload

⚡ Manual data entry for sustainability metrics

🧮 Automated sustainability score calculation

📄 Year-wise PDF report generation

🔐 Role-based authentication (Admin/User)

🌙 Dark mode UI

🚀 Features
✅ Authentication System

Secure login with password hashing (SHA-256)

Session-based authentication

Role-based access control (Admin / User)

✅ Sustainability Data Modules

⚡ Energy Consumption

💧 Water Usage

🗑 Waste Generation

🌳 Green Cover Area

✅ Automated Score Calculation

Sustainability scores are calculated using weighted normalization formulas:

Energy Score = 100 - (energy / 10)

Water Score = 100 - (water / 10)

Waste Score = 100 - (waste / 5)

Greenery Score = greenery / 2

Final Score = Average of all four components

✅ Bulk Excel Upload

Upload .xlsx files

Required columns:

month | year | energy | water | waste | greenery


Duplicate month–year entries are prevented

Scores auto-calculated immediately after upload

✅ Dashboard Visualization

Built using Chart.js

Displays monthly sustainability trends

Dynamic updates after data insertion

✅ PDF Report Generation

Year-wise sustainability report

Generated using ReportLab

Downloadable directly from dashboard

🛠 Tech Stack

Backend

Python 3

Flask

SQLite

Pandas

ReportLab

Frontend

HTML

CSS

Chart.js

Jinja2 Templating

Version Control

Git & GitHub

📂 Project Structure
Campus-Sustainability-Analysis-Engine/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── energy_entry.html
│   ├── water_entry.html
│   ├── waste_entry.html
│   ├── greenery_entry.html
│   └── upload_sustainability_excel.html
│
├── static/
│   └── style.css

⚙ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/ATHIDHYA/Campus-Sustainablity-Analysis-Engine.git
cd Campus-Sustainablity-Analysis-Engine

2️⃣ Create virtual environment
python3 -m venv venv
source venv/bin/activate

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Run the application
python app.py


Open in browser:

http://127.0.0.1:5000

🔐 Admin Functionalities

Add new users

Upload bulk sustainability data

Generate sustainability reports

📊 Sample Excel Format
month	year	energy	water	waste	greenery
1	2025	1200	3000	180	400
🧠 Academic Relevance

This project demonstrates:

Full-stack web development

Data ingestion & preprocessing

Analytical computation

Role-based security implementation

Report automation

Data visualization

🎓 Author

Athidhya J
Final Year Project – Campus Sustainability Analytics Engine

📜 License

This project is developed for academic and educational purposes.
