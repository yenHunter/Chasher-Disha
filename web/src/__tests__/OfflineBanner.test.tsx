/**
 * OfflineBanner.test.tsx — M8: TEST-2
 * Tests: banner hidden when online, banner visible when offline,
 * correct Bangla text, accessible role.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen }                   from '@testing-library/react';
import OfflineBanner from '@/components/OfflineBanner';
import { useNetworkStore }                  from '@/store/networkStore';

// Helper to directly set the Zustand store state in tests
function setOnline(connected: boolean) {
  useNetworkStore.setState({ isOnline: connected, connectionType: connected ? 'wifi' : 'none' });
}

describe('OfflineBanner', () => {
  beforeEach(() => {
    // Reset to online before each test
    setOnline(true);
  });

  it('renders nothing when online', () => {
    setOnline(true);
    const { container } = render(<OfflineBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the banner when offline', () => {
    setOnline(false);
    render(<OfflineBanner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('contains Bangla offline text', () => {
    setOnline(false);
    render(<OfflineBanner />);
    expect(screen.getByText(/অফলাইন/)).toBeInTheDocument();
  });

  it('has aria-live="polite" for screen readers', () => {
    setOnline(false);
    render(<OfflineBanner />);
    const banner = screen.getByRole('status');
    expect(banner).toHaveAttribute('aria-live', 'polite');
  });

  it('disappears after going back online', () => {
    setOnline(false);
    const { rerender } = render(<OfflineBanner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    setOnline(true);
    rerender(<OfflineBanner />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
