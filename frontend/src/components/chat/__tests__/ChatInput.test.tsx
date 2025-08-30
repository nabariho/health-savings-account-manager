/**
 * Tests for ChatInput component.
 * 
 * Tests message input functionality including form submission, validation,
 * keyboard shortcuts, example questions, character limits, and accessibility.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ChatInput } from '../ChatInput';
import type { ChatInputProps } from '@/types/hsaAssistant';

describe('ChatInput', () => {
  const mockOnSendMessage = vi.fn();

  const defaultProps: ChatInputProps = {
    onSendMessage: mockOnSendMessage,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with default props', () => {
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveAttribute('placeholder', 'Ask me anything about HSA rules and eligibility...');
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeInTheDocument();
    expect(sendButton).toBeDisabled();
  });

  it('renders with custom placeholder', () => {
    const customPlaceholder = 'Custom placeholder text';
    render(<ChatInput {...defaultProps} placeholder={customPlaceholder} />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('placeholder', customPlaceholder);
  });

  it('enables send button when message is typed', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    expect(sendButton).toBeDisabled();
    
    await user.type(textarea, 'Test message');
    expect(sendButton).not.toBeDisabled();
  });

  it('sends message on form submission', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    const message = 'What are HSA contribution limits?';
    
    await user.type(textarea, message);
    await user.click(screen.getByRole('button', { name: /send/i }));
    
    expect(mockOnSendMessage).toHaveBeenCalledWith(message);
    expect(textarea).toHaveValue('');
  });

  it('sends message on Enter key press', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    const message = 'Am I eligible for HSA?';
    
    await user.type(textarea, message);
    await user.keyboard('{Enter}');
    
    expect(mockOnSendMessage).toHaveBeenCalledWith(message);
    expect(textarea).toHaveValue('');
  });

  it('adds new line on Shift+Enter', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    await user.type(textarea, 'Line 1');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    await user.type(textarea, 'Line 2');
    
    expect(textarea).toHaveValue('Line 1\nLine 2');
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('trims whitespace from messages', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    const message = '  Test message with whitespace  ';
    
    await user.type(textarea, message);
    await user.click(screen.getByRole('button', { name: /send/i }));
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message with whitespace');
  });

  it('does not send empty messages', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    await user.type(textarea, '   ');
    await user.keyboard('{Enter}');
    
    expect(mockOnSendMessage).not.toHaveBeenCalled();
    expect(textarea).toHaveValue('   ');
  });

  it('shows character count', () => {
    render(<ChatInput {...defaultProps} />);
    
    expect(screen.getByText('500 characters remaining')).toBeInTheDocument();
  });

  it('updates character count as user types', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    const message = 'Test message';
    
    await user.type(textarea, message);
    
    expect(screen.getByText(`${500 - message.length} characters remaining`)).toBeInTheDocument();
  });

  it('highlights character count when near limit', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    // Type 451 characters (49 remaining, which is <= 50)
    const longMessage = 'x'.repeat(451);
    
    await user.type(textarea, longMessage);
    
    const characterCount = screen.getByText('49 characters remaining');
    expect(characterCount).toHaveClass('text-yellow-600', 'font-medium');
  });

  it('enforces character limit', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('maxLength', '500');
  });

  it('shows example questions on focus when input is empty', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    expect(screen.queryByText('Example questions:')).not.toBeInTheDocument();
    
    await user.click(textarea);
    
    expect(screen.getByText('Example questions:')).toBeInTheDocument();
    expect(screen.getByText('What are the HSA contribution limits for 2024?')).toBeInTheDocument();
  });

  it('does not show example questions on focus when input has text', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    await user.type(textarea, 'Some text');
    await user.click(textarea);
    
    expect(screen.queryByText('Example questions:')).not.toBeInTheDocument();
  });

  it('selects example question when clicked', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    await user.click(textarea);
    
    const exampleQuestion = screen.getByText('What are the HSA contribution limits for 2024?');
    await user.click(exampleQuestion);
    
    expect(textarea).toHaveValue('What are the HSA contribution limits for 2024?');
    expect(screen.queryByText('Example questions:')).not.toBeInTheDocument();
  });

  it('hides example questions on blur', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    await user.click(textarea);
    expect(screen.getByText('Example questions:')).toBeInTheDocument();
    
    await user.click(document.body);
    
    // Wait for the timeout in handleBlur
    await waitFor(() => {
      expect(screen.queryByText('Example questions:')).not.toBeInTheDocument();
    });
  });

  it('hides example questions on Escape key', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    await user.click(textarea);
    expect(screen.getByText('Example questions:')).toBeInTheDocument();
    
    await user.keyboard('{Escape}');
    
    expect(screen.queryByText('Example questions:')).not.toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(<ChatInput {...defaultProps} disabled={true} />);
    
    const textarea = screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    expect(textarea).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('does not send message when disabled', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} disabled={true} />);
    
    const textarea = screen.getByRole('textbox');
    
    // Try to type (should not work)
    await user.type(textarea, 'Test message');
    await user.keyboard('{Enter}');
    
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('shows keyboard shortcuts hint when not disabled', () => {
    render(<ChatInput {...defaultProps} />);
    
    expect(screen.getByText('Press Enter to send, Shift+Enter for new line')).toBeInTheDocument();
  });

  it('does not show keyboard shortcuts hint when disabled', () => {
    render(<ChatInput {...defaultProps} disabled={true} />);
    
    expect(screen.queryByText('Press Enter to send, Shift+Enter for new line')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const customClass = 'custom-chat-input';
    render(<ChatInput {...defaultProps} className={customClass} />);
    
    const container = screen.getByRole('textbox').closest('.relative');
    expect(container).toHaveClass(customClass);
  });

  it('auto-resizes textarea based on content', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    // Initial height should be auto
    expect(textarea.style.height).toBe('');
    
    // Add multiple lines
    await user.type(textarea, 'Line 1\nLine 2\nLine 3\nLine 4');
    
    // Height should be set after typing
    await waitFor(() => {
      expect(textarea.style.height).not.toBe('');
    });
  });

  it('resets textarea height after sending message', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    
    await user.type(textarea, 'Line 1\nLine 2\nLine 3');
    await user.keyboard('{Enter}');
    
    expect(mockOnSendMessage).toHaveBeenCalled();
    
    // Height should be reset to auto after sending
    await waitFor(() => {
      expect(textarea.style.height).toBe('auto');
    });
  });

  it('has proper accessibility attributes', () => {
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    expect(textarea).toBeInTheDocument();
    expect(sendButton).toBeInTheDocument();
    
    // Check that form is properly structured
    const form = textarea.closest('form');
    expect(form).toBeInTheDocument();
  });

  it('focuses textarea on mount when not disabled', () => {
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveFocus();
  });

  it('does not focus textarea on mount when disabled', () => {
    render(<ChatInput {...defaultProps} disabled={true} />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).not.toHaveFocus();
  });

  it('handles all example questions correctly', async () => {
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} />);
    
    const textarea = screen.getByRole('textbox');
    await user.click(textarea);
    
    // Check all example questions are present
    const expectedQuestions = [
      "What are the HSA contribution limits for 2024?",
      "Am I eligible for an HSA if I have other health insurance?",
      "Can I use my HSA for dental expenses?",
      "What happens to my HSA when I turn 65?",
    ];
    
    expectedQuestions.forEach(question => {
      expect(screen.getByText(question)).toBeInTheDocument();
    });
    
    // Test selecting each example
    for (const question of expectedQuestions) {
      await user.click(screen.getByText(question));
      expect(textarea).toHaveValue(question);
      
      // Clear and try next
      await user.clear(textarea);
      await user.click(textarea);
    }
  });
});