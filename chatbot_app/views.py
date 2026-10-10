import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .nlp_model import get_response

# ---------------------------------------------------------------------------
# Home — serves the current Django template (will be replaced by React in M6)
# ---------------------------------------------------------------------------
def home(request):
    return render(request, "index.html")


# ---------------------------------------------------------------------------
# Chat  (M0: BUG-2 guard added; full REST migration in M3)
# ---------------------------------------------------------------------------
def chat(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user_input = request.GET.get("message", "").strip()
    if not user_input:
        return JsonResponse({"response": "দুঃখিত, আমি কিছুই পাইনি 😔"})

    bot_response = get_response(user_input)
    return JsonResponse({"response": bot_response})


# ---------------------------------------------------------------------------
# Weather  (M0 stub — OpenWeatherMap removed; full Open-Meteo impl in M2)
# ---------------------------------------------------------------------------
@csrf_exempt   # temporary — replaced by JWT auth in M3/SEC-3
def get_weather(request):
    """
    STUB: OpenWeatherMap removed in M0 (no API key required for Open-Meteo).
    Full implementation with Open-Meteo API lands in M2.
    """
    if request.method != 'POST':
        return JsonResponse({'weather': "Invalid request."}, status=400)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'weather': "অনুরোধ বিন্যাস ভুল।"}, status=400)

    lat = data.get('latitude')
    lon = data.get('longitude')

    if not (lat and lon):
        return JsonResponse({'weather': "লোকেশন পাওয়া যায়নি।"}, status=400)

    # TODO (M2/WX-1): replace with Open-Meteo API call
    return JsonResponse({
        'weather': "আবহাওয়া সার্ভিস আপগ্রেড চলছে। শীঘ্রই পুনরায় পাওয়া যাবে।"
    })


# ---------------------------------------------------------------------------
# Disease detection  (M0 stub — Roboflow removed; full YOLO impl in M4)
# ---------------------------------------------------------------------------
@csrf_exempt   # temporary — replaced by JWT auth in M3/SEC-3
def predict_disease(request):
    """
    STUB: Roboflow cloud API removed in M0.
    Full implementation with local YOLOv8-nano model lands in M4.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)

    if not request.FILES.get("image"):
        return JsonResponse({"success": False, "error": "ছবি আপলোড করুন।"}, status=400)

    # TODO (M4/ML-4): replace with local YOLO inference
    return JsonResponse({
        "success": False,
        "error": "রোগ শনাক্তকরণ সার্ভিস আপগ্রেড চলছে। শীঘ্রই পুনরায় পাওয়া যাবে।"
    })
