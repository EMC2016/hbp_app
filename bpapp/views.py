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

def discovery_cds_services(request):
    print("discovery request: ",request.method)
    return JsonResponse({
        'services':[
            {
                'hook':"patient-view",
                'title':'HyperPredict',
                'description':'Hello, this is an AI assisted app for blood pressure management!',
                'id':'80120',
                'prefetch': {
                    'patient': "Patient/{{context.patientId}}",
                    'observations': "Observation?patient={{context.patientId}}",
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
        print("Get Prefetch formatted_body!", formatted_body)
       
        
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
        "code_verifier": code_verifier,  # Must match the original challenge
        "scope": "openid profile launch patient/*.*", 
        "response_type": "code",# Ensure all scopes are requested
        "authority": "https://app.meldrx.com/",
    }

   

    # Send the POST request to the OIDC token endpoint
    response = requests.post(settings.OIDC_TOKEN_ENDPOINT, data=token_data)

    if response.status_code != 200:
        return HttpResponseBadRequest(f"Failed to exchange code for token: {response.text}")

    token_json = response.json()
    id_token = token_json.get("id_token")
    decoded_id = jwt.decode(id_token, options={"verify_signature": False})
    access_token = token_json.get("access_token")
    decoded_access = jwt.decode(access_token, options={"verify_signature": False})
    tenant_list = json.loads(decoded_access.get('tenant'))
    # If you expect only one tenant, get the first element:
    patient_id = tenant_list[0]
    print("Decoded ID Token:", decoded_id)
    print("Decoded access Token:",decoded_access)
    print("Patient ID:",patient_id)
    print("response: ",token_json)
    
   
    
   
    return JsonResponse(token_json)




            
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
