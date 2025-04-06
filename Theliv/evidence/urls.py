from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_evidence, name='submit_evidence'),
    path('preview/<str:evd_id>/', views.preview_evidence, name='preview_evidence'),
    path('view/', views.view_evidence, name='view_evidence'),
    path('transfer/', views.transfer_evidence, name='transfer_evidence'),
    path('audit/', views.audit_evidence, name='audit_evidence'),
]