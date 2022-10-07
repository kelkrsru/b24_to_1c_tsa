from django.urls import path

from . import views

app_name = 'activities'

urlpatterns = [
    path('install/', views.install, name='install'),
    path('uninstall/', views.uninstall, name='uninstall'),
    path('b24-to-1c/', views.b24_to_1c, name='b24_to_1c'),
    path('add-productrow/', views.add_productrow, name='add_productrow'),
]
