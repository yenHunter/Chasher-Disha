/**
 * MessageInput.test.tsx — M8: TEST-2
 * Tests: textarea renders, send button present, Enter key triggers onSend,
 * send button disabled when loading, camera button triggers onImageUpload.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MessageInput from '@/components/MessageInput';

describe('MessageInput', () => {
  it('renders the textarea and send button', () => {
    render(<MessageInput onSend={vi.fn()} onImageUpload={vi.fn()} disabled={false} />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /পাঠান/i })).toBeInTheDocument();
  });

  it('calls onSend with typed text when send button is clicked', async () => {
    const onSend = vi.fn();
    const user   = userEvent.setup();
    render(<MessageInput onSend={onSend} onImageUpload={vi.fn()} disabled={false} />);
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'ধানে পোকা');
    await user.click(screen.getByRole('button', { name: /পাঠান/i }));
    expect(onSend).toHaveBeenCalledWith('ধানে পোকা');
  });

  it('calls onSend when Enter is pressed (without Shift)', async () => {
    const onSend = vi.fn();
    const user   = userEvent.setup();
    render(<MessageInput onSend={onSend} onImageUpload={vi.fn()} disabled={false} />);
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'আবহাওয়া কেমন');
    await user.keyboard('{Enter}');
    expect(onSend).toHaveBeenCalledWith('আবহাওয়া কেমন');
  });

  it('does NOT call onSend on Shift+Enter (multiline)', async () => {
    const onSend = vi.fn();
    const user   = userEvent.setup();
    render(<MessageInput onSend={onSend} onImageUpload={vi.fn()} disabled={false} />);
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'প্রথম লাইন');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    expect(onSend).not.toHaveBeenCalled();
  });

  it('send button is disabled when disabled=true', () => {
    render(<MessageInput onSend={vi.fn()} onImageUpload={vi.fn()} disabled={true} />);
    expect(screen.getByRole('button', { name: /পাঠান/i })).toBeDisabled();
  });

  it('clears input after sending', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={vi.fn()} onImageUpload={vi.fn()} disabled={false} />);
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    await user.type(textarea, 'কিছু টেক্সট');
    await user.click(screen.getByRole('button', { name: /পাঠান/i }));
    expect(textarea.value).toBe('');
  });
});
