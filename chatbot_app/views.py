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
# Weather  (M2: WX-1 Open-Meteo, WX-2 Nominatim, BUG-1 rain logic fixed)
# ---------------------------------------------------------------------------
@csrf_exempt   # temporary — replaced by JWT auth in M3/SEC-3
def get_weather(request):
    """
    POST /get_weather/
    Body: {"latitude": <float>, "longitude": <float>}

    Returns a Bangla weather summary built from Open-Meteo (no API key needed)
    with reverse-geocoded place name from Nominatim/OSM (WX-2).

    M2 implementation — replaces the M0 stub.
    """
    if request.method != "POST":
        return JsonResponse({"error": "শুধু POST অনুরোধ গ্রহণযোগ্য।"}, status=405)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "অনুরোধ বিন্যাস ভুল।"}, status=400)

    try:
        lat = float(body["latitude"])
        lon = float(body["longitude"])
    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {"error": "latitude ও longitude প্রয়োজন (দশমিক সংখ্যা)।"},
            status=400,
        )

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return JsonResponse(
            {"error": "latitude বা longitude এর মান সঠিক নয়।"},
            status=400,
        )

    from .weather import fetch_weather, WeatherServiceError  # noqa: PLC0415
    try:
        data = fetch_weather(lat, lon)
    except WeatherServiceError as exc:
        return JsonResponse(
            {"error": f"আবহাওয়া তথ্য পাওয়া যায়নি: {exc}"},
            status=503,
        )

    return JsonResponse({
        "weather":          data["message"],
        "agri_advice":      data["agri_advice"],
        "place":            data["place"],
        "condition":        data["condition"],
        "temperature":      data["temperature"],
        "humidity":         data["humidity"],
        "rain_probability": data["rain_probability"],
        "wind_speed":       data["wind_speed"],
        "uv_index":         data["uv_index"],
        "rain_3day_mm":     data["rain_3day"],
        "et0_3day_mm":      data["et0_3day"],
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
