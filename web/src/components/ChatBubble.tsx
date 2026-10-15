/** components/ChatBubble.tsx — Single chat message bubble. */
import { Message } from '@/store/chatStore';
import bn from '@/i18n/bn';

interface Props { message: Message }

export default function ChatBubble({ message }: Props) {
  const isUser = message.sender === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold mr-2 flex-shrink-0 mt-1">
          চা
        </div>
      )}
      <div
        className={`max-w-[78%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm
          ${isUser
            ? 'bg-brand-600 text-white rounded-br-sm'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-sm'
          }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.text}</p>
        <p className={`text-xs mt-1 ${isUser ? 'text-brand-200 text-right' : 'text-gray-400'}`}>
          {new Date(message.timestamp).toLocaleTimeString('bn-BD', {
            hour: '2-digit', minute: '2-digit',
          })}
        </p>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-700 dark:text-gray-200 text-xs font-bold ml-2 flex-shrink-0 mt-1">
          {bn.youLabel[0]}
        </div>
      )}
    </div>
  );
}
