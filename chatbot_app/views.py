import requests
import json
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from .nlp_model import get_response
from django.views.decorators.csrf import csrf_exempt

OPENWEATHER_API_KEY = settings.OPENWEATHER_API_KEY

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

@csrf_exempt
def get_weather(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        lat = data.get('latitude')
        lon = data.get('longitude')
        if lat and lon:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=bn"
            resp = requests.get(url)
            if resp.status_code == 200:
                weather_data = resp.json()
                location = weather_data['name']
                weather = weather_data['weather'][0]['main'].lower()
                clouds = weather_data['clouds']['all']
                temp = weather_data['main']['temp']
                feels_like = weather_data['main']['feels_like']
                humidity = weather_data['main']['humidity']
                if weather in ['rain', 'drizzle', 'thunderstorm']:
                    rain = 100
                if weather in ['clear', 'haze', 'mist', 'smoke', 'dust', 'fog', 'sand', 'ash', 'squall', 'tornado']:
                    rain = 0
                
                if clouds >= 90:
                    rain = 80
                elif clouds >= 70:
                    rain = 60
                elif clouds >= 50:
                    rain = 40
                elif clouds >= 30:
                    rain = 20
                else:
                    rain = 5
                
                weather_text = f"আপনার বর্তমান অবস্থান {location} । এখন তাপমাত্রা {round(temp)}°C, অনুভুত হবে {round(feels_like)}°C -এর মত। আদ্রতা: {humidity}% ও বৃষ্টির সম্ভাবনা: {rain}%।"
                return JsonResponse({'weather': weather_text})
            else:
                return JsonResponse({'weather': "আবহাওয়ার তথ্য পাওয়া যায়নি।"}, status=400)
        else:
            return JsonResponse({'weather': "লোকেশন পাওয়া যায়নি।"}, status=400)
    return JsonResponse({'weather': "Invalid request."}, status=400)

@csrf_exempt
def predict_disease(request):
    if request.method == "POST" and request.FILES.get("image"):
        image_file = request.FILES["image"]

        api_key = settings.ROBOFLOW_API_KEY
        model = getattr(settings, "ROBOFLOW_MODEL", "plant-disease-detection-2")
        version = getattr(settings, "ROBOFLOW_VERSION", "1")
        url = f"https://detect.roboflow.com/{model}/{version}?api_key={api_key}"

        response = requests.post(
            url,
            files={"file": image_file},
            data={"name": image_file.name}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("predictions"):
                top_pred = max(result["predictions"], key=lambda x: x["confidence"])
                label = top_pred["class"]
                confidence = top_pred["confidence"]
                return JsonResponse({
                    "success": True,
                    "label": label,
                    "confidence": f"{confidence*100:.1f}%"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": "কোনো রোগ শনাক্ত করা যায়নি।"
                })
        else:
            return JsonResponse({
                "success": False,
                "error": "API তে সমস্যা হয়েছে।"
            })
    return JsonResponse({
        "success": False,
        "error": "ছবি আপলোড করুন।"
    })