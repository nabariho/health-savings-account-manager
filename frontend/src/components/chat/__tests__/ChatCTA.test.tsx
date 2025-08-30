/**
 * Tests for ChatCTA (Call-to-Action) component.
 * 
 * Tests CTA display functionality including visibility logic, eligibility detection,
 * user interaction, custom content, and business logic for triggering the CTA.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ChatCTA, useCTAVisibility, hasEligibilityQuestions } from '../ChatCTA';
import type { CTAProps } from '@/types/hsaAssistant';

// Mock UI components
vi.mock('@/components/ui/Button', () => ({
  Button: ({ children, onClick, className, ...props }: any) => (
    <button onClick={onClick} className={className} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children, className }: any) => (
    <div className={className}>{children}</div>
  ),
}));

describe('ChatCTA', () => {
  const mockOnStartApplication = vi.fn();

  const defaultProps: CTAProps = {
    show: true,
    onStartApplication: mockOnStartApplication,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default content when show is true', () => {
    render(<ChatCTA {...defaultProps} />);
    
    expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
    expect(screen.getByText(/Based on our conversation, it looks like you might be eligible/)).toBeInTheDocument();
    expect(screen.getByText('Start HSA Application')).toBeInTheDocument();
  });

  it('does not render when show is false', () => {
    render(<ChatCTA {...defaultProps} show={false} />);
    
    expect(screen.queryByText('Ready to Open Your HSA?')).not.toBeInTheDocument();
    expect(screen.queryByText('Start HSA Application')).not.toBeInTheDocument();
  });

  it('renders with custom title and description', () => {
    const customProps: CTAProps = {
      ...defaultProps,
      title: 'Custom HSA Title',
      description: 'Custom HSA description text.',
      buttonText: 'Custom Button Text',
    };

    render(<ChatCTA {...customProps} />);
    
    expect(screen.getByText('Custom HSA Title')).toBeInTheDocument();
    expect(screen.getByText('Custom HSA description text.')).toBeInTheDocument();
    expect(screen.getByText('Custom Button Text')).toBeInTheDocument();
  });

  it('calls onStartApplication when button is clicked', async () => {
    const user = userEvent.setup();
    render(<ChatCTA {...defaultProps} />);
    
    const button = screen.getByText('Start HSA Application');
    await user.click(button);
    
    expect(mockOnStartApplication).toHaveBeenCalledTimes(1);
  });

  it('handles missing onStartApplication callback gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    
    render(<ChatCTA show={true} />);
    
    const button = screen.getByText('Start HSA Application');
    fireEvent.click(button);
    
    expect(consoleSpy).toHaveBeenCalledWith('Starting HSA application...');
    consoleSpy.mockRestore();
  });

  it('displays HSA benefits list', () => {
    render(<ChatCTA {...defaultProps} />);
    
    expect(screen.getByText('Tax deductible')).toBeInTheDocument();
    expect(screen.getByText('Tax-free growth')).toBeInTheDocument();
    expect(screen.getByText('No expiration')).toBeInTheDocument();
  });

  it('displays continue chatting option', () => {
    render(<ChatCTA {...defaultProps} />);
    
    expect(screen.getByText('Continue chatting')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const customClass = 'custom-cta-class';
    render(<ChatCTA {...defaultProps} className={customClass} />);
    
    const container = screen.getByText('Ready to Open Your HSA?').closest('.sticky');
    expect(container).toHaveClass(customClass);
  });

  it('has proper styling and visual elements', () => {
    render(<ChatCTA {...defaultProps} />);
    
    // Check for gradient background
    const card = screen.getByText('Ready to Open Your HSA?').closest('.bg-gradient-to-r');
    expect(card).toHaveClass('from-primary-500', 'to-primary-600', 'text-white');
    
    // Check for animation classes
    const container = screen.getByText('Ready to Open Your HSA?').closest('.sticky');
    expect(container).toHaveClass('animate-fade-in-up');
  });

  it('displays money icon SVG', () => {
    render(<ChatCTA {...defaultProps} />);
    
    // Check for SVG with money/dollar sign path
    const svg = screen.getByRole('img', { hidden: true });
    expect(svg).toBeInTheDocument();
  });

  it('has checkmark icons for benefits', () => {
    render(<ChatCTA {...defaultProps} />);
    
    // There should be 3 checkmark icons (one for each benefit)
    const checkmarks = screen.getAllByRole('img', { hidden: true }).filter(el => 
      el.getAttribute('fill') === 'currentColor' && 
      el.querySelector('path[fill-rule="evenodd"]')
    );
    expect(checkmarks).toHaveLength(3);
  });

  it('positions sticky at bottom with proper z-index', () => {
    render(<ChatCTA {...defaultProps} />);
    
    const container = screen.getByText('Ready to Open Your HSA?').closest('.sticky');
    expect(container).toHaveClass('bottom-4', 'z-10');
  });

  it('has proper responsive layout classes', () => {
    render(<ChatCTA {...defaultProps} />);
    
    // Benefits should have responsive grid
    const benefitsContainer = screen.getByText('Tax deductible').closest('.grid');
    expect(benefitsContainer).toHaveClass('grid-cols-1', 'md:grid-cols-3');
    
    // Buttons should have responsive flex
    const buttonsContainer = screen.getByText('Start HSA Application').closest('.flex');
    expect(buttonsContainer).toHaveClass('flex-col', 'sm:flex-row');
  });
});

describe('useCTAVisibility', () => {
  it('returns false for insufficient message count', () => {
    const result = useCTAVisibility(2, false);
    expect(result).toBe(false);
  });

  it('returns true for sufficient message count', () => {
    const result = useCTAVisibility(6, false);
    expect(result).toBe(true);
  });

  it('returns true when eligibility questions are detected regardless of count', () => {
    const result = useCTAVisibility(2, true);
    expect(result).toBe(true);
  });

  it('returns true when both conditions are met', () => {
    const result = useCTAVisibility(8, true);
    expect(result).toBe(true);
  });

  it('handles edge case of exactly 6 messages', () => {
    const result = useCTAVisibility(6, false);
    expect(result).toBe(true);
  });

  it('handles zero message count', () => {
    const result = useCTAVisibility(0, false);
    expect(result).toBe(false);
  });
});

describe('hasEligibilityQuestions', () => {
  it('detects "eligible" keyword', () => {
    const messages = ['Am I eligible for an HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "eligibility" keyword', () => {
    const messages = ['What are the eligibility requirements?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "qualify" keyword', () => {
    const messages = ['Do I qualify for an HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "qualified" keyword', () => {
    const messages = ['What expenses are qualified?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "can i" keyword phrase', () => {
    const messages = ['Can I open an HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "high deductible" keyword phrase', () => {
    const messages = ['I have a high deductible health plan'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "hdhp" abbreviation', () => {
    const messages = ['Do I need an HDHP for HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "contribute" keyword', () => {
    const messages = ['How much can I contribute to an HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "open" keyword', () => {
    const messages = ['How do I open an HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects "start" keyword', () => {
    const messages = ['How do I start an HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('is case insensitive', () => {
    const messages = ['AM I ELIGIBLE FOR AN HSA?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects keywords in mixed case', () => {
    const messages = ['Can I Qualify for an HSA with High Deductible plan?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('detects keywords in any message of the array', () => {
    const messages = [
      'What are HSA contribution limits?',
      'How does an HSA work?',
      'Am I eligible for an HSA?'
    ];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('returns false when no eligibility keywords are found', () => {
    const messages = [
      'What are the HSA contribution limits?',
      'How does an HSA work?',
      'What are the tax benefits?'
    ];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(false);
  });

  it('returns false for empty message array', () => {
    const messages: string[] = [];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(false);
  });

  it('handles partial word matches correctly', () => {
    const messages = ['I am not illegible for benefits']; // "illegible" contains "eligible"
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true); // Current implementation would match this
  });

  it('detects multiple keywords in single message', () => {
    const messages = ['Am I eligible to contribute to an HSA and can I open one?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('handles messages with special characters and punctuation', () => {
    const messages = ['Can I qualify? What about eligibility?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('handles very long messages', () => {
    const longMessage = 'I have been wondering about Health Savings Accounts and whether I might be eligible for one given my current health insurance situation and employment status...';
    const messages = [longMessage];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });

  it('handles messages with numbers and symbols', () => {
    const messages = ['Can I contribute $3,500 to an HSA in 2024?'];
    const result = hasEligibilityQuestions(messages);
    expect(result).toBe(true);
  });
});