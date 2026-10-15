/**
 * App.tsx — Root component.
 * M7: mounts useNetworkWatcher + OfflineBanner.
 */
import { useEffect } from 'react';
import { useAuthStore }      from '@/store/authStore';
import { useChatStore }      from '@/store/chatStore';
import { useNetworkWatcher } from '@/hooks/useNetworkWatcher';
import LoginPage      from '@/pages/LoginPage';
import ChatPage       from '@/pages/ChatPage';
import WeatherPage    from '@/pages/WeatherPage';
import DiseasePage    from '@/pages/DiseasePage';
import FertilizerPage from '@/pages/FertilizerPage';
import Sidebar        from '@/components/Sidebar';
import OfflineBanner  from '@/components/OfflineBanner';
import { useState } from 'react';

type Page = 'chat' | 'weather' | 'disease' | 'fertilizer';

export default function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const darkMode        = useChatStore((s) => s.darkMode);
  const [page, setPage] = useState<Page>('chat');

  // M7: initialise network watcher (OFFLINE-5)
  useNetworkWatcher();

  // Sync Tailwind dark class on first load (FRONT-7)
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  if (!isAuthenticated) return <LoginPage />;

  const PageComponent: Record<Page, React.FC> = {
    chat:       ChatPage,
    weather:    WeatherPage,
    disease:    DiseasePage,
    fertilizer: FertilizerPage,
  };
  const Current = PageComponent[page];

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-white dark:bg-gray-900">
      {/* OFFLINE-5: banner at top when no internet */}
      <OfflineBanner />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar onNavigate={setPage} />
        <main className="flex-1 overflow-hidden flex flex-col">
          <Current />
        </main>
      </div>
    </div>
  );
}
