/**
 * store/networkStore.ts
 * M7: OFFLINE-4, OFFLINE-5 — Network status Zustand store.
 *
 * Initialised once on app mount via useNetworkWatcher hook.
 * Components read `useNetworkStore(s => s.isOnline)` reactively.
 */
import { create } from 'zustand';

interface NetworkState {
  isOnline:       boolean;
  connectionType: string;
  setStatus: (connected: boolean, connectionType: string) => void;
}

export const useNetworkStore = create<NetworkState>((set) => ({
  isOnline:       true,    // optimistic default
  connectionType: 'unknown',
  setStatus: (connected, connectionType) => set({ isOnline: connected, connectionType }),
}));
