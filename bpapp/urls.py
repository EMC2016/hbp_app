from django.urls import path
from .views import get_bp_data, predict_bp,dashboard

urlpatterns = [
    path("dashboard/<str:patient_id>/", dashboard, name="bp_dashboard"),
    path("predict/<str:patient_id>/", predict_bp, name="predict_bp"),
    path("api/<str:patient_id>/", get_bp_data, name="get_datas"),
    
]
