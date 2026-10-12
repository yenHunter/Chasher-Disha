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
# Disease detection  (M4: ML-4 — local YOLOv8-nano inference)
# ---------------------------------------------------------------------------
@csrf_exempt   # temporary — replaced by JWT auth in M3/SEC-3
def predict_disease(request):
    """
    POST /predict_disease/
    Body: multipart/form-data  — field name: "image"  (JPEG / PNG)

    Runs the locally-trained YOLOv8-nano model (rice_disease.pt) and returns
    the detected disease, confidence, Bangla name, management advice, and all
    detected bounding boxes.

    Response (success):
        {
          "success":        true,
          "disease":        "Blast",
          "disease_bn":     "ব্লাস্ট রোগ",
          "confidence":     "87.3%",
          "advice":         "ট্রাইসাইক্লাজল ছত্রাকনাশক ব্যবহার করুন।",
          "all_detections": [...]
        }

    Response (model not ready — weights file missing):
        HTTP 503  {"success": false, "error": "..."}

    M4 implementation — replaces the M0 stub.  (BUG-3: Roboflow fully removed)
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "শুধু POST অনুরোধ গ্রহণযোগ্য।"}, status=405)

    image_file = request.FILES.get("image")
    if not image_file:
        return JsonResponse({"success": False, "error": "ছবি আপলোড করুন।"}, status=400)

    # -- Basic file-type guard -----------------------------------------------
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    content_type  = getattr(image_file, "content_type", "").lower()
    if content_type and content_type not in allowed_types:
        return JsonResponse(
            {"success": False, "error": "শুধু JPEG বা PNG ছবি গ্রহণযোগ্য।"},
            status=400,
        )

    # -- File size guard (max 10 MB) -----------------------------------------
    MAX_SIZE_BYTES = 10 * 1024 * 1024
    if image_file.size > MAX_SIZE_BYTES:
        return JsonResponse(
            {"success": False, "error": "ছবির আকার ১০ MB-এর বেশি হওয়া উচিত নয়।"},
            status=400,
        )

    image_bytes = image_file.read()

    # -- Inference -----------------------------------------------------------
    from .ml.rice_disease import (  # noqa: PLC0415
        ModelNotReadyError,
        InferenceError,
        predict,
    )

    try:
        result = predict(image_bytes)
    except ModelNotReadyError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "রোগ শনাক্তকরণ মডেল এখনও প্রস্তুত নয়। "
                    "প্রশিক্ষণ শেষ হয়নি বা weights ফাইল নেই।"
                ),
                "detail": str(exc),
            },
            status=503,
        )
    except ValueError as exc:
        return JsonResponse(
            {"success": False, "error": f"ছবি পড়া যায়নি: {exc}"},
            status=400,
        )
    except InferenceError as exc:
        return JsonResponse(
            {"success": False, "error": f"মডেল ত্রুটি: {exc}"},
            status=500,
        )

    return JsonResponse({
        "success":        result["success"],
        "disease":        result["disease"],
        "disease_bn":     result["disease_bn"],
        "confidence":     f"{result['confidence'] * 100:.1f}%",
        "advice":         result["advice"],
        "all_detections": result["all_detections"],
    })
