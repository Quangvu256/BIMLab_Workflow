from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('docs.urls')),
]

admin.site.site_header = "BIM Lab Docs Administration"
admin.site.site_title = "BIM Lab Admin"
admin.site.index_title = "Quản trị Quy trình & Tiêu chuẩn Kỹ thuật BIM (v3)"
