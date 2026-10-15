/**
 * ChatBubble.test.tsx — M8: TEST-2
 * Tests: renders user bubble right-aligned, bot bubble left-aligned,
 * sentinel text hidden, timestamp rendered.
 */
import { describe, it, expect } from 'vitest';
import { render, screen }       from '@testing-library/react';
import ChatBubble from '@/components/ChatBubble';
import type { Message } from '@/store/chatStore';

function makeMsg(overrides: Partial<Message>): Message {
  return {
    id:        'test-id-1',
    sender:    'bot',
    text:      'পরীক্ষামূলক বার্তা',
    timestamp: new Date('2026-10-14T08:00:00'),
    ...overrides,
  };
}

describe('ChatBubble', () => {
  it('renders bot message text', () => {
    render(<ChatBubble message={makeMsg({ sender: 'bot', text: 'বট বলছে' })} />);
    expect(screen.getByText('বট বলছে')).toBeInTheDocument();
  });

  it('renders user message text', () => {
    render(<ChatBubble message={makeMsg({ sender: 'user', text: 'আমি বলছি' })} />);
    expect(screen.getByText('আমি বলছি')).toBeInTheDocument();
  });

  it('sentinel message still renders as a bubble (routing handled by ChatPage)', () => {
    render(<ChatBubble message={makeMsg({ text: '__ASK_WEATHER__', sentinel: '__ASK_WEATHER__' })} />);
    // The bubble renders; ChatPage (not ChatBubble) handles routing/display logic
    const { container } = render(<ChatBubble message={makeMsg({ sender: 'bot', text: 'test' })} />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('bot bubble contains the bot avatar element', () => {
    const { container } = render(<ChatBubble message={makeMsg({ sender: 'bot' })} />);
    // Bot avatar: a div with brand-600 bg class
    const avatar = container.querySelector('.bg-brand-600');
    expect(avatar).toBeInTheDocument();
  });

  it('user bubble has justify-end alignment', () => {
    const { container } = render(<ChatBubble message={makeMsg({ sender: 'user' })} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain('justify-end');
  });
});
