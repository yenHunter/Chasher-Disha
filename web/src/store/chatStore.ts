/**
 * store/chatStore.ts — Zustand store for chat messages + dark-mode toggle.
 * FRONT-4: clearChat, exportChat implemented here.
 * FRONT-7: dark mode persisted to localStorage.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Sender = 'user' | 'bot';

export interface Message {
  id:        string;   // client-side UUID
  sender:    Sender;
  text:      string;
  sentinel?: string;   // __ASK_WEATHER__ | __ASK_DISEASE__ | __ASK_FERTILIZER__
  timestamp: number;
}

interface ChatState {
  messages:  Message[];
  darkMode:  boolean;
  sessionLabel: string;
  addMessage:    (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;
  setDarkMode:   (on: boolean) => void;
  setSessionLabel: (label: string) => void;
  exportTxt: () => void;
}

let _counter = 0;
function uid() { return `msg-${Date.now()}-${++_counter}`; }

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages:     [],
      darkMode:     false,
      sessionLabel: 'চ্যাট ১',
      addMessage: (msg) =>
        set((s) => ({
          messages: [...s.messages, { ...msg, id: uid(), timestamp: Date.now() }],
        })),
      clearMessages: () => set({ messages: [] }),
      setDarkMode: (on) => {
        // Sync Tailwind dark class on <html> (FRONT-7)
        document.documentElement.classList.toggle('dark', on);
        set({ darkMode: on });
      },
      setSessionLabel: (label) => set({ sessionLabel: label }),
      exportTxt: () => {
        const { messages, sessionLabel } = get();
        const lines = messages.map(
          (m) =>
            `[${new Date(m.timestamp).toLocaleString('bn-BD')}] ${
              m.sender === 'user' ? 'আপনি' : 'বট'
            }: ${m.text}`,
        );
        const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `${sessionLabel}.txt`;
        a.click();
        URL.revokeObjectURL(url);
      },
    }),
    {
      name: 'chat-storage',
      // Only persist dark mode and session label — not message history
      partialize: (s) => ({ darkMode: s.darkMode, sessionLabel: s.sessionLabel }),
    },
  ),
);
