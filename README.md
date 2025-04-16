# simple-survey-api
API for a simple survey application  

LOCAL SETUP  
DataBase Setup
Pre-requisites - mySQL/mariaDB Server and Client.  
Run the SQL set up queries in the sky_survey.sql file to set up the database.  
Remember to add your db password in the db_connector function in the simple-survey-api.py  

Python modules Setup.  
Pre-requisites - python3.  
Modules Setup - python3 -m pip install -r requirements.txt .  

Running the API  
python3 -m uvicorn simple-survey-api:app .
