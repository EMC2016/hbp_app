from django.urls import path
from .views import *

urlpatterns = [
    path("dashboard/<str:patient_id>/", dashboard, name="bp_dashboard"),
    path("predict/<str:patient_id>/", predict_bp, name="predict_bp"),
    path("api/<str:patient_id>/", get_bp_data, name="get_datas"),
    path("cds-services/",discovery_cds_services,name="discovery"),
    path("launch",dashboard, name="bp_dashboard"),
    path("cds-services/<str:app_id>",check_id,name = "check_id"),#This verifies the app user is valid by checking id is correct. 
   
]