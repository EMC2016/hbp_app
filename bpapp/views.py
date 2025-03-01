from django.shortcuts import render
import json
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlencode
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import redirect
from django.conf import settings
import pkce
import secrets
import requests
from django.http import JsonResponse, HttpResponseBadRequest
import jwt
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import xgboost as xgb
from scipy.special import expit


def extract_observation_value(entry):
    """Extracts a value from an Observation or checks Condition existence."""
    if not entry or "entry" not in entry or not entry["entry"]:
        return None  # Return None if the entry is empty

    resource = entry["entry"][0]["resource"]

    # If it's an Observation, extract the numeric value
    if resource["resourceType"] == "Observation":
        return resource.get("valueQuantity", {}).get("value", None)

    # If it's a Condition, return True (indicating presence of the condition)
    if resource["resourceType"] == "Condition":
        return True  # Indicates the patient has hypertension

    return None  # Default case


def organize_and_store_json_data(data,patient_id):
    # Extracting values and timestamps from the "prefetch" section
    extracted_data = []

    for category, details in data.get("prefetch", {}).items():
        if isinstance(details, dict) and "entry" in details:
            for entry in details["entry"]:
                resource = entry.get("resource", {})
                timestamp = resource.get("effectiveDateTime") or resource.get("onsetDateTime") or resource.get("recordedDate")
                value = None
                unit = ""

                if "valueQuantity" in resource:
                    value = resource["valueQuantity"]["value"]
                    unit = resource["valueQuantity"].get("unit", "")
                elif "valueCodeableConcept" in resource:
                    value = resource["valueCodeableConcept"]["text"]

                if timestamp and value is not None:
                    extracted_data.append({"Category": category, "Timestamp": timestamp, "Value": value, "Unit": unit})

    # Convert to DataFrame and display
    df_extracted = pd.DataFrame(extracted_data)
    # tools.display_dataframe_to_user(name="Extracted Values and Timestamps", dataframe=df_extracted)
    


    # Define CSV file name
    csv_filename = f"extracted_data_{patient_id}.csv"

    # Save to CSV
    df_extracted.to_csv(csv_filename, index=False)





def discovery_cds_services(request):
    print("discovery request: ", request.method)
    
    # Calculate the date two years ago from today
    #two_years_ago = (datetime.utcnow() - timedelta(days=2*365)).strftime("%Y-%m-%d")

    return JsonResponse({
        'services': [
            {
                'hook': "patient-view",
                'title': 'HyperPredict',
                'description': 'AI-assisted app for blood pressure management and prediction.',
                'id': '80120',
                'prefetch': {
                    'patient': "Patient/{{context.patientId}}",
                    'age': "Observation?patient={{context.patientId}}&code=30525-0",  # Age
                    'gender': "Observation?patient={{context.patientId}}&code=76689-9",  # Gender
                    'bmi': "Observation?patient={{context.patientId}}&code=39156-5",
                    # 'waist': "Observation?patient={{context.patientId}}&code=8280-0",
                    'fasting_glucose': "Observation?patient={{context.patientId}}&code=2339-0",
                    'hdl': "Observation?patient={{context.patientId}}&code=2085-9",
                    # 'ldl': "Observation?patient={{context.patientId}}&code=13457-7",
                    'triglycerides': "Observation?patient={{context.patientId}}&code=2571-8",
                    'hba1c': "Observation?patient={{context.patientId}}&code=4548-4",
                    'serum_creatinine': "Observation?patient={{context.patientId}}&code=2160-0",
                    'alt': "Observation?patient={{context.patientId}}&code=1742-6",
                    'ast': "Observation?patient={{context.patientId}}&code=1920-8",
                    # 'crp': "Observation?patient={{context.patientId}}&code=1988-5",
                    'smoking_status': "Observation?patient={{context.patientId}}&code=72166-2",
                    # 'alcohol_use': "Observation?patient={{context.patientId}}&code=74013-4",
                    # 'physical_activity': "Observation?patient={{context.patientId}}&code=68215-7",
                    # 'ckd': "Condition?patient={{context.patientId}}&code=431855005",
                    # 'egfr': "Observation?patient={{context.patientId}}&code=33914-3", 
                    'hypertension': "Condition?patient={{context.patientId}}&code=59621000"
                }

            }
        ]
    })



    
