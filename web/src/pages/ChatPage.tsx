/**
 * pages/ChatPage.tsx — Main chat interface.
 * Handles text chat, disease image upload sentinel routing, and weather sentinel.
 */
import { useEffect, useRef, useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useChat }      from '@/hooks/useChat';
import { useWeather }   from '@/hooks/useWeather';
import { detectDisease, apiErrorMessage } from '@/api/endpoints';
import ChatBubble    from '@/components/ChatBubble';
import MessageInput  from '@/components/MessageInput';
import WeatherCard   from '@/components/WeatherCard';
import DiseaseResult from '@/components/DiseaseResult';
import { DiseaseResponse } from '@/api/endpoints';
import bn from '@/i18n/bn';

export default function ChatPage() {
  const messages   = useChatStore((s) => s.messages);
  const addMessage = useChatStore((s) => s.addMessage);
  const { submit, loading } = useChat();
  const weather = useWeather();
  const bottomRef = useRef<HTMLDivElement>(null);

  const [diseaseResult, setDiseaseResult] = useState<DiseaseResponse | null>(null);
  const [diseaseLoading, setDiseaseLoading] = useState(false);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(text: string) {
    const sentinel = await submit(text);
    if (sentinel === '__ASK_WEATHER__') {
      weather.load();
    }
  }

  async function handleImageUpload(file: File) {
    addMessage({ sender: 'user', text: `📷 ${file.name}` });
    setDiseaseLoading(true);
    setDiseaseResult(null);
    try {
      const result = await detectDisease(file);
      setDiseaseResult(result);
      addMessage({
        sender: 'bot',
        text: result.disease === 'Healthy'
          ? `✅ ${bn.healthy}`
          : `🔬 ${result.disease_bn} (${result.confidence})`,
      });
    } catch (err) {
      const msg = apiErrorMessage(err);
      // Show specific Bangla message for model-not-ready (503)
      addMessage({
        sender: 'bot',
        text: msg.includes('প্রস্তুত') ? bn.modelNotReady : `⚠️ ${msg}`,
      });
    } finally {
      setDiseaseLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1 scrollbar-thin">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 dark:text-gray-500 text-sm">{bn.emptyChat}</p>
          </div>
        )}
        {messages.map((msg) => <ChatBubble key={msg.id} message={msg} />)}

        {/* Inline weather card after weather sentinel */}
        {weather.loading && (
          <p className="text-xs text-center text-gray-400">{bn.locating}</p>
        )}
        {weather.error && (
          <p className="text-xs text-center text-red-400">{weather.error}</p>
        )}
        {weather.data && !weather.loading && (
          <div className="max-w-sm mx-auto">
            <WeatherCard data={weather.data} />
          </div>
        )}

        {/* Inline disease result */}
        {diseaseLoading && (
          <p className="text-xs text-center text-gray-400">{bn.analyzing}</p>
        )}
        {diseaseResult && !diseaseLoading && (
          <div className="max-w-sm mx-auto">
            <DiseaseResult data={diseaseResult} />
          </div>
        )}

        {loading && (
          <div className="flex justify-start mb-3">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl px-4 py-2.5 text-sm text-gray-400">
              {bn.thinking}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSend={handleSend}
        onImageUpload={handleImageUpload}
        disabled={loading || diseaseLoading}
      />
    </div>
  );
}
