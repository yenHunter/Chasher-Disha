/**
 * lib/capacitorBridge.ts
 * M7: platform abstraction layer.
 *
 * Detects whether the app is running inside a Capacitor WebView (Android/iOS)
 * or as a plain web browser, and re-exports the correct implementations of:
 *   - network status / listener
 *   - persistent preferences (KV store)
 *   - geolocation
 *   - camera / file picker
 *
 * Web browsers fall back to Web APIs; Capacitor targets use native plugins.
 * This means the React components never import @capacitor/* directly —
 * they always import from this module, keeping them testable in plain Vitest.
 */

import { Capacitor } from '@capacitor/core';

// ---------- Re-export Capacitor flag ----------------------------------------
export const isNative = Capacitor.isNativePlatform();

// ---------- Network ----------------------------------------------------------
export type NetworkStatus = { connected: boolean; connectionType: string };

export async function getNetworkStatus(): Promise<NetworkStatus> {
  if (isNative) {
    const { Network } = await import('@capacitor/network');
    return Network.getStatus();
  }
  return { connected: navigator.onLine, connectionType: 'unknown' };
}

export async function addNetworkListener(
  cb: (status: NetworkStatus) => void,
): Promise<() => void> {
  if (isNative) {
    const { Network } = await import('@capacitor/network');
    const handle = await Network.addListener('networkStatusChange', cb);
    return () => handle.remove();
  }
  const online  = () => cb({ connected: true,  connectionType: 'unknown' });
  const offline = () => cb({ connected: false, connectionType: 'none' });
  window.addEventListener('online',  online);
  window.addEventListener('offline', offline);
  return () => {
    window.removeEventListener('online',  online);
    window.removeEventListener('offline', offline);
  };
}

// ---------- Preferences (persistent KV) -------------------------------------
export async function prefGet(key: string): Promise<string | null> {
  if (isNative) {
    const { Preferences } = await import('@capacitor/preferences');
    const { value } = await Preferences.get({ key });
    return value;
  }
  return localStorage.getItem(key);
}

export async function prefSet(key: string, value: string): Promise<void> {
  if (isNative) {
    const { Preferences } = await import('@capacitor/preferences');
    await Preferences.set({ key, value });
  } else {
    localStorage.setItem(key, value);
  }
}

export async function prefRemove(key: string): Promise<void> {
  if (isNative) {
    const { Preferences } = await import('@capacitor/preferences');
    await Preferences.remove({ key });
  } else {
    localStorage.removeItem(key);
  }
}

// ---------- Geolocation ------------------------------------------------------
export interface GeoPosition { latitude: number; longitude: number }

export async function getCurrentPosition(): Promise<GeoPosition> {
  if (isNative) {
    const { Geolocation } = await import('@capacitor/geolocation');
    const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true });
    return { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
  }
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ latitude: p.coords.latitude, longitude: p.coords.longitude }),
      reject,
      { timeout: 8000 },
    );
  });
}

// ---------- Camera / file picker (OFFLINE-3, FRONT-5) -----------------------
export interface PhotoResult { dataUrl: string; mimeType: string }

export async function pickPhoto(): Promise<PhotoResult | null> {
  if (isNative) {
    const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera');
    const photo = await Camera.getPhoto({
      resultType: CameraResultType.DataUrl,
      source:     CameraSource.Prompt,   // Ask user: Camera or Gallery
      quality:    85,
    });
    return {
      dataUrl:  photo.dataUrl ?? '',
      mimeType: `image/${photo.format}`,
    };
  }
  // Web: trigger a file-input click (handled by MessageInput / DiseasePage)
  return null;
}
