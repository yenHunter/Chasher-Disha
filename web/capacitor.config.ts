import { CapacitorConfig } from '@capacitor/cli';

/**
 * capacitor.config.ts — Chasher-Disha Android/iOS configuration.
 * M7: FRONT-9 / MOB-1
 *
 * After first build:
 *   npx cap add android
 *   npx cap sync android
 *   npx cap open android        ← opens Android Studio
 */
const config: CapacitorConfig = {
  appId:   'com.chasher_disha.app',
  appName: 'চাষের দিশা',
  webDir:  'dist',              // Vite output directory

  // --- Server (dev only) ---------------------------------------------------
  // Uncomment for live-reload during Android development:
  // server: { url: 'http://YOUR_LAN_IP:5173', cleartext: true },

  // --- Plugins -------------------------------------------------------------
  plugins: {
    // Geolocation: fine accuracy for weather fetch
    Geolocation: {
      permissions: ['location'],
    },
    // Camera: pick from gallery or capture for disease detection
    Camera: {
      permissions: ['camera', 'photos'],
    },
    // Preferences: persistent KV store (replaces localStorage for offline data)
    Preferences: {},
    // Network: online/offline listener
    Network: {},
  },

  // --- Android-specific ----------------------------------------------------
  android: {
    allowMixedContent: false,    // HTTPS only in prod
    captureInput: true,          // fixes Bangla IME soft keyboard
    webContentsDebuggingEnabled: false,  // set true during development
  },
};

export default config;
