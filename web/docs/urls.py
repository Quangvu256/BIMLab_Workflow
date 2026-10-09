from django.urls import path
from . import views

urlpatterns = [
    path('', views.doc_list, name='doc_list'),
    path('docs/<slug:slug>/', views.doc_detail, name='doc_detail'),
    path('docs/<slug:slug>/raw-html/', views.doc_html_raw, name='doc_html_raw'),
    path('media/<path:path>', views.media_access, name='media_access'),
    path('api/upload-image/', views.api_upload_image, name='api_upload_image'),
    path('api/upload-html/', views.api_upload_html, name='api_upload_html'),
]
