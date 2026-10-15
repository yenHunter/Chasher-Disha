/**
 * hooks/useNetworkWatcher.ts
 * M7: OFFLINE-5 — Initialises and subscribes to network status changes.
 * Call once in App.tsx on mount.
 */
import { useEffect } from 'react';
import { getNetworkStatus, addNetworkListener } from '@/lib/capacitorBridge';
import { useNetworkStore } from '@/store/networkStore';

export function useNetworkWatcher() {
  const setStatus = useNetworkStore((s) => s.setStatus);

  useEffect(() => {
    // Seed initial status
    getNetworkStatus().then((s) => setStatus(s.connected, s.connectionType));

    // Subscribe to changes
    let removeListener: (() => void) | null = null;
    addNetworkListener((s) => setStatus(s.connected, s.connectionType))
      .then((remove) => { removeListener = remove; });

    return () => { removeListener?.(); };
  }, [setStatus]);
}
