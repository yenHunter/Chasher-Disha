/**
 * components/OfflineBanner.tsx
 * M7: OFFLINE-5 — Displays a Bangla offline warning bar at the top of the screen.
 */
import { useNetworkStore } from '@/store/networkStore';

export default function OfflineBanner() {
  const isOnline = useNetworkStore((s) => s.isOnline);
  if (isOnline) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full bg-amber-500 text-white text-center text-xs font-semibold py-1.5 px-4 z-50"
    >
      📵 অফলাইন — সীমিত সেবা পাওয়া যাচ্ছে। ইন্টারনেট সংযোগ নেই।
    </div>
  );
}
