/**
 * hooks/useChat.ts
 * M7: OFFLINE-1 update — Falls back to offlineLookup when network is unavailable.
 */
import { useState } from 'react';
import { sendChat, apiErrorMessage } from '@/api/endpoints';
import { useChatStore }  from '@/store/chatStore';
import { useNetworkStore } from '@/store/networkStore';
import { offlineLookup } from '@/lib/offlineNlp';

export function useChat() {
  const addMessage = useChatStore((s) => s.addMessage);
  const isOnline   = useNetworkStore((s) => s.isOnline);
  const [loading, setLoading] = useState(false);

  async function submit(text: string): Promise<string | undefined> {
    if (!text.trim()) return;
    addMessage({ sender: 'user', text });
    setLoading(true);
    try {
      if (!isOnline) {
        // OFFLINE-1: local bigram intent lookup
        const response = await offlineLookup(text);
        addMessage({ sender: 'bot', text: response, sentinel: response.startsWith('__') ? response : undefined });
        return response.startsWith('__') ? response : undefined;
      }
      const res = await sendChat(text);
      addMessage({ sender: 'bot', text: res.response, sentinel: res.sentinel });
      return res.sentinel;
    } catch (err) {
      const msg = apiErrorMessage(err);
      addMessage({ sender: 'bot', text: `⚠️ ${msg}` });
    } finally {
      setLoading(false);
    }
  }

  return { submit, loading };
}
