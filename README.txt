WEATHER DATA ANALYSIS SYSTEM - VS CODE PROJECT

FEATURES
1. Upload a weather CSV file.
2. Validate required fields and report missing/invalid values.
3. Remove exact duplicate records and report their count.
4. Calculate daily minimum, maximum and average temperature and humidity,
   plus daily total rainfall.
5. Calculate monthly minimum, maximum and average temperature and humidity,
   plus monthly total rainfall.
6. Filter the dashboard by location.
7. Plot daily temperature trends, monthly rainfall, and monthly temperature/
   rainfall comparisons using Matplotlib.
8. Display units: temperature °C, humidity %, rainfall mm.
9. Includes a MySQL table design in schema.sql.

RUN IN VS CODE (Windows)
1. Extract the ZIP file.
2. Open the extracted Weather_Data_Analysis_Complete folder in VS Code.
3. Open Terminal > New Terminal.
4. Create environment:
   python -m venv venv
5. Activate:
   venv\Scripts\activate
6. Install packages:
   pip install -r requirements.txt
7. Run:
   python app.py
8. Open the local address printed in terminal, usually:
   http://127.0.0.1:5000

CSV FORMAT
Your CSV must contain these exact column names:
record_id, observation_date, location, temperature, humidity, rainfall

VALIDATION RULES
- Blank required fields are reported as missing.
- Unreadable dates and non-numeric weather values are reported as invalid.
- Temperature accepted range: -90 to 60 °C.
- Humidity accepted range: 0 to 100 percent.
- Rainfall must be zero or greater.
- Rows with missing/invalid required values are excluded from calculations.
- Exact duplicate rows are removed and counted separately.
- Data-quality counts are shown in the website.

IMPORTANT
The included weather.csv is sample demonstration data, not a verified official
weather record. Replace it with your supplied/public dataset for your report.
This project analyzes recorded observations; it does not forecast weather.

MYSQL
schema.sql contains the suggested weather_records table. The website currently
reads CSV files for analysis; MySQL schema is provided as the database design
deliverable and is not connected automatically.
