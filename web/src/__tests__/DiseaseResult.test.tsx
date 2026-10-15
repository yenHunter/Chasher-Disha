/**
 * DiseaseResult.test.tsx — M8: TEST-2
 * Tests: disease name rendered in Bangla, confidence badge visible,
 * advice text rendered, Healthy class has green badge.
 */
import { describe, it, expect } from 'vitest';
import { render, screen }       from '@testing-library/react';
import DiseaseResult from '@/components/DiseaseResult';
import type { DiseaseResponse } from '@/api/endpoints';

const blastResult: DiseaseResponse = {
  success:        true,
  disease:        'Blast',
  disease_bn:     'ব্লাস্ট রোগ',
  confidence:     '87.3%',
  advice:         'ট্রাইসাইক্লাজল ছত্রাকনাশক ব্যবহার করুন।',
  all_detections: [],
};

const healthyResult: DiseaseResponse = {
  success:        true,
  disease:        'Healthy',
  disease_bn:     'সুস্থ গাছ',
  confidence:     '95.1%',
  advice:         'গাছ সুস্থ আছে।',
  all_detections: [],
};

describe('DiseaseResult', () => {
  it('renders the Bangla disease name', () => {
    render(<DiseaseResult data={blastResult} />);
    expect(screen.getByText('ব্লাস্ট রোগ')).toBeInTheDocument();
  });

  it('renders the confidence percentage', () => {
    render(<DiseaseResult data={blastResult} />);
    expect(screen.getByText('87.3%')).toBeInTheDocument();
  });

  it('renders the advice text', () => {
    render(<DiseaseResult data={blastResult} />);
    expect(screen.getByText(/ট্রাইসাইক্লাজল/)).toBeInTheDocument();
  });

  it('Healthy result renders with green styling', () => {
    const { container } = render(<DiseaseResult data={healthyResult} />);
    // Green badge class for Healthy
    expect(container.innerHTML).toContain('green');
  });

  it('non-Healthy result does not use only green classes', () => {
    const { container } = render(<DiseaseResult data={blastResult} />);
    // Blast should have red badge, not just green
    expect(container.innerHTML).toContain('red');
  });
});
