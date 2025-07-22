// Main Application Module
// =======================

class MarkdownReaderApp {
  constructor() {
    this.modules = {
      theme: null,
      sidebar: null,
      search: null
    };
    
    this.config = {
      autoSave: true,
      readingProgress: true,
      smoothScrolling: true,
      keyboardShortcuts: true
    };
    
    this.state = {
      currentDocument: null,
      readingPosition: 0,
      isFullscreen: false
    };
    
    this.init();
  }
  
  init() {
    this.waitForModules().then(() => {
      this.setupKeyboardShortcuts();
      this.setupReadingProgress();
      this.setupDocumentNavigation();
      this.setupPrintHandling();
      this.restoreUserState();
      
      console.log('Markdown Reader App initialized');
    });
  }
  
  async waitForModules() {
    // Wait for other modules to be initialized
    const checkInterval = 50;
    const maxWait = 5000;
    let waited = 0;
    
    while (waited < maxWait) {
      if (window.themeManager && window.sidebarManager && window.searchManager) {
        this.modules.theme = window.themeManager;
        this.modules.sidebar = window.sidebarManager;
        this.modules.search = window.searchManager;
        break;
      }
      
      await new Promise(resolve => setTimeout(resolve, checkInterval));
      waited += checkInterval;
    }
  }
  
