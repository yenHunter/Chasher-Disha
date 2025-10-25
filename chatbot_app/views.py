from django.shortcuts import render
from django.http import JsonResponse
from .nlp_model import get_response

# View to render index.html
def home(request):
    return render(request, "index.html")  # make sure index.html is in templates folder

# AJAX view for chat
def chat(request):
    if request.method == "GET":
        user_input = request.GET.get("message", "")
        if user_input.strip() == "":
            return JsonResponse({"response": "দুঃখিত, আমি কিছুই পাইনি 😔"})
        
        bot_response = get_response(user_input)
        return JsonResponse({"response": bot_response})
