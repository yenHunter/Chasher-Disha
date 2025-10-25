from django.http import JsonResponse
from django.shortcuts import render
from .nlp_model import get_response

def chat_page(request):
    return render(request, "index.html")

def get_reply(request):
    user_input = request.GET.get("msg")
    bot_reply = get_response(user_input)
    return JsonResponse({"reply": bot_reply})
