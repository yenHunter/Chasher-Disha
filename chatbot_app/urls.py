from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # load index.html at root
    path('chat/', views.chat, name='chat'),  # AJAX endpoint
]