  setupKeyboardShortcuts() {
    if (!this.config.keyboardShortcuts) return;
    
    document.addEventListener('keydown', (e) => {
      // Don't handle shortcuts when typing in inputs
      if (e.target.matches('input, textarea, [contenteditable]')) return;
      
      // Handle modifier key combinations
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'k':
            e.preventDefault();
            this.focusSearch();
            break;
          case 'f':
            e.preventDefault();
            this.focusSearch();
            break;
          case 'p':
            e.preventDefault();
            this.print();
            break;
          case 'd':
            e.preventDefault();
            this.modules.theme?.toggleTheme();
            break;
        }
      } else {
        switch (e.key) {
          case '/':
            e.preventDefault();
            this.focusSearch();
            break;
          case 'Escape':
            this.handleEscape();
            break;
          case 's':
            if (!e.target.closest('input')) {
              e.preventDefault();
              this.modules.sidebar?.toggle();
            }
            break;
          case 'f':
            if (!e.target.closest('input')) {
              e.preventDefault();
              this.toggleFullscreen();
            }
            break;
          case 'n':
            if (!e.target.closest('input')) {
              e.preventDefault();
              this.navigateNext();
            }
            break;
          case 'p':
            if (!e.target.closest('input')) {
              e.preventDefault();
              this.navigatePrevious();
            }
            break;
        }
      }
    });
  }
  
  setupReadingProgress() {
    if (!this.config.readingProgress) return;
    
    // Track reading position
    let ticking = false;
    
    const updateProgress = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          this.updateReadingProgress();
          ticking = false;
        });
        ticking = true;
      }
    };
    
    window.addEventListener('scroll', updateProgress);
    window.addEventListener('resize', updateProgress);
    
    // Initial update
    updateProgress();
  }
  
  updateReadingProgress() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    
    if (scrollHeight <= 0) return;
    
    const progress = Math.min(100, (scrollTop / scrollHeight) * 100);
    this.state.readingPosition = progress;
    
    // Update global progress bar
    const globalProgressBar = document.querySelector('.global-progress-bar');
    if (globalProgressBar) {
      globalProgressBar.style.width = `${progress}%`;
    }
    
    // Save progress if auto-save is enabled
    if (this.config.autoSave) {
      this.saveReadingProgress();
    }
  }
  
  setupDocumentNavigation() {
    // Handle navigation buttons
    const prevButton = document.querySelector('[data-nav="previous"]');
    const nextButton = document.querySelector('[data-nav="next"]');
    
    if (prevButton) {
      prevButton.addEventListener('click', () => this.navigatePrevious());
    }
    
    if (nextButton) {
      nextButton.addEventListener('click', () => this.navigateNext());
    }
    
    // Handle anchor link clicks
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"]');
      if (link && this.config.smoothScrolling) {
        e.preventDefault();
        this.smoothScrollTo(link.getAttribute('href'));
      }
    });
  }
  
  setupPrintHandling() {
    // Handle print button
    const printButton = document.querySelector('[data-action="print"]');
    if (printButton) {
      printButton.addEventListener('click', () => this.print());
    }
    
    // Before print event
    window.addEventListener('beforeprint', () => {
      document.body.classList.add('preparing-print');
    });
    
    // After print event
    window.addEventListener('afterprint', () => {
      document.body.classList.remove('preparing-print');
    });
  }
  
  focusSearch() {
    const searchInput = document.querySelector('.content-search, .sidebar-search input');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }
  
  handleEscape() {
    // Close any open overlays or modals
    this.modules.sidebar?.close();
    this.modules.search?.hideAllResults();
    
    // Clear search if focused
    const activeElement = document.activeElement;
    if (activeElement && activeElement.matches('input[type="search"], .content-search, .sidebar-search input')) {
      activeElement.blur();
    }
  }
  
  navigateNext() {
    const currentActive = document.querySelector('.sidebar-nav-item.active');
    if (currentActive) {
      const nextItem = currentActive.nextElementSibling;
      if (nextItem && nextItem.classList.contains('sidebar-nav-item')) {
        nextItem.click();
      }
    }
  }
  
  navigatePrevious() {
    const currentActive = document.querySelector('.sidebar-nav-item.active');
    if (currentActive) {
      const prevItem = currentActive.previousElementSibling;
      if (prevItem && prevItem.classList.contains('sidebar-nav-item')) {
        prevItem.click();
      }
    }
  }
  
  smoothScrollTo(target) {
    const element = document.querySelector(target);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
      
      // Update URL
      if (history.pushState) {
        history.pushState(null, null, target);
      }
    }
  }
  
  toggleFullscreen() {
    if (!document.fullscreenEnabled) return;
    
    if (document.fullscreenElement) {
      document.exitFullscreen();
      this.state.isFullscreen = false;
    } else {
      document.documentElement.requestFullscreen();
      this.state.isFullscreen = true;
    }
  }
  
  print() {
    // Optimize for printing
    document.body.classList.add('preparing-print');
    
    // Small delay to allow styles to apply
    setTimeout(() => {
      window.print();
      document.body.classList.remove('preparing-print');
    }, 100);
  }
  
  saveReadingProgress() {
    if (!this.state.currentDocument) return;
    
    try {
      const progressData = {
        document: this.state.currentDocument,
        position: this.state.readingPosition,
        timestamp: Date.now()
      };
      
      localStorage.setItem('markdown-reader-progress', JSON.stringify(progressData));
    } catch (e) {
      console.warn('Failed to save reading progress:', e);
    }
  }
  
  restoreReadingProgress() {
    try {
      const stored = localStorage.getItem('markdown-reader-progress');
      if (!stored) return;
      
      const progressData = JSON.parse(stored);
      
      // Only restore if it's the same document and recent
      if (progressData.document === this.state.currentDocument &&
          Date.now() - progressData.timestamp < 24 * 60 * 60 * 1000) {
        
        // Restore scroll position
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollTop = (progressData.position / 100) * scrollHeight;
        
        setTimeout(() => {
          window.scrollTo(0, scrollTop);
        }, 100);
      }
    } catch (e) {
      console.warn('Failed to restore reading progress:', e);
    }
  }
  
  restoreUserState() {
    // Set current document (you might get this from the URL or data attribute)
    const documentMeta = document.querySelector('meta[name="document-id"]');
    this.state.currentDocument = documentMeta?.content || window.location.pathname;
    
    // Restore reading progress
    this.restoreReadingProgress();
  }
  
  // Public API methods
  getState() {
    return {
      ...this.state,
      theme: this.modules.theme?.getCurrentTheme(),
      sidebar: this.modules.sidebar?.getCurrentState()
    };
  }
  
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
  }
  
  navigateToDocument(href) {
    window.location.href = href;
  }
  
  exportProgress() {
    return {
      currentDocument: this.state.currentDocument,
      readingPosition: this.state.readingPosition,
      theme: this.modules.theme?.getCurrentTheme(),
      timestamp: Date.now()
    };
  }
  
  showKeyboardShortcuts() {
    const shortcuts = [
      'Ctrl/Cmd + K: Focus search',
      'Ctrl/Cmd + F: Focus search',
      'Ctrl/Cmd + P: Print',
      'Ctrl/Cmd + D: Toggle dark mode',
      '/: Focus search',
      'S: Toggle sidebar',
      'F: Toggle fullscreen',
      'N: Next document',
      'P: Previous document',
      'Escape: Close overlays'
    ];
    
    alert('Keyboard Shortcuts:\n\n' + shortcuts.join('\n'));
  }
}

// Export for global access
window.MarkdownReaderApp = MarkdownReaderApp;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.markdownReaderApp = new MarkdownReaderApp();
  });
} else {
  window.markdownReaderApp = new MarkdownReaderApp();
}

// Help function for keyboard shortcuts
window.showKeyboardHelp = function() {
  if (window.markdownReaderApp) {
    window.markdownReaderApp.showKeyboardShortcuts();
  }
};
