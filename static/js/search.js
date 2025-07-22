// Search Management Module
// ========================

class SearchManager {
  constructor() {
    this.searchInputs = [];
    this.searchResults = null;
    this.searchIndex = [];
    this.currentQuery = '';
    this.highlightedIndex = -1;
    this.debounceTimer = null;
    this.debounceDelay = 300;
    
    this.init();
  }
  
  init() {
    this.setupElements();
    this.buildSearchIndex();
    this.setupEventListeners();
  }
  
  setupElements() {
    // Find all search inputs
    this.searchInputs = document.querySelectorAll('input[type="search"], .content-search, .sidebar-search input');
    
    // Create or find search results containers
    this.searchInputs.forEach(input => {
      this.setupSearchContainer(input);
    });
  }
  
  setupSearchContainer(input) {
    const container = input.parentElement;
    
    // Make container relative positioned
    if (getComputedStyle(container).position === 'static') {
      container.style.position = 'relative';
    }
    
    // Create results container if it doesn't exist
    let results = container.querySelector('.search-results');
    if (!results) {
      results = document.createElement('div');
      results.className = 'search-results';
      results.setAttribute('role', 'listbox');
      results.setAttribute('aria-label', 'Search results');
      container.appendChild(results);
    }
  }
  
  buildSearchIndex() {
    // Index navigation items
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    navItems.forEach((item, index) => {
      const title = item.querySelector('.nav-item-title')?.textContent || '';
      const href = item.getAttribute('href') || '';
      
      this.searchIndex.push({
        type: 'navigation',
        title: title.trim(),
        href: href,
        element: item,
        index: index
      });
    });
    
    // Index markdown content headings
    const headings = document.querySelectorAll('.markdown-content h1, .markdown-content h2, .markdown-content h3');
    headings.forEach((heading, index) => {
      const text = heading.textContent || '';
      const id = heading.id || `heading-${index}`;
      
      // Create anchor if it doesn't exist
      if (!heading.id) {
        heading.id = id;
      }
      
      this.searchIndex.push({
        type: 'content',
        title: text.trim(),
        href: `#${id}`,
        element: heading,
        index: index
      });
    });
    
    // Index markdown content paragraphs (limited to first 150 chars)
    const paragraphs = document.querySelectorAll('.markdown-content p');
    paragraphs.forEach((p, index) => {
      const text = p.textContent || '';
      if (text.trim().length > 20) { // Only index substantial paragraphs
        this.searchIndex.push({
          type: 'paragraph',
          title: text.trim().substring(0, 150) + (text.length > 150 ? '...' : ''),
          href: `#paragraph-${index}`,
          element: p,
          index: index,
          fullText: text.trim()
        });
        
        // Add ID to paragraph for linking
        if (!p.id) {
          p.id = `paragraph-${index}`;
        }
      }
    });
  }
  
