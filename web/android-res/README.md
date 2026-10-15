# android-res/README.md — MOB-1 Android Resource Guide

## Contents

Place the following files in this directory before running `npx cap sync android`.
Capacitor will copy them into the correct Android Studio locations automatically.

---

## App icon

| File | Size | Location after sync |
|---|---|---|
| `icon.png` | 1024×1024 px | Source for adaptive icon |
| `icon-foreground.png` | 1024×1024 px, transparent background | Adaptive foreground layer |

**Design spec:** Use the সবুজ (green) leaf motif from the existing brand. Export from any design tool.  
**Tool:** After placing files, run `npx @capacitor/assets generate` to auto-generate all density variants.

---

## Splash screen

| File | Size |
|---|---|
| `splash.png` | 2732×2732 px (centred logo on white/green background) |

---

## AndroidManifest.xml permissions (auto-added by Capacitor plugins)

The following permissions are added automatically by Capacitor plugins when you run `npx cap sync`:

```xml
<!-- @capacitor/geolocation -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

<!-- @capacitor/camera -->
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />

<!-- Network state -->
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.INTERNET" />
```

No manual `AndroidManifest.xml` edits are needed for M7.

---

## First-time Android setup

```bash
# 1. Build the web app
npm run build              # outputs to web/dist/

# 2. Add Android platform (run ONCE)
npx cap add android

# 3. Sync web assets + plugins into Android project
npx cap sync android

# 4. Open in Android Studio
npx cap open android

# 5. In Android Studio: Build → Generate Signed Bundle/APK
#    Min SDK: API 29 (Android 10)
#    Target SDK: API 34 (Android 14)
```

---

## Live reload during development

1. Find your machine's LAN IP: `ipconfig | findstr IPv4`
2. In `capacitor.config.ts`, uncomment and set:
   ```ts
   server: { url: 'http://YOUR_LAN_IP:5173', cleartext: true }
   ```
3. Run `npm run dev` and connect the device to the same Wi-Fi.
4. `npx cap run android` — changes reflect instantly without rebuild.

---

## APK size targets (M7 acceptance criteria)

| Variant | Target |
|---|---|
| Without `rice_disease.onnx` | < 15 MB |
| With `rice_disease.onnx` (~4 MB) | < 20 MB |

ONNX model is excluded from the bundle until `web/src/assets/rice_disease.onnx` is placed.
