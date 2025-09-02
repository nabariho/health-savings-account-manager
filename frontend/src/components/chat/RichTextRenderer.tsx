/**
 * RichTextRenderer component for rendering formatted text content.
 * 
 * Supports markdown-style formatting including bold, italics, bullet points,
 * numbered lists, code blocks, and other rich text elements commonly used
 * in HSA Assistant responses.
 */

import React from 'react';
import clsx from 'clsx';

/**
 * Props for RichTextRenderer component.
 */
export interface RichTextRendererProps {
  /** Text content to render with rich formatting */
  content: string;
  /** Additional CSS classes */
  className?: string;
  /** Whether to use compact spacing */
  compact?: boolean;
}

/**
 * Parse and render markdown-style text elements.
 */
class MarkdownParser {
  private static readonly PATTERNS = {
    // Bold text: **text** or __text__
    bold: /\*\*(.*?)\*\*|__(.*?)__/g,
    // Italic text: *text* or _text_
    italic: /(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)/g,
    // Code spans: `code`
    code: /`([^`]+)`/g,
    // Links: [text](url)
    link: /\[([^\]]+)\]\(([^)]+)\)/g,
    // Unordered list items: - item or * item
    unorderedList: /^[-*]\s+(.+)$/gm,
    // Ordered list items: 1. item
    orderedList: /^\d+\.\s+(.+)$/gm,
    // Headers: # Header, ## Header, etc.
    header: /^(#{1,6})\s+(.+)$/gm,
    // Line breaks: double newlines
    paragraph: /\n\s*\n/g,
  };

  /**
   * Parse text content and return JSX elements.
   */
  static parse(content: string, compact: boolean = false): JSX.Element[] {
    const elements: JSX.Element[] = [];
    const lines = content.split('\n');
    let currentParagraph: string[] = [];
    let listItems: { type: 'ul' | 'ol'; items: string[] } | null = null;
    let key = 0;

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        const paragraphContent = currentParagraph.join(' ').trim();
        if (paragraphContent) {
          elements.push(
            <p key={`p-${key++}`} className={compact ? 'mb-2' : 'mb-3'}>
              {this.parseInlineElements(paragraphContent)}
            </p>
          );
        }
        currentParagraph = [];
      }
    };

    const flushList = () => {
      if (listItems) {
        const ListTag = listItems.type === 'ul' ? 'ul' : 'ol';
        elements.push(
          <ListTag key={`list-${key++}`} className={clsx(
            'pl-4',
            listItems.type === 'ul' ? 'list-disc' : 'list-decimal',
            compact ? 'mb-2 space-y-1' : 'mb-3 space-y-1'
          )}>
            {listItems.items.map((item, index) => (
              <li key={`item-${index}`} className="text-inherit">
                {this.parseInlineElements(item)}
              </li>
            ))}
          </ListTag>
        );
        listItems = null;
      }
    };

    lines.forEach(line => {
      const trimmedLine = line.trim();

      // Empty line - flush current elements
      if (!trimmedLine) {
        flushParagraph();
        flushList();
        return;
      }

      // Check for headers
      const headerMatch = trimmedLine.match(/^(#{1,6})\s+(.+)$/);
      if (headerMatch) {
        flushParagraph();
        flushList();
        const level = headerMatch[1].length;
        const HeaderTag = `h${Math.min(level, 6)}` as keyof JSX.IntrinsicElements;
        const headerClass = this.getHeaderClass(level, compact);
        
        elements.push(
          <HeaderTag key={`h-${key++}`} className={headerClass}>
            {this.parseInlineElements(headerMatch[2])}
          </HeaderTag>
        );
        return;
      }

      // Check for unordered list items
      const ulMatch = trimmedLine.match(/^[-*]\s+(.+)$/);
      if (ulMatch) {
        flushParagraph();
        if (!listItems || listItems.type !== 'ul') {
          flushList();
          listItems = { type: 'ul', items: [] };
        }
        listItems.items.push(ulMatch[1]);
        return;
      }

      // Check for ordered list items
      const olMatch = trimmedLine.match(/^\d+\.\s+(.+)$/);
      if (olMatch) {
        flushParagraph();
        if (!listItems || listItems.type !== 'ol') {
          flushList();
          listItems = { type: 'ol', items: [] };
        }
        listItems.items.push(olMatch[1]);
        return;
      }

      // Regular paragraph line
      flushList();
      currentParagraph.push(trimmedLine);
    });

    // Flush remaining content
    flushParagraph();
    flushList();

    return elements.length > 0 ? elements : [
      <p key="default" className={compact ? 'mb-2' : 'mb-3'}>
        {this.parseInlineElements(content)}
      </p>
    ];
  }

  /**
   * Parse inline elements like bold, italic, code, links.
   */
  private static parseInlineElements(text: string): React.ReactNode[] {
    let key = 0;
    let processedText = text;
    
    // Process bold text
    processedText = processedText.replace(this.PATTERNS.bold, (_, group1, group2) => {
      const content = group1 || group2;
      return `<strong class="font-semibold">${content}</strong>`;
    });

    // Process italic text
    processedText = processedText.replace(this.PATTERNS.italic, (_, group1, group2) => {
      const content = group1 || group2;
      return `<em class="italic">${content}</em>`;
    });

    // Process code spans
    processedText = processedText.replace(this.PATTERNS.code, (_, code) => {
      return `<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">${code}</code>`;
    });

    // Process links
    processedText = processedText.replace(this.PATTERNS.link, (_, text, url) => {
      return `<a href="${url}" class="text-primary-600 hover:text-primary-700 underline" target="_blank" rel="noopener noreferrer">${text}</a>`;
    });

    // Return the processed HTML as dangerouslySetInnerHTML for now
    // In a production app, you might want to use a proper markdown library
    return [<span key={`inline-${key++}`} dangerouslySetInnerHTML={{ __html: processedText }} />];
  }

  /**
   * Get CSS class for header based on level.
   */
  private static getHeaderClass(level: number, compact: boolean): string {
    const baseClasses = compact ? 'mb-2' : 'mb-3';
    
    switch (level) {
      case 1:
        return `text-xl font-bold text-gray-900 ${baseClasses}`;
      case 2:
        return `text-lg font-bold text-gray-900 ${baseClasses}`;
      case 3:
        return `text-base font-semibold text-gray-900 ${baseClasses}`;
      case 4:
        return `text-sm font-semibold text-gray-700 ${baseClasses}`;
      case 5:
        return `text-sm font-medium text-gray-700 ${baseClasses}`;
      case 6:
        return `text-xs font-medium text-gray-600 ${baseClasses}`;
      default:
        return `text-base font-semibold text-gray-900 ${baseClasses}`;
    }
  }
}

