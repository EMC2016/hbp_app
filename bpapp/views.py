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
                    'conditions': "Condition?patient={{context.patientId}}",
                },
            }
        ]
        })
@csrf_exempt 
def check_id(request,app_id):
    print("app id: ",app_id)
    print("Method:", request.method)
    print("Path:", request.path)

    all_headers = dict(request.headers)
    print("Headers:", all_headers)

    meta_info = dict(request.META)
    print("META:", meta_info)

    raw_body = request.body
    print("Raw body (bytes):", raw_body)
    
    if app_id=="80120":
        print('Valid user!')
        print(request.META.get("HTTP_TRANSFER_ENCODING"))
        
        if not request.body:
            return JsonResponse({"error": "Empty request body"}, status=400)
        body = json.loads(request.body.decode('utf-8'))
        print("body:", body)
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
                            "url":"https://45aafa042c34e0.lhr.life/dashboard",
                            "type":"absolute",
                        }
                    ]
                }
            ]
        })
        

        # try:
        # headers = dict(request.headers)
        # print("Raw header: ",headers)
        # data = json.loads(request.body)
        # print("Received data:", data)
        # return HttpResponse("Data received successfully")


        # except json.JSONDecodeError:
        #     return JsonResponse({"error": "Invalid JSON format"}, status=400)
        # data = request.data  # DRF automatically parses JSON
        # print("Received data:", data)
    


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