@csrf_exempt 
def check_id(request,app_id):
    
    if app_id=="80120":
        # print('Valid user!')
        # print(request.META.get("HTTP_TRANSFER_ENCODING"))
        
        wsgi_input = request.META.get("wsgi.input")
        if not wsgi_input:
            return JsonResponse({"error": "WSGI input stream unavailable"}, status=500)

        body = b""
        while True:
            chunk = wsgi_input.read(4096)  # Read in 4KB chunks
            if not chunk:
                break
            body += chunk  
        decoded_body = body.decode("utf-8")  
        json_data = json.loads(decoded_body)
        
        
        
        
        prefetch = json_data.get("prefetch", {})

        # Extract individual values from FHIR response
        patient_id = prefetch.get("patient", {}).get("id")
        organize_and_store_json_data(json_data,patient_id)
    
        # Extract observations using helper function
        data = {
            "PatientID": patient_id,
            "Age": prefetch.get("patient", {}).get("birthDate"),  # Convert birthdate to age later
            "Gender": prefetch.get("patient", {}).get("gender"),
            "BMI": extract_observation_value(prefetch.get("bmi")),
            "Hypertension": 1 if extract_observation_value(prefetch.get("hypertension")) else 0,
            "Glucose": extract_observation_value(prefetch.get("fasting_glucose")),
            # "WaistCircumference": extract_observation_value(prefetch.get("waist")),
            # "SBP": extract_observation_value(prefetch.get("sbp")),
            # "DBP": extract_observation_value(prefetch.get("dbp")),
            "HDL": extract_observation_value(prefetch.get("hdl")),
            # "LDL": extract_observation_value(prefetch.get("ldl")),
            "Triglycerides": extract_observation_value(prefetch.get("triglycerides")),
            "Smoking": prefetch.get("smoking_status", {}).get("entry", [{}])[0].get("resource", {}).get("valueCodeableConcept", {}).get("coding", [{}])[0].get("display", None),
            # "Alcohol": prefetch.get("alcohol_use", {}).get("entry", [{}])[0].get("resource", {}).get("valueQuantity", {}).get("value", None),
            "HbA1c": extract_observation_value(prefetch.get("hba1c")),
            "SerumCreatinine": extract_observation_value(prefetch.get("serum_creatinine")),
            "ALT": extract_observation_value(prefetch.get("alt")),
            "AST": extract_observation_value(prefetch.get("ast")),
            # "CRP": extract_observation_value(prefetch.get("crp")),
            # "PhysicalActivity": extract_observation_value(prefetch.get("physical_activity")),
            
           
        }

        # Convert birthdate to age (assuming today's date)
        if data["Age"]:
            from datetime import datetime
            birth_year = int(data["Age"].split("-")[0])  # Extract year from birthdate
            data["Age"] = datetime.today().year - birth_year
            
        smoking_map = {
            "Never smoked tobacco (finding)": 0,
            "Ex-smoker (finding)": 1,
            "Current smoker (finding)": 1
        }
        gender_map = {"male": 1, "female": 2}
        # Convert Smoking Status to 0 or 1
        data["Smoking"] = smoking_map.get(data["Smoking"], 0)
        data["Gender"] = gender_map.get(data["Gender"],0)
        
        csv_file_path = "/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/hyertension_project/django_project/XGBoostModel/default_values.csv"
        # Load CSV into a DataFrame
        df_loaded = pd.read_csv(csv_file_path)

        # Convert first row to dictionary
        default_values = df_loaded.iloc[0].to_dict()
        # Convert to Pandas DataFrame
        df_patient = pd.DataFrame([data])   
        
        #Store data in csv file
        csv_filename = "patient_data.csv"
        df_patient.to_csv(csv_filename, mode='a', index=False, header=not pd.io.common.file_exists(csv_filename))

        print(f"✅ Patient data saved to {csv_filename}")
          
        # Assuming `df` is the DataFrame containing these columns
        df_patient.fillna(default_values, inplace=True)
        df_patient = df_patient.drop(columns=["PatientID"])
        # df_patient["Alcohol"] = pd.to_numeric(df_patient["Alcohol"], errors="coerce")

        model_path = "/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/hyertension_project/django_project/XGBoostModel/xgb_hypertension.json"
        model = xgb.Booster()
        model.load_model(model_path)
        dinput = xgb.DMatrix(df_patient)

        # Predict probability using the model
        y_pred_log_odds = model.predict(dinput, output_margin=True)
        probabilities = expit(y_pred_log_odds)
        
        probability = probabilities[0]

        # Display the result
        print(f"Predicted Probability: {probability}")       

        formatted_body = json.dumps(json_data, indent=4)

        ## APPS which deal with the prefetched data.
        with open(f"prefetch_data.json", "w") as json_file:
           json.dump(json_data, json_file, indent=4)

        if probability > 0.1:
            alert_indicator = "warning"
            summary_text = "High Risk of Cardiovascular Disease! Please click SMARTAPP for more information."
        else:
            alert_indicator = "info"
            summary_text = "Cardiovascular disease risk is low."

        # Return JSON response with appropriate alert level
        return JsonResponse({
            "cards": [
                {
                    "summary": summary_text,
                    "indicator": alert_indicator,
                    "source": {
                        "label": "Hypertension Risk Assessment",
                    },
                    "links": [
                        {
                            "label": "HyperTension App",
                            #"url": f"{settings.BASE_URL}/bpapp/launch",
                            "url":"http://localhost:4434/launch",
                            "type": "smart",
                        }
                    ]
                }
            ]
        })
     
     




            
def dashboard(request):
    """Render dashboard.html initially"""
    patient_id = "123"
   
    return render(request, "dashboard.html", {"patient_id": patient_id})


def get_bp_data(request, patient_id):
    # """Fetch blood pressure data from FHIR API"""
    data = {
        "bp_readings": [
            {"date": "2024-02-01", "systolic": 130, "diastolic": 85},
            {"date": "2024-02-02", "systolic": 135, "diastolic": 88},
            {"date": "2024-02-03", "systolic": 140, "diastolic": 90},
        ]
    }
    return JsonResponse(data)
    
    # return render(request, "dashboard.html", {"patient_id": patient_id})

def predict_bp(request, patient_id):
    """Simulated AI prediction (Replace with ML model)"""
    future_readings = [
        {"date": "2024-02-15", "systolic": 130, "diastolic": 85},
        {"date": "2024-02-16", "systolic": 135, "diastolic": 90},
    ]
    
    return JsonResponse({"predicted_bp": future_readings})
