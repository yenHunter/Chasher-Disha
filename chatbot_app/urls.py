from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('get_weather/', views.get_weather, name='get_weather'),
    path('predict_disease/', views.predict_disease, name='predict_disease'),
]
