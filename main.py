import uuid
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
import pdfplumber
import json
import api
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi import status

from typing import Dict, Optional

# This will store red flags keyed by a unique identifier
red_flags_storage: Dict[str, str] = {}
app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root(request: Request, red_flags_id: Optional[str] = None):
    red_flags_html = ""

    # If a red flags id was passed, retrieve the red flags HTML
    if red_flags_id and red_flags_id in red_flags_storage:
        red_flags_html = red_flags_storage[red_flags_id]
        # Optionally, delete the red flags from storage after retrieval
        del red_flags_storage[red_flags_id]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "red_flags_html": red_flags_html
    })


def format_red_flags(red_flags):
    if not red_flags:
        return "<h2 class='safe'>No red flags found. Your contract is safe!</h2>"

    red_flags_html = "<h2 class='red-flags-header'>Red Flags detected:</h2><ul class='red-flags-list'>"
    for key, value in red_flags.items():
        red_flags_html += f"<li class='red-flag'><strong>{key}</strong>: {value}</li>"
    red_flags_html += "</ul>"

    return red_flags_html

def check_red_flags(final_response):
    red_flags = {}

    # Helper function to check if value is numeric and not 'NA'
    def is_valid_number(value):
        try:
            return value != "NA" and float(value) is not None
        except ValueError:
            return False

    # Check for price per kWh
    if is_valid_number(final_response.get("Rate per Kwh", 0)) and final_response.get("Rate per Kwh", 0) > 0.15:
        red_flags["Rate per Kwh"] = "Price per kWh is greater than $0.15"

    # Check for escalator rate
    if is_valid_number(final_response.get("Price Increase Per Year", 0)) and final_response.get("Price Increase Per Year", 0) > 1.5:
        red_flags["Price Increase Per Year"] = "Escalator rate is greater than 1.5%"

    # Check for vendor name
    if final_response.get("Vendor", "") in ["Sunrun", "Sunnova"]:
        red_flags["Vendor"] = "Vendor is Sunrun or Sunnova, which has a bad reputation. Please be cautious."

    # Check for cost per kW
    if is_valid_number(final_response.get("Cost per kW", 0)) and final_response.get("Cost per kW", 0) > 2.50:
        red_flags["Cost per kW"] = "Cost per kW is greater than $2.50"

    # Check for interest rate
    if is_valid_number(final_response.get("Interest Rate", 0)) and final_response.get("Interest Rate", 0) > 4:
        red_flags["Interest Rate"] = "Interest Rate is greater than 4%"

    return {"Red Flags": red_flags}


@app.post("/uploadfile/", response_class=HTMLResponse)
async def create_upload_file(request: Request, file: UploadFile = File(...)):
    responses = []
    with pdfplumber.open(file.file) as pdf:
        for i in range(min(3, len(pdf.pages))):  # Processing only the first three pages
            page = pdf.pages[i]
            text = page.extract_text()
            print("page begins#####################")
            print(text)
            print("#######################page ends")
            response = await api.get_gpt_response(text)  # Await the asynchronous call
            responses.append(response)

    final_response = {}
    
    for key in set(k for d in responses for k in d.keys()):
        values = [d[key] for d in responses if d[key] != "NA"]
        if values:
            final_response[key] = max(values, key=lambda x: (x is not None, x))
        else:
            final_response[key] = "NA"
    
    red_flags_response = check_red_flags(final_response)
    formatted_red_flags = format_red_flags(
        red_flags_response.get("Red Flags", {}))

    # Generate a unique identifier for this set of red flags
    red_flags_id = str(uuid.uuid4())
    red_flags_storage[red_flags_id] = formatted_red_flags

    url = app.url_path_for("read_root") + f"?red_flags_id={red_flags_id}#features12-4"
    response = RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
    return response
    
