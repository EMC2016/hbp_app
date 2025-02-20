from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

FHIR_SERVER = "https://fhir-server.com"


def discovery_cds_services(request):
    print("discovery request: ",request.method)
    return JsonResponse({
        'services':[
            {
                'hook':'patient-view',
                'title':'HyperPredict',
                'description':'Hello, this is an AI assisted app for blood pressure management!',
                'id':'80120',
                # 'prefetch':{
                    
                # }
            }
        ]
        })
@csrf_exempt 
def check_id(request,app_id):
    print("app id: ",app_id)
    print("request: ",request.method)
    if app_id=="80120":
        print('Valid user!')
        # if not request.body:
        #     return JsonResponse({"error": "Empty request body"}, status=400)

        # try:
        headers = dict(request.get_json())
        print("Raw header: ",headers)

        # body = json.loads(request.body.decode('utf-8'))
        # print("body:", body)
        # except json.JSONDecodeError:
        #     return JsonResponse({"error": "Invalid JSON format"}, status=400)
    return JsonResponse({"response:":"request received"})


def dashboard(request, patient_id):
    """Render dashboard.html initially"""
    
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
