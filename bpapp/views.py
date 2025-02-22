from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
    # print("app id: ",app_id)
    # print("Method:", request.method)
    # print("Path:", request.path)

    # all_headers = dict(request.headers)
    # print("Headers:", all_headers)

    # meta_info = dict(request.META)
    # print("META:", meta_info)

    
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
        print(formatted_body)
       
        
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
                            "url":"https://ba7adcd78b8bcf.lhr.life/bpapp/launch",
                            "type":"smart",
                        }
                    ]
                }
            ]
        })
            
def dashboard(request):
    """Render dashboard.html initially"""
    patient_id = "123"
    # data = {
    #     "bp_readings": [
    #         {"date": "2024-02-01", "systolic": 130, "diastolic": 85},
    #         {"date": "2024-02-02", "systolic": 135, "diastolic": 88},
    #         {"date": "2024-02-03", "systolic": 140, "diastolic": 90},
    #     ]
    # }
    # return JsonResponse(data)
    return render(request, "dashboard.html", {"patient_id": patient_id})


def get_bp_data(request, patient_id):
    # """Fetch blood pressure data from FHIR API"""
    # url = f"{FHIR_SERVER}/Observation?patient={patient_id}&code=85354-9"
    # response = requests.get(url)
    # bp_data = response.json()
    
    # # Extract systolic & diastolic values
    # readings = [
    #     {"date": obs["resource"]["effectiveDateTime"], 
    #      "systolic": obs["resource"]["component"][0]["valueQuantity"]["value"], 
    #      "diastolic": obs["resource"]["component"][1]["valueQuantity"]["value"]}
    #     for obs in bp_data.get("entry", [])
    # ]
    
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
