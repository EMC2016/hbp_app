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


def extract_json_data_chronological(data):
    # Extracting values and timestamps from the "prefetch" section
    extracted_data = []
    prefetch = data.get("prefetch", {})
    patient_id = prefetch.get("patient", {}).get("id")

    # Define attributes for time-series data
    attributes = {
        'bmi': "39156-5",
        'fasting_glucose': "2339-0",
        'hdl': "2085-9",
        'triglycerides': "2571-8",
        'hba1c': "4548-4",
        'serum_creatinine': "2160-0",
        'alt': "1742-6",
        'ast': "1920-8",
    }

    # Store single values for age, gender, and hypertension

    # Loop through prefetch data
    for category, details in prefetch.items():
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



                # Store time-series attributes
                if timestamp and value is not None:
                    for attr_name, code in attributes.items():
                        if code in details.get("resourceType", "") or code in resource.get("code", {}).get("coding", [{}])[0].get("code", ""):
                            extracted_data.append({
                                "Patient ID": patient_id,
                                "Category": attr_name,
                                "Timestamp": timestamp,
                                "Value": value,
                                "Unit": unit
                            })

    # Convert to DataFrame
    df_extracted = pd.DataFrame(extracted_data)

    # Save single-value patient info separately
    

    # Save to CSV
    csv_filename_values = f"/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/meldrx_app/medlrx_project/vite_app/src/assets/extracted_data_{patient_id}.csv"

    df_extracted.to_csv(csv_filename_values, index=False)

    print(f"Chronological data saved to {csv_filename_values}")

    # Save raw prefetch data for debugging
    with open("prefetch_data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    return df_extracted





def extract_observation_value(entry):
    """Extracts a value from an Observation or checks Condition existence."""
    if not entry or "entry" not in entry or not entry["entry"]:
        return None  
    resource = entry["entry"][0]["resource"]

    # If it's an Observation, extract the numeric value
    if resource["resourceType"] == "Observation":
        return resource.get("valueQuantity", {}).get("value", None)

    # If it's a Condition, return True (indicating presence of the condition)
    if resource["resourceType"] == "Condition":
        return True  # Indicates the patient has hypertension

    return None  # Default case
    
    
def extract_pretech_data_and_convert_values(json_data):
    # Extract observations in the same order as them in XGBoost
    
    prefetch = json_data.get("prefetch", {})
    patient_id = prefetch.get("patient", {}).get("id")
    
    data = {
        "PatientID": patient_id,
        "Age": prefetch.get("patient", {}).get("birthDate"),  
        "Gender": prefetch.get("patient", {}).get("gender"),
        "BMI": extract_observation_value(prefetch.get("bmi")),
        "Hypertension": 1 if extract_observation_value(prefetch.get("hypertension")) else 0,
        "Glucose": extract_observation_value(prefetch.get("fasting_glucose")),
        "HDL": extract_observation_value(prefetch.get("hdl")),
        "Triglycerides": extract_observation_value(prefetch.get("triglycerides")),
        "Smoking": prefetch.get("smoking_status", {}).get("entry", [{}])[0].get("resource", {}).get("valueCodeableConcept", {}).get("coding", [{}])[0].get("display", None),
        "HbA1c": extract_observation_value(prefetch.get("hba1c")),
        "SerumCreatinine": extract_observation_value(prefetch.get("serum_creatinine")),
        "ALT": extract_observation_value(prefetch.get("alt")),
        "AST": extract_observation_value(prefetch.get("ast")),
        
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
    
    
    patient_info = {"Patient ID": patient_id, "Age": data["Age"] , "Gender": data["Gender"] , "Hypertension": data["Hypertension"] ,"Smoking":data["Smoking"]}
    df_patient_info = pd.DataFrame([patient_info])
    csv_filename_info = f"/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/meldrx_app/medlrx_project/vite_app/src/assets/patient_info_{patient_id}.csv"
    df_patient_info.to_csv(csv_filename_info, index=False)
    print(f"Patient info saved to {csv_filename_info}")


    df_patient = pd.DataFrame([data])       
    csv_filename = "patient_data.csv"
    df_patient.to_csv(csv_filename, mode='a', index=False, header=not pd.io.common.file_exists(csv_filename))
    print(f"✅ Patient data saved to {csv_filename}")
    
    return df_patient

    
def fill_NaN_and_drop_patientId(df_patient):
    csv_file_path = "/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/meldrx_app/medlrx_project/XGBoostModel/default_values.csv"
    # Load CSV into a DataFrame
    df_loaded = pd.read_csv(csv_file_path)

    # Convert first row to dictionary
    default_values = df_loaded.iloc[0].to_dict()
    # Convert to Pandas DataFrame
    
    # Assuming `df` is the DataFrame containing these columns
    df_patient.fillna(default_values, inplace=True)
    df_patient = df_patient.drop(columns=["PatientID"])
    
    return df_patient