/**
 * RichTextRenderer component.
 */
export const RichTextRenderer: React.FC<RichTextRendererProps> = ({
  content,
  className,
  compact = false,
}) => {
  const elements = MarkdownParser.parse(content, compact);

  return (
    <div className={clsx('rich-text-content', className)}>
      {elements}
    </div>
  );
};

/**
 * Simple helper for rendering inline-only rich text (no block elements).
 */
export const InlineRichText: React.FC<{
  content: string;
  className?: string;
}> = ({ content, className }) => {
  // Only process inline elements, no paragraphs or lists
  let processedContent = content;
  
  // Process bold text
  processedContent = processedContent.replace(/\*\*(.*?)\*\*|__(.*?)__/g, (_, group1, group2) => {
    const text = group1 || group2;
    return `<strong class="font-semibold">${text}</strong>`;
  });

  // Process italic text
  processedContent = processedContent.replace(/(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)/g, (_, group1, group2) => {
    const text = group1 || group2;
    return `<em class="italic">${text}</em>`;
  });

  // Process code spans
  processedContent = processedContent.replace(/`([^`]+)`/g, (_, code) => {
    return `<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">${code}</code>`;
  });

  return (
    <span
      className={className}
      dangerouslySetInnerHTML={{ __html: processedContent }}
    />
  );
};

export default RichTextRenderer;