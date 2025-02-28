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
                    'ckd': "Condition?patient={{context.patientId}}&code=431855005",
                    'egfr': "Observation?patient={{context.patientId}}&code=33914-3", 
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
            #"LDL": extract_observation_value(prefetch.get("ldl")),
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
        
        # default_values = {
        #     "BMI": 22.5,
        #     "HDL": 50,
        #     "Triglycerides": 100,
        #     "Glucose": 90,
        #     "HbA1c": 5.4,
        #     "SerumCreatinine": 1.0,
        #     "ALT": 20,
        #     "AST": 20,
        #     # "Alcohol":4,
        # }
        csv_file_path = "/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/hyertension_project/XGBoostModel/default_values.csv"

        # Load CSV into a DataFrame
        df_loaded = pd.read_csv(csv_file_path)

        # Convert first row to dictionary
        default_values = df_loaded.iloc[0].to_dict()
        
        
        # Convert to Pandas DataFrame
        df_patient = pd.DataFrame([data])
        
        # Assuming `df` is the DataFrame containing these columns
        df_patient.fillna(default_values, inplace=True)
        df_patient = df_patient.drop(columns=["PatientID"])
        # df_patient["Alcohol"] = pd.to_numeric(df_patient["Alcohol"], errors="coerce")

        model_path = "/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/hyertension_project/XGBoostModel/xgb_hypertension.json"  # Adjust the path to your actual model location

        model = xgb.Booster()
        model.load_model(model_path)
        dinput = xgb.DMatrix(df_patient)

        # Predict probability using the model
        y_pred_log_odds = model.predict(dinput, output_margin=True)
        probabilities = expit(y_pred_log_odds)
        
        probability = probabilities[0]

        # Display the result
        print(f"Predicted Probability: {probability}")
        print(probabilities)
        print(y_pred_log_odds)

        # Print extracted data for debugging
        csv_filename = "patient_data.csv"
        df_patient.to_csv(csv_filename, mode='a', index=False, header=not pd.io.common.file_exists(csv_filename))

        print(f"✅ Patient data saved to {csv_filename}")

        formatted_body = json.dumps(json_data, indent=4)
        #print("Get Prefetch formatted_body!", formatted_body)

        ## APPS which deal with the prefetched data.
        with open(f"prefetch_data.json", "w") as json_file:
           json.dump(json_data, json_file, indent=4)
        probability = 0.8
        if probability > 0.5:
            alert_indicator = "warning"
            summary_text = "High Risk of Hypertension! Please consult a doctor."
        else:
            alert_indicator = "info"
            summary_text = "Hypertension risk is low."

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
                            "url": f"{settings.BASE_URL}/bpapp/launch",
                            "type": "smart",
                        }
                    ]
                }
            ]
        })
     
     


def launch_app(request):
    """Generates the OIDC authentication URL with PKCE and state protection"""

    # Generate a random state (for CSRF protection)
    state = secrets.token_hex(16)  # Equivalent to JavaScript's random state

    # Generate a PKCE code verifier and challenge
    code_verifier = pkce.generate_code_verifier(length=64)  # Secure random string
    code_challenge = pkce.get_code_challenge(code_verifier)

    # Store these values in the session for later token exchange
    request.session["oidc_state"] = state
    request.session["oidc_code_verifier"] = code_verifier  # Save to validate PKCE

    # Construct the OIDC authorization URL
    oidc_params = {
        "client_id": settings.OIDC_CLIENT_ID,
        "client_secret": settings.OIDC_CLIENT_SECRET,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.OIDC_RP_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "response_mode": "query",  # Default behavior
    }

    auth_url = f"{settings.OIDC_AUTHORITY}/connect/authorize?{urlencode(oidc_params)}"

    print(f"Redirecting to OIDC URL: {auth_url}")  # Debugging

    return redirect(auth_url)



def callback(request):
    """Handles OIDC callback and processes the signin response"""
    print("Procee CallBack: ",request)
    # Extract the authorization code from the request
    auth_code = request.GET.get("code")
    state = request.GET.get("state")
    
    if not auth_code:
        return HttpResponseBadRequest("Missing authorization code")

    # Validate the state parameter (CSRF protection)
    if state != request.session.get("oidc_state"):
        return HttpResponseBadRequest("Invalid state parameter")

    # Retrieve the stored PKCE code verifier
    code_verifier = request.session.get("oidc_code_verifier")
    if not code_verifier:
        return HttpResponseBadRequest("PKCE verifier missing")
    
    
     # Exchange the authorization code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "client_id": settings.OIDC_CLIENT_ID,
        "client_secret": settings.OIDC_CLIENT_SECRET,
        "code_verifier": code_verifier
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    # Send the POST request to the OIDC token endpoint
    response = requests.post(settings.OIDC_TOKEN_ENDPOINT, data=token_data, headers = headers)

    if response.status_code != 200:
        return HttpResponseBadRequest(f"Failed to exchange code for token: {response.text}")

    token_json = response.json()
    id_token = token_json.get("id_token")
    decoded_id = jwt.decode(id_token, options={"verify_signature": False})
    access_token = token_json.get("access_token")
    decoded_access = jwt.decode(access_token, options={"verify_signature": False})
    
    print("Decoded ID Token:", decoded_id)
    print("Decoded access Token:",decoded_access)
    

   
    # return JsonResponse(token_json)




            
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
