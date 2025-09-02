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
   * Parse inline elements like bold, italic, code, links safely using JSX.
   */
  private static parseInlineElements(text: string): React.ReactNode[] {
    let key = 0;
    
    // Helper to create a parsing pipeline for all inline elements
    const parseWithMultipleFormats = (content: string): React.ReactNode[] => {
      const elements: React.ReactNode[] = [];
      
      // Find all inline formatting patterns
      const patterns = [
        { type: 'bold', regex: this.PATTERNS.bold },
        { type: 'italic', regex: this.PATTERNS.italic },
        { type: 'code', regex: this.PATTERNS.code },
        { type: 'link', regex: this.PATTERNS.link },
      ];
      
      const allMatches: Array<{ 
        type: string; 
        match: RegExpMatchArray; 
        start: number; 
        end: number;
      }> = [];
      
      // Collect all matches with their positions
      patterns.forEach(pattern => {
        const matches = Array.from(content.matchAll(pattern.regex));
        matches.forEach(match => {
          if (match.index !== undefined) {
            allMatches.push({
              type: pattern.type,
              match,
              start: match.index,
              end: match.index + match[0].length,
            });
          }
        });
      });
      
      // Sort matches by start position
      allMatches.sort((a, b) => a.start - b.start);
      
      // If no matches, return plain text
      if (allMatches.length === 0) {
        return [<span key={`text-${key++}`}>{content}</span>];
      }
      
      let lastIndex = 0;
      
      allMatches.forEach(({ type, match, start, end }) => {
        // Add text before this match
        if (start > lastIndex) {
          const beforeText = content.slice(lastIndex, start);
          if (beforeText) {
            elements.push(<span key={`text-${key++}`}>{beforeText}</span>);
          }
        }
        
        // Add the formatted element
        switch (type) {
          case 'bold':
            const boldText = match[1] || match[2];
            elements.push(
              <strong key={`bold-${key++}`} className="font-semibold">
                {boldText}
              </strong>
            );
            break;
            
          case 'italic':
            const italicText = match[1] || match[2];
            elements.push(
              <em key={`italic-${key++}`} className="italic">
                {italicText}
              </em>
            );
            break;
            
          case 'code':
            elements.push(
              <code 
                key={`code-${key++}`} 
                className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono"
              >
                {match[1]}
              </code>
            );
            break;
            
          case 'link':
            elements.push(
              <a
                key={`link-${key++}`}
                href={match[2]}
                className="text-primary-600 hover:text-primary-700 underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                {match[1]}
              </a>
            );
            break;
        }
        
        lastIndex = end;
      });
      
      // Add remaining text after last match
      if (lastIndex < content.length) {
        const remainingText = content.slice(lastIndex);
        if (remainingText) {
          elements.push(<span key={`text-${key++}`}>{remainingText}</span>);
        }
      }
      
      return elements;
    };
    
    return parseWithMultipleFormats(text);
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
 * Uses safe JSX rendering instead of dangerouslySetInnerHTML.
 */
export const InlineRichText: React.FC<{
  content: string;
  className?: string;
}> = ({ content, className }) => {
  let key = 0;
  
  // Helper function to safely parse inline formatting
  const parseInlineFormatting = (text: string): JSX.Element[] => {
    const elements: JSX.Element[] = [];
    let currentText = text;
    
    // Process bold text: **text** or __text__
    const boldMatches = Array.from(currentText.matchAll(/\*\*(.*?)\*\*|__(.*?)__/g));
    if (boldMatches.length > 0) {
      let lastIndex = 0;
      boldMatches.forEach((match) => {
        // Add text before bold
        if (match.index! > lastIndex) {
          const beforeText = currentText.slice(lastIndex, match.index);
          if (beforeText) {
            elements.push(<span key={`text-${key++}`}>{beforeText}</span>);
          }
        }
        
        // Add bold element
        const boldText = match[1] || match[2];
        elements.push(<strong key={`bold-${key++}`} className="font-semibold">{boldText}</strong>);
        
        lastIndex = match.index! + match[0].length;
      });
      
      // Add remaining text
      if (lastIndex < currentText.length) {
        const remainingText = currentText.slice(lastIndex);
        if (remainingText) {
          elements.push(<span key={`text-${key++}`}>{remainingText}</span>);
        }
      }
      
      return elements;
    }
    
    // Process italic text: *text* or _text_ (if no bold found)
    const italicMatches = Array.from(currentText.matchAll(/(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)/g));
    if (italicMatches.length > 0) {
      let lastIndex = 0;
      italicMatches.forEach((match) => {
        // Add text before italic
        if (match.index! > lastIndex) {
          const beforeText = currentText.slice(lastIndex, match.index);
          if (beforeText) {
            elements.push(<span key={`text-${key++}`}>{beforeText}</span>);
          }
        }
        
        // Add italic element
        const italicText = match[1] || match[2];
        elements.push(<em key={`italic-${key++}`} className="italic">{italicText}</em>);
        
        lastIndex = match.index! + match[0].length;
      });
      
      // Add remaining text
      if (lastIndex < currentText.length) {
        const remainingText = currentText.slice(lastIndex);
        if (remainingText) {
          elements.push(<span key={`text-${key++}`}>{remainingText}</span>);
        }
      }
      
      return elements;
    }
    
    // Process code spans: `code`
    const codeMatches = Array.from(currentText.matchAll(/`([^`]+)`/g));
    if (codeMatches.length > 0) {
      let lastIndex = 0;
      codeMatches.forEach((match) => {
        // Add text before code
        if (match.index! > lastIndex) {
          const beforeText = currentText.slice(lastIndex, match.index);
          if (beforeText) {
            elements.push(<span key={`text-${key++}`}>{beforeText}</span>);
          }
        }
        
        // Add code element
        elements.push(
          <code 
            key={`code-${key++}`} 
            className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono"
          >
            {match[1]}
          </code>
        );
        
        lastIndex = match.index! + match[0].length;
      });
      
      // Add remaining text
      if (lastIndex < currentText.length) {
        const remainingText = currentText.slice(lastIndex);
        if (remainingText) {
          elements.push(<span key={`text-${key++}`}>{remainingText}</span>);
        }
      }
      
      return elements;
    }
    
    // No formatting found, return plain text
    return [<span key={`text-${key++}`}>{text}</span>];
  };

  const formattedElements = parseInlineFormatting(content);

  return (
    <span className={className}>
      {formattedElements}
    </span>
  );
};

export default RichTextRenderer;