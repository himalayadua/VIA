/**
 * URL Detection and Classification Utilities
 * 
 * Detects URLs in text and classifies them by type (docs, GitHub, video, etc.)
 */

export interface DetectedURL {
  url: string;
  type: URLType;
  startIndex: number;
  endIndex: number;
  displayName?: string;
}

export type URLType = 
  | 'github'
  | 'youtube'
  | 'documentation'
  | 'pdf'
  | 'generic';

// URL regex pattern
const URL_REGEX = /(https?:\/\/[^\s]+)/g;

// URL type patterns
const URL_PATTERNS = {
  github: /github\.com\/[\w-]+\/[\w-]+/i,
  youtube: /(?:youtube\.com\/watch\?v=|youtu\.be\/)/i,
  pdf: /\.pdf(?:\?|$)/i,
  documentation: /(?:docs?\.|documentation|readthedocs|developer\.|api\.)/i
};

/**
 * Detect all URLs in a text message
 */
export function detectURLs(text: string): DetectedURL[] {
  const urls: DetectedURL[] = [];
  const matches = text.matchAll(URL_REGEX);

  for (const match of matches) {
    if (match[0] && match.index !== undefined) {
      const url = match[0];
      const type = classifyURL(url);
      
      urls.push({
        url,
        type,
        startIndex: match.index,
        endIndex: match.index + url.length,
        displayName: getDisplayName(url, type)
      });
    }
  }

  return urls;
}

/**
 * Classify a URL by type
 */
export function classifyURL(url: string): URLType {
  if (URL_PATTERNS.github.test(url)) return 'github';
  if (URL_PATTERNS.youtube.test(url)) return 'youtube';
  if (URL_PATTERNS.pdf.test(url)) return 'pdf';
  if (URL_PATTERNS.documentation.test(url)) return 'documentation';
  return 'generic';
}

/**
 * Get a display name for a URL
 */
function getDisplayName(url: string, type: URLType): string {
  try {
    const urlObj = new URL(url);
    
    switch (type) {
      case 'github':
        const pathParts = urlObj.pathname.split('/').filter(Boolean);
        if (pathParts.length >= 2) {
          return `${pathParts[0]}/${pathParts[1]}`;
        }
        break;
      case 'youtube':
        return 'YouTube Video';
      case 'pdf':
        const pdfName = urlObj.pathname.split('/').pop()?.replace('.pdf', '');
        return pdfName || 'PDF Document';
      case 'documentation':
        return urlObj.hostname.replace('www.', '');
    }
    
    return urlObj.hostname.replace('www.', '');
  } catch {
    return url;
  }
}

/**
 * Get icon for URL type
 */
export function getURLTypeIcon(type: URLType): string {
  switch (type) {
    case 'github':
      return '🐙';
    case 'youtube':
      return '▶️';
    case 'pdf':
      return '📄';
    case 'documentation':
      return '📚';
    default:
      return '🔗';
  }
}

/**
 * Get color class for URL type
 */
export function getURLTypeColor(type: URLType): string {
  switch (type) {
    case 'github':
      return 'text-purple-400';
    case 'youtube':
      return 'text-red-400';
    case 'pdf':
      return 'text-orange-400';
    case 'documentation':
      return 'text-blue-400';
    default:
      return 'text-slate-400';
  }
}

/**
 * Highlight URLs in text with React components
 */
export function highlightURLs(text: string): Array<{ type: 'text' | 'url'; content: string; urlData?: DetectedURL }> {
  const urls = detectURLs(text);
  
  if (urls.length === 0) {
    return [{ type: 'text', content: text }];
  }

  const parts: Array<{ type: 'text' | 'url'; content: string; urlData?: DetectedURL }> = [];
  let lastIndex = 0;

  for (const url of urls) {
    // Add text before URL
    if (url.startIndex > lastIndex) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex, url.startIndex)
      });
    }

    // Add URL
    parts.push({
      type: 'url',
      content: url.url,
      urlData: url
    });

    lastIndex = url.endIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.substring(lastIndex)
    });
  }

  return parts;
}
