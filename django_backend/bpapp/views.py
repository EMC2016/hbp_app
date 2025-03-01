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
from . import data_process as dp  


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
                    'age': "Observation?patient={{context.patientId}}&code=30525-0",  
                    'gender': "Observation?patient={{context.patientId}}&code=76689-9", 
                    'bmi': "Observation?patient={{context.patientId}}&code=39156-5",
                    'fasting_glucose': "Observation?patient={{context.patientId}}&code=2339-0",
                    'hdl': "Observation?patient={{context.patientId}}&code=2085-9",
                    'triglycerides': "Observation?patient={{context.patientId}}&code=2571-8",
                    'hba1c': "Observation?patient={{context.patientId}}&code=4548-4",
                    'serum_creatinine': "Observation?patient={{context.patientId}}&code=2160-0",
                    'alt': "Observation?patient={{context.patientId}}&code=1742-6",
                    'ast': "Observation?patient={{context.patientId}}&code=1920-8",
                    'smoking_status': "Observation?patient={{context.patientId}}&code=72166-2",
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
        
        dp.extract_json_data_chronological(json_data)
    
        df_patient = dp.extract_pretech_data_and_convert_values(json_data)

        df_patient = dp.fill_NaN_and_drop_patientId(df_patient)
        
        model_path = "/Users/qingxiaochen/Documents/Program/Hackathon/MedAI/meldrx_app/medlrx_project/XGBoostModel/xgb_hypertension.json"
        model = xgb.Booster()
        model.load_model(model_path)
        dinput = xgb.DMatrix(df_patient)

        # Predict probability using the model
        y_pred_log_odds = model.predict(dinput, output_margin=True)
        probabilities = expit(y_pred_log_odds)
        
        probability = probabilities[0]

        # Display the result
        print(f"Predicted Probability: {probability}")       

        if probability > 0.1:
            alert_indicator = "warning"
            summary_text = "High Risk of Cardiovascular Disease!  Visit SMARTAPP for more."
            suggestions = [
                {"label": "Schedule a Cardiologist Appointment"},
                {"label": "Order a Lipid Panel Test"},
                {"label": "Start a Low-Sodium Diet"},
                {"label": "Increase Daily Physical Activity"},
            ]
            
            suggestions = "1.Schedule a Cardiologist Appointment 2. Order a Lipid Panel Test "

            
        else:
            alert_indicator = "info"
            summary_text = "Cardiovascular disease risk is low."
            suggestions = [
                {"label": "Keep Daily Physical Activity"},
                {"label": "Maintain Healthy Diet"},
            ]

        # Return JSON response with appropriate alert level
        return JsonResponse({
            "cards": [
                {
                    "summary": summary_text,
                    "indicator": alert_indicator,
                    # "detail": suggestions,
                    "source": {
                        "label": "Cardiovascular Disease Risk Assessment",
                    },
                    "links": [
                        {
                            "label": "Cardiovascular App",
                            "url":"http://localhost:4434/launch",
                            "type": "smart",
                        },
                    ]
                }
            ]
        })
     