  setupEventListeners() {
    this.searchInputs.forEach(input => {
      // Search input events
      input.addEventListener('input', (e) => {
        this.handleSearch(e.target);
      });
      
      input.addEventListener('keydown', (e) => {
        this.handleKeydown(e, input);
      });
      
      input.addEventListener('focus', (e) => {
        this.handleFocus(e.target);
      });
      
      input.addEventListener('blur', (e) => {
        // Delay hiding results to allow for clicks
        setTimeout(() => {
          this.hideResults(e.target);
        }, 150);
      });
    });
    
    // Click outside to close
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-results') && 
          !e.target.closest('input[type="search"]') &&
          !e.target.closest('.content-search') &&
          !e.target.closest('.sidebar-search')) {
        this.hideAllResults();
      }
    });
  }
  
  handleSearch(input) {
    clearTimeout(this.debounceTimer);
    
    this.debounceTimer = setTimeout(() => {
      const query = input.value.trim();
      this.currentQuery = query;
      this.highlightedIndex = -1;
      
      if (query.length < 2) {
        this.hideResults(input);
        return;
      }
      
      const results = this.performSearch(query);
      this.displayResults(input, results);
    }, this.debounceDelay);
  }
  
  performSearch(query) {
    const lowercaseQuery = query.toLowerCase();
    const results = [];
    
    this.searchIndex.forEach(item => {
      const title = item.title.toLowerCase();
      const fullText = item.fullText ? item.fullText.toLowerCase() : title;
      
      // Exact match (highest priority)
      if (title.includes(lowercaseQuery)) {
        const score = this.calculateScore(lowercaseQuery, title, item.type);
        results.push({
          ...item,
          score: score,
          matchType: 'title',
          highlightText: this.highlightMatch(item.title, query)
        });
      }
      // Content match (lower priority)
      else if (fullText.includes(lowercaseQuery)) {
        const score = this.calculateScore(lowercaseQuery, fullText, item.type) * 0.7;
        const context = this.extractContext(fullText, lowercaseQuery);
        results.push({
          ...item,
          score: score,
          matchType: 'content',
          highlightText: this.highlightMatch(context, query)
        });
      }
    });
    
    // Sort by score (highest first)
    results.sort((a, b) => b.score - a.score);
    
    // Limit results
    return results.slice(0, 10);
  }
  
  calculateScore(query, text, type) {
    const queryLength = query.length;
    const textLength = text.length;
    
    // Base score: how much of the text matches
    let score = queryLength / textLength;
    
    // Boost for exact matches at the beginning
    if (text.startsWith(query)) {
      score *= 2;
    }
    
    // Boost for word boundaries
    const words = text.split(/\s+/);
    const matchingWords = words.filter(word => word.includes(query));
    score += (matchingWords.length / words.length) * 0.5;
    
    // Type-based scoring
    const typeScores = {
      'navigation': 1.5,
      'content': 1.2,
      'paragraph': 1.0
    };
    
    score *= typeScores[type] || 1.0;
    
    return score;
  }
  
  extractContext(text, query, contextLength = 100) {
    const index = text.indexOf(query);
    if (index === -1) return text.substring(0, contextLength);
    
    const start = Math.max(0, index - contextLength / 2);
    const end = Math.min(text.length, index + query.length + contextLength / 2);
    
    let context = text.substring(start, end);
    
    if (start > 0) context = '...' + context;
    if (end < text.length) context = context + '...';
    
    return context;
  }
  
  highlightMatch(text, query) {
    if (!query || !text) return text;
    
    const regex = new RegExp(`(${this.escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }
  
  escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  
  displayResults(input, results) {
    const container = input.parentElement;
    const resultsContainer = container.querySelector('.search-results');
    
    if (!resultsContainer) return;
    
    if (results.length === 0) {
      resultsContainer.innerHTML = '<div class="search-no-results">No results found</div>';
    } else {
      resultsContainer.innerHTML = results.map((result, index) => `
        <div class="search-result-item" data-index="${index}" data-href="${result.href}" role="option">
          <div class="search-result-title">${result.title}</div>
          <div class="search-result-context">${result.highlightText}</div>
        </div>
      `).join('');
      
      // Add click handlers
      resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
          this.selectResult(item.dataset.href, input);
        });
      });
    }
    
    resultsContainer.style.display = 'block';
  }
  
  handleKeydown(e, input) {
    const resultsContainer = input.parentElement.querySelector('.search-results');
    if (!resultsContainer || resultsContainer.style.display === 'none') return;
    
    const items = resultsContainer.querySelectorAll('.search-result-item');
    if (items.length === 0) return;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        this.highlightedIndex = Math.min(this.highlightedIndex + 1, items.length - 1);
        this.updateHighlight(items);
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        this.highlightedIndex = Math.max(this.highlightedIndex - 1, -1);
        this.updateHighlight(items);
        break;
        
      case 'Enter':
        e.preventDefault();
        if (this.highlightedIndex >= 0 && items[this.highlightedIndex]) {
          const href = items[this.highlightedIndex].dataset.href;
          this.selectResult(href, input);
        }
        break;
        
      case 'Escape':
        this.hideResults(input);
        break;
    }
  }
  
  updateHighlight(items) {
    items.forEach((item, index) => {
      item.classList.toggle('highlighted', index === this.highlightedIndex);
    });
    
    // Scroll highlighted item into view
    if (this.highlightedIndex >= 0 && items[this.highlightedIndex]) {
      items[this.highlightedIndex].scrollIntoView({
        block: 'nearest',
        behavior: 'smooth'
      });
    }
  }
  
  selectResult(href, input) {
    // Navigate to the result
    if (href.startsWith('#')) {
      // Internal anchor
      const element = document.querySelector(href);
      if (element) {
        element.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
        
        // Update URL without reloading
        if (history.pushState) {
          history.pushState(null, null, href);
        }
        
        // Update sidebar active state if it's a navigation item
        if (window.sidebarManager) {
          window.sidebarManager.setActiveItem(href);
        }
      }
    } else {
      // External link
      window.location.href = href;
    }
    
    // Clear search and hide results
    input.value = '';
    this.hideResults(input);
    input.blur();
  }
  
  handleFocus(input) {
    if (input.value.trim().length >= 2) {
      const results = this.performSearch(input.value.trim());
      this.displayResults(input, results);
    }
  }
  
  hideResults(input) {
    const container = input.parentElement;
    const resultsContainer = container.querySelector('.search-results');
    
    if (resultsContainer) {
      resultsContainer.style.display = 'none';
    }
    
    this.highlightedIndex = -1;
  }
  
  hideAllResults() {
    this.searchInputs.forEach(input => {
      this.hideResults(input);
    });
  }
  
  // Public API methods
  rebuildIndex() {
    this.searchIndex = [];
    this.buildSearchIndex();
  }
  
  addToIndex(item) {
    this.searchIndex.push(item);
  }
  
  search(query) {
    return this.performSearch(query);
  }
  
  clearSearch() {
    this.searchInputs.forEach(input => {
      input.value = '';
      this.hideResults(input);
    });
    this.currentQuery = '';
  }
}

// Export for use in other modules
window.SearchManager = SearchManager;

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.searchManager = new SearchManager();
  });
} else {
  window.searchManager = new SearchManager();
}
