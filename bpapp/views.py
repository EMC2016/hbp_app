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

def discovery_cds_services(request):
    print("discovery request: ", request.method)
    
    # Calculate the date two years ago from today
    two_years_ago = (datetime.utcnow() - timedelta(days=2*365)).strftime("%Y-%m-%d")

    # return JsonResponse({
    #     'services': [
    #         {
    #             'hook': "patient-view",
    #             'title': 'HyperPredict',
    #             'description': 'AI-assisted app for blood pressure management and prediction.',
    #             'id': '80120',
    #             'prefetch': {
    #                 'patient': "Patient/{{context.patientId}}",
    #                 'bmi': f"Observation?patient={{context.patientId}}&code=39156-5&date=ge{two_years_ago}",
    #                 'waist': f"Observation?patient={{context.patientId}}&code=8280-0&date=ge{two_years_ago}",
    #                 'sbp': f"Observation?patient={{context.patientId}}&code=8480-6&date=ge{two_years_ago}",
    #                 'dbp': f"Observation?patient={{context.patientId}}&code=8462-4&date=ge{two_years_ago}",
    #                 'cavi': f"Observation?patient={{context.patientId}}&code=CUSTOM-CAVI&date=ge{two_years_ago}",  # Custom Code
    #                 'hdl': f"Observation?patient={{context.patientId}}&code=2085-9&date=ge{two_years_ago}",
    #                 'ldl': f"Observation?patient={{context.patientId}}&code=13457-7&date=ge{two_years_ago}",
    #                 'uric_acid': f"Observation?patient={{context.patientId}}&code=14959-1&date=ge{two_years_ago}",
    #                 'fasting_glucose': f"Observation?patient={{context.patientId}}&code=2339-0&date=ge{two_years_ago}",
    #                 'triglycerides': f"Observation?patient={{context.patientId}}&code=2571-8&date=ge{two_years_ago}",
    #                 'alp': f"Observation?patient={{context.patientId}}&code=6768-6&date=ge{two_years_ago}",
    #                 'diabetes': f"Condition?patient={{context.patientId}}&code=73211009&onset-date=ge{two_years_ago}",
    #                 'ckd': f"Condition?patient={{context.patientId}}&code=431855005&onset-date=ge{two_years_ago}",
    #                 'smoking_status': f"Observation?patient={{context.patientId}}&code=72166-2&date=ge{two_years_ago}",
    #                 'alcohol_use': f"Observation?patient={{context.patientId}}&code=74013-4&date=ge{two_years_ago}"
    #             },
    #         }
    #     ]
    # })
    return JsonResponse({
        'services': [
            {
                'hook': "patient-view",
                'title': 'HyperPredict',
                'description': 'AI-assisted app for blood pressure management and prediction.',
                'id': '80120',
                'prefetch': {
                    'patient': "Patient/{{context.patientId}}",
                    'bmi': "Observation?patient={{context.patientId}}&code=39156-5",
                    'waist': "Observation?patient={{context.patientId}}&code=8280-0",
                    'sbp': "Observation?patient={{context.patientId}}&code=8480-6",
                    'dbp': "Observation?patient={{context.patientId}}&code=8462-4",
                    'cavi': "Observation?patient={{context.patientId}}&code=CUSTOM-CAVI",  # Custom Code
                    'hdl': "Observation?patient={{context.patientId}}&code=2085-9",
                    'ldl': "Observation?patient={{context.patientId}}&code=13457-7",
                    'uric_acid': "Observation?patient={{context.patientId}}&code=14959-1",
                    'fasting_glucose': "Observation?patient={{context.patientId}}&code=2339-0",
                    'triglycerides': "Observation?patient={{context.patientId}}&code=2571-8",
                    'alp': "Observation?patient={{context.patientId}}&code=6768-6",
                    'diabetes': "Condition?patient={{context.patientId}}&code=73211009",
                    'ckd': "Condition?patient={{context.patientId}}&code=431855005",
                    'smoking_status': "Observation?patient={{context.patientId}}&code=72166-2",
                    'alcohol_use': "Observation?patient={{context.patientId}}&code=74013-4"
                },
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
        formatted_body = json.dumps(json_data, indent=4)
        #print("Get Prefetch formatted_body!", formatted_body)

        ## APPS which deal with the prefetched data.
        with open("prefetch_data.json", "w") as json_file:
           json.dump(json_data, json_file, indent=4)
        
        return JsonResponse({
            "cards":[
                {
                    "summary":"Hello world!",
                    "indicator":"info",
                    "source":{
                        "label":"test service",
                    },
                    "links":[
                        {
                            "label":"HyperTension App",
                            "url":f"{settings.BASE_URL}/bpapp/launch",
                            #"url":"http://localhost:4434/launch",
                            "type":"smart",
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
