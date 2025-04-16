from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from typing import List, Any
from pathlib import Path
from collections import defaultdict, OrderedDict
import json, mysql.connector, os, uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="../simple-survey-client/static"), name="static")
templates = Jinja2Templates(directory="../simple-survey-client/templates")

@app.get("/api/questions", response_class=HTMLResponse)
async def create(request : Request):
    return templates.TemplateResponse("sky_survey.html", {"request" : request})

@app.put("/api/questions/responses", response_class=HTMLResponse)
async def store(
    request : Request,
    full_name : str = Form(...),
    email_address : str = Form(...),
    description : str = Form(...),
    gender : str = Form(...),
    programming_stack : List[str] = Form(...),
    certificates : List[UploadFile] = File(...)
):
    store_message : str = ""
    if not (survey_already_filled(email_address)):
        if (validate_responses(full_name, email_address, description, gender, programming_stack, certificates)):
            if (store_response(full_name, email_address, description, gender, programming_stack, certificates)):
                store_message = "success"
            else:
                store_message = "Your responses could not be saved, Please Fill the survey again"
        else:
            store_message = "Your responses could not be saved, Please Fill the survey again"
    else:
        store_message = "You have already taken the survey"

    return templates.TemplateResponse("sky_survey.html", {"request" : request, "store_message" : store_message})


@app.get("/api/questions/responses", response_class=HTMLResponse)
async def show(request : Request, email: str = ""):
    records = fetch_records(email)

    return templates.TemplateResponse("sky_survey_responses.html", {"request" : request, "records" : records})

@app.get("/api/questions/responses/certificates/{id}")
async def download(id : str, request : Request):
    cert_id : str = id
    conn : Any = db_connector()
    cur : Any = conn.cursor()
    get_cert_name_query : str = f"SELECT certificate_name FROM certificates WHERE certificate_id = '{cert_id}'"
    cur.execute(get_cert_name_query)

    cert_name = cur.fetchall()[0][0]

    file_path = Path(f"certificates/{cert_id}.pdf")

    return FileResponse(file_path, media_type="application/pdf", filename=f"{cert_name}")

@app.get("/api/survey_questions.json")
async def survey_questions():
    with open("static/js/survey_questions.json") as fo:
        survey_questions = json.load(fo)
    
    return survey_questions


def validate_responses(
    full_name : str,
    email_address : str,
    description : str,
    gender : str,
    programming_stack : List[str],
    certificates : List[UploadFile]
) -> bool:
    return full_name is not None and email_address is not None and description is not None and gender is not None and programming_stack is not None and certificates is not None

def db_connector() -> Any:
    conn : Any = mysql.connector.connect(
        host = "localhost",
        port = "3306",
        user = "root",
        passwd = "your_password_here",
        db = "sky_survey_db" 
    )
    return conn

def store_response(
    full_name : str,
    email_address : str,
    description : str,
    gender : str,
    programming_stack : List[str],
    certificates : List[UploadFile]
) -> str:
    stored_flag : bool = False
    try:
        programming_stack_str : str = ", ".join(programming_stack)
        personal_query : str = "INSERT INTO personal_information(email_address, full_name, gender) VALUES (%s, %s, %s)"
        resume_query : str = "INSERT INTO resume_information(email_address, description_, programming_stack) VALUES (%s, %s, %s)"

        conn : Any = db_connector()

        cur : Any = conn.cursor()
        cur.execute(personal_query, (email_address, full_name, gender))
        cur.execute(resume_query, (email_address, description, programming_stack_str))

        upload_dir :str = f"certificates"
        os.makedirs(upload_dir, exist_ok=True)
        print(certificates)
        if certificates[0].filename != "":
            certs : List[UploadFile] = certificates
        else:
            certs : List[UploadFile] = certificates[1:]

        cert_query : str = "INSERT INTO certificates(certificate_id, resume_id, certificate_name) VALUES (%s, %s, %s)"
        get_resume_id_query : str = "SELECT resume_id FROM resume_information WHERE email_address = %s"
        cur.execute(get_resume_id_query, (email_address, ))
        resume_id : str = cur.fetchall()[0][0]

        for file in certs:
            certificate_id : str = f"{uuid.uuid4()}"
            certificate_name : str = file.filename
            safe_filename : str = f"{certificate_id}.pdf"
            file_path : str = os.path.join(upload_dir, safe_filename)
            with open(file_path, "wb") as fo:
                fo.write(file.file.read())
            cur.execute(cert_query, (certificate_id, resume_id, certificate_name))
        
        conn.commit()
        cur.close()
        conn.close()

        stored_flag = True
    except:
        pass

    return stored_flag

def survey_already_filled(email_address : str) -> bool:
    conn : Any = db_connector()
    check_email_query : str = "SELECT email_address FROM personal_information WHERE email_address = %s"
    
    cur : Any = conn.cursor()
    cur.execute(check_email_query, (email_address, ) )
    exists : str = cur.fetchall()
    if exists: return True

    return False

def fetch_records(email : str = ""):

    fetch_responses_query : str = """
SELECT 
    pi.full_name,
    pi.email_address,
    ri.description_,
    pi.gender,
    ri.programming_stack
FROM personal_information pi
LEFT JOIN resume_information ri ON pi.email_address = ri.email_address
"""
    fetch_certificates_query : str = """
SELECT ri.email_address, ci.certificate_id 
FROM resume_information ri
LEFT JOIN certificates ci ON ri.resume_id = ci.resume_id
"""
    conn : Any = db_connector()
    cur : Any = conn.cursor()

    if email:
        fetch_responses_query += "WHERE pi.email_address = %s"
        fetch_certificates_query += "WHERE ri.email_address = %s"

        cur.execute(fetch_responses_query, (email, ))
        responses = cur.fetchall()
        cur.execute(fetch_certificates_query, (email, ))
        certificates = cur.fetchall()
    else:
        cur.execute(fetch_responses_query)
        responses = cur.fetchall()
        cur.execute(fetch_certificates_query)
        certificates = cur.fetchall()

    records = defaultdict(tuple)
    num_records : int = 0
    for response in responses:
        records[response[1]] = response
        for i in range(num_records, len(certificates)):
            if certificates[i][0] == response[1]:
                records[response[1]] += certificates[i]
            else:
                break
            num_records += 1 
    records = records.values()


    cur.close()
    conn.close()

    return records