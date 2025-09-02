/**
 * Comprehensive tests for RichTextRenderer component.
 * 
 * Tests rich text formatting support including:
 * - Bold, italics, and code span formatting
 * - Bullet points and numbered lists
 * - Headers and structured content
 * - Link rendering with proper attributes
 * - Whitespace preservation and line breaks
 * - Edge cases and security considerations
 * - Compact vs normal spacing modes
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { RichTextRenderer, InlineRichText } from '../RichTextRenderer';

describe('RichTextRenderer', () => {
  describe('Basic Formatting', () => {
    it('renders plain text without formatting', () => {
      const content = 'This is plain text content.';
      render(<RichTextRenderer content={content} />);
      
      expect(screen.getByText(content)).toBeInTheDocument();
    });

    it('renders bold text with **bold** syntax', () => {
      const content = 'This is **bold text** in a sentence.';
      render(<RichTextRenderer content={content} />);
      
      const boldElement = document.querySelector('strong');
      expect(boldElement).toBeInTheDocument();
      expect(boldElement).toHaveTextContent('bold text');
      expect(boldElement).toHaveClass('font-semibold');
    });

    it('renders bold text with __bold__ syntax', () => {
      const content = 'This is __bold text__ in a sentence.';
      render(<RichTextRenderer content={content} />);
      
      const boldElement = document.querySelector('strong');
      expect(boldElement).toBeInTheDocument();
      expect(boldElement).toHaveTextContent('bold text');
    });

    it('renders italic text with *italic* syntax', () => {
      const content = 'This is *italic text* in a sentence.';
      render(<RichTextRenderer content={content} />);
      
      const italicElement = document.querySelector('em');
      expect(italicElement).toBeInTheDocument();
      expect(italicElement).toHaveTextContent('italic text');
      expect(italicElement).toHaveClass('italic');
    });

    it('renders italic text with _italic_ syntax', () => {
      const content = 'This is _italic text_ in a sentence.';
      render(<RichTextRenderer content={content} />);
      
      const italicElement = document.querySelector('em');
      expect(italicElement).toBeInTheDocument();
      expect(italicElement).toHaveTextContent('italic text');
    });

    it('renders code spans with proper styling', () => {
      const content = 'Use the `navigator.clipboard` API for copying.';
      render(<RichTextRenderer content={content} />);
      
      const codeElement = document.querySelector('code');
      expect(codeElement).toBeInTheDocument();
      expect(codeElement).toHaveTextContent('navigator.clipboard');
      expect(codeElement).toHaveClass('bg-gray-100', 'px-1', 'py-0.5', 'rounded', 'text-sm', 'font-mono');
    });

    it('handles multiple formatting types in same text', () => {
      const content = 'This has **bold**, *italic*, and `code` formatting.';
      render(<RichTextRenderer content={content} />);
      
      expect(document.querySelector('strong')).toHaveTextContent('bold');
      expect(document.querySelector('em')).toHaveTextContent('italic');
      expect(document.querySelector('code')).toHaveTextContent('code');
    });

    it('handles nested formatting correctly', () => {
      const content = 'This has **bold with *italic* inside** formatting.';
      render(<RichTextRenderer content={content} />);
      
      const boldElement = document.querySelector('strong');
      expect(boldElement).toBeInTheDocument();
      
      const italicElement = document.querySelector('em');
      expect(italicElement).toBeInTheDocument();
    });
  });

  describe('Link Rendering', () => {
    it('renders links with proper attributes', () => {
      const content = 'Visit [HSA Information](https://www.irs.gov/hsa) for details.';
      render(<RichTextRenderer content={content} />);
      
      const linkElement = document.querySelector('a');
      expect(linkElement).toBeInTheDocument();
      expect(linkElement).toHaveTextContent('HSA Information');
      expect(linkElement).toHaveAttribute('href', 'https://www.irs.gov/hsa');
      expect(linkElement).toHaveAttribute('target', '_blank');
      expect(linkElement).toHaveAttribute('rel', 'noopener noreferrer');
      expect(linkElement).toHaveClass('text-primary-600', 'hover:text-primary-700', 'underline');
    });

    it('handles multiple links in same text', () => {
      const content = 'Check [IRS HSA Rules](https://irs.gov/hsa) and [Bank HSA Info](https://bank.com/hsa).';
      render(<RichTextRenderer content={content} />);
      
      const links = document.querySelectorAll('a');
      expect(links).toHaveLength(2);
      
      expect(links[0]).toHaveTextContent('IRS HSA Rules');
      expect(links[0]).toHaveAttribute('href', 'https://irs.gov/hsa');
      
      expect(links[1]).toHaveTextContent('Bank HSA Info');
      expect(links[1]).toHaveAttribute('href', 'https://bank.com/hsa');
    });
  });

  describe('List Rendering', () => {
    it('renders unordered lists with dashes', () => {
      const content = `Benefits of HSAs:
- Tax-deductible contributions
- Tax-free withdrawals for medical expenses
- Funds roll over year to year`;
      
      render(<RichTextRenderer content={content} />);
      
      const list = document.querySelector('ul');
      expect(list).toBeInTheDocument();
      expect(list).toHaveClass('list-disc', 'pl-4');
      
      const items = document.querySelectorAll('li');
      expect(items).toHaveLength(3);
      expect(items[0]).toHaveTextContent('Tax-deductible contributions');
      expect(items[1]).toHaveTextContent('Tax-free withdrawals for medical expenses');
      expect(items[2]).toHaveTextContent('Funds roll over year to year');
    });

    it('renders unordered lists with asterisks', () => {
      const content = `HSA Requirements:
* High-deductible health plan
* No other health coverage
* Not enrolled in Medicare`;
      
      render(<RichTextRenderer content={content} />);
      
      const list = document.querySelector('ul');
      expect(list).toBeInTheDocument();
      
      const items = document.querySelectorAll('li');
      expect(items).toHaveLength(3);
      expect(items[0]).toHaveTextContent('High-deductible health plan');
    });

    it('renders ordered lists correctly', () => {
      const content = `Steps to open an HSA:
1. Verify plan eligibility
2. Choose an HSA provider
3. Complete application
4. Fund your account`;
      
      render(<RichTextRenderer content={content} />);
      
      const list = document.querySelector('ol');
      expect(list).toBeInTheDocument();
      expect(list).toHaveClass('list-decimal', 'pl-4');
      
      const items = document.querySelectorAll('li');
      expect(items).toHaveLength(4);
      expect(items[0]).toHaveTextContent('Verify plan eligibility');
      expect(items[3]).toHaveTextContent('Fund your account');
    });

    it('handles mixed list types', () => {
      const content = `Benefits:
- Tax advantages
- Investment growth

Steps:
1. Open account
2. Contribute funds`;
      
      render(<RichTextRenderer content={content} />);
      
      expect(document.querySelector('ul')).toBeInTheDocument();
      expect(document.querySelector('ol')).toBeInTheDocument();
      
      const allItems = document.querySelectorAll('li');
      expect(allItems).toHaveLength(4);
    });
  });

  describe('Header Rendering', () => {
    it('renders different header levels with appropriate styling', () => {
      const content = `# Main Title
## Section Header
### Subsection
#### Details
##### Small Header
###### Smallest Header`;
      
      render(<RichTextRenderer content={content} />);
      
      // Check all header levels exist
      expect(document.querySelector('h1')).toHaveTextContent('Main Title');
      expect(document.querySelector('h2')).toHaveTextContent('Section Header');
      expect(document.querySelector('h3')).toHaveTextContent('Subsection');
      expect(document.querySelector('h4')).toHaveTextContent('Details');
      expect(document.querySelector('h5')).toHaveTextContent('Small Header');
      expect(document.querySelector('h6')).toHaveTextContent('Smallest Header');
      
      // Check styling classes
      expect(document.querySelector('h1')).toHaveClass('text-xl', 'font-bold', 'text-gray-900');
      expect(document.querySelector('h2')).toHaveClass('text-lg', 'font-bold', 'text-gray-900');
      expect(document.querySelector('h3')).toHaveClass('text-base', 'font-semibold', 'text-gray-900');
    });

    it('handles headers with formatting inside', () => {
      const content = '## **Bold Header** with *italic*';
      render(<RichTextRenderer content={content} />);
      
      const header = document.querySelector('h2');
      expect(header).toBeInTheDocument();
      expect(header?.querySelector('strong')).toHaveTextContent('Bold Header');
      expect(header?.querySelector('em')).toHaveTextContent('italic');
    });
  });

  describe('Paragraph and Line Break Handling', () => {
    it('renders paragraphs with proper spacing', () => {
      const content = `First paragraph of content.

Second paragraph after line break.

Third paragraph with more content.`;
      
      render(<RichTextRenderer content={content} />);
      
      const paragraphs = document.querySelectorAll('p');
      expect(paragraphs).toHaveLength(3);
      expect(paragraphs[0]).toHaveTextContent('First paragraph of content.');
      expect(paragraphs[1]).toHaveTextContent('Second paragraph after line break.');
      expect(paragraphs[2]).toHaveTextContent('Third paragraph with more content.');
    });

    it('handles single line breaks within paragraphs', () => {
      const content = `This is a paragraph
with a single line break
that should stay together.`;
      
      render(<RichTextRenderer content={content} />);
      
      const paragraph = document.querySelector('p');
      expect(paragraph).toBeInTheDocument();
      expect(paragraph).toHaveTextContent('This is a paragraph with a single line break that should stay together.');
    });
  });

  describe('Compact Mode', () => {
    it('applies compact spacing when compact=true', () => {
      const content = `# Header
This is content.

Another paragraph.`;
      
      render(<RichTextRenderer content={content} compact={true} />);
      
      const header = document.querySelector('h1');
      const paragraphs = document.querySelectorAll('p');
      
      expect(header).toHaveClass('mb-2'); // Compact spacing
      expect(paragraphs[0]).toHaveClass('mb-2'); // Compact spacing
    });

    it('applies normal spacing when compact=false', () => {
      const content = `# Header
This is content.`;
      
      render(<RichTextRenderer content={content} compact={false} />);
      
      const header = document.querySelector('h1');
      const paragraph = document.querySelector('p');
      
      expect(header).toHaveClass('mb-3'); // Normal spacing
      expect(paragraph).toHaveClass('mb-3'); // Normal spacing
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className to container', () => {
      const customClass = 'custom-rich-text';
      render(<RichTextRenderer content="Test content" className={customClass} />);
      
      const container = document.querySelector('.rich-text-content');
      expect(container).toHaveClass(customClass);
    });

    it('preserves base rich-text-content class', () => {
      render(<RichTextRenderer content="Test content" className="custom" />);
      
      const container = document.querySelector('.rich-text-content');
      expect(container).toHaveClass('rich-text-content', 'custom');
    });
  });

  describe('Edge Cases and Security', () => {
    it('handles empty content', () => {
      render(<RichTextRenderer content="" />);
      
      const paragraph = document.querySelector('p');
      expect(paragraph).toBeInTheDocument();
      expect(paragraph).toHaveTextContent('');
    });

    it('handles content with only whitespace', () => {
      render(<RichTextRenderer content="   \n\n   " />);
      
      const paragraph = document.querySelector('p');
      expect(paragraph).toBeInTheDocument();
    });

    it('handles malformed markdown gracefully', () => {
      const malformedContent = '**unclosed bold and *unclosed italic and `unclosed code';
      
      expect(() => {
        render(<RichTextRenderer content={malformedContent} />);
      }).not.toThrow();
      
      // Should render as plain text when markdown is malformed
      expect(screen.getByText(malformedContent)).toBeInTheDocument();
    });

    it('escapes HTML content properly', () => {
      const htmlContent = 'This contains <script>alert("xss")</script> HTML.';
      render(<RichTextRenderer content={htmlContent} />);
      
      // Script tags should not be executed
      expect(document.querySelector('script')).not.toBeInTheDocument();
      expect(screen.getByText(/This contains.*HTML\./)).toBeInTheDocument();
    });

    it('handles very long content without breaking', () => {
      const longContent = 'A'.repeat(10000);
      
      expect(() => {
        render(<RichTextRenderer content={longContent} />);
      }).not.toThrow();
      
      expect(screen.getByText(longContent)).toBeInTheDocument();
    });
  });

  describe('Complex Mixed Content', () => {
    it('renders complex HSA content with mixed formatting', () => {
      const complexContent = `# HSA Contribution Limits 2024

For **2024**, the HSA contribution limits are:

## Individual Coverage
- Maximum contribution: **$4,150**
- Catch-up contribution (55+): *additional $1,000*

## Family Coverage
1. Maximum contribution: **$8,300**
2. Catch-up contribution applies per individual

Visit [IRS Publication 969](https://www.irs.gov/pub969) for complete details.

\`Remember:\` Contributions must be made by tax filing deadline.`;
      
      render(<RichTextRenderer content={complexContent} />);
      
      // Check headers
      expect(document.querySelector('h1')).toHaveTextContent('HSA Contribution Limits 2024');
      expect(document.querySelector('h2')).toHaveTextContent('Individual Coverage');
      
      // Check lists
      expect(document.querySelectorAll('ul')).toHaveLength(1);
      expect(document.querySelectorAll('ol')).toHaveLength(1);
      
      // Check formatting
      expect(document.querySelectorAll('strong')).toHaveLength(3);
      expect(document.querySelectorAll('em')).toHaveLength(1);
      expect(document.querySelectorAll('code')).toHaveLength(1);
      
      // Check links
      const link = document.querySelector('a');
      expect(link).toHaveAttribute('href', 'https://www.irs.gov/pub969');
    });
  });
});

describe('InlineRichText', () => {
  it('renders inline formatting without block elements', () => {
    const content = 'This has **bold** and *italic* and `code` formatting.';
    render(<InlineRichText content={content} />);
    
    // Should not create paragraphs or other block elements
    expect(document.querySelector('p')).not.toBeInTheDocument();
    expect(document.querySelector('ul')).not.toBeInTheDocument();
    expect(document.querySelector('ol')).not.toBeInTheDocument();
    expect(document.querySelector('h1')).not.toBeInTheDocument();
    
    // Should still format inline elements
    expect(document.querySelector('strong')).toHaveTextContent('bold');
    expect(document.querySelector('em')).toHaveTextContent('italic');
    expect(document.querySelector('code')).toHaveTextContent('code');
  });

  it('applies custom className to inline span', () => {
    const customClass = 'custom-inline';
    render(<InlineRichText content="test" className={customClass} />);
    
    const span = document.querySelector('span');
    expect(span).toHaveClass(customClass);
  });

  it('handles plain text without formatting', () => {
    const content = 'Plain text content';
    render(<InlineRichText content={content} />);
    
    expect(screen.getByText(content)).toBeInTheDocument();
  });

  it('ignores block-level markdown in inline mode', () => {
    const content = '# Header\n- List item\n**Bold text**';
    render(<InlineRichText content={content} />);
    
    // Headers and lists should be treated as plain text
    expect(document.querySelector('h1')).not.toBeInTheDocument();
    expect(document.querySelector('ul')).not.toBeInTheDocument();
    
    // Bold should still work
    expect(document.querySelector('strong')).toHaveTextContent('Bold text');
  });
});