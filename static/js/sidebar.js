// Sidebar Management Module
// =========================

class SidebarManager {
  constructor() {
    this.sidebar = null;
    this.overlay = null;
    this.toggleButtons = [];
    this.isOpen = false;
    this.storageKey = 'markdown-reader-sidebar-state';
    
    this.init();
  }
  
  init() {
    this.setupElements();
    this.setupEventListeners();
    this.restoreState();
    this.updateProgress();
  }
  
  setupElements() {
    this.sidebar = document.querySelector('.sidebar');
    this.overlay = document.querySelector('.sidebar-overlay');
    this.toggleButtons = document.querySelectorAll('[data-sidebar-toggle]');
    
    if (!this.sidebar) {
      console.warn('Sidebar element not found');
      return;
    }
    
    // Create overlay if it doesn't exist
    if (!this.overlay) {
      this.overlay = document.createElement('div');
      this.overlay.className = 'sidebar-overlay';
      document.body.appendChild(this.overlay);
    }
  }
  
  setupEventListeners() {
    // Toggle buttons
    this.toggleButtons.forEach(button => {
      button.addEventListener('click', () => {
        this.toggle();
      });
    });
    
    // Overlay click to close
    if (this.overlay) {
      this.overlay.addEventListener('click', () => {
        this.close();
      });
    }
    
    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
    
    // Resize handler for responsive behavior
    window.addEventListener('resize', () => {
      this.handleResize();
    });
    
    // Navigation item clicks
    this.setupNavigation();
  }
  
  setupNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        // Update active state
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        
        // Close sidebar on mobile after navigation
        if (window.innerWidth < 1024) {
          this.close();
        }
        
        // Update progress
        this.updateProgressFromNavigation(item);
      });
    });
  }
  
  updateProgressFromNavigation(activeItem) {
    const allItems = document.querySelectorAll('.sidebar-nav-item');
    const activeIndex = Array.from(allItems).indexOf(activeItem);
    const totalItems = allItems.length;
    
    if (totalItems > 0) {
      const progress = ((activeIndex + 1) / totalItems) * 100;
      this.updateProgressBar(progress);
      this.updateProgressText(activeIndex + 1, totalItems);
    }
  }
  
  updateProgress() {
    // Update progress based on current page/document
    const activeItem = document.querySelector('.sidebar-nav-item.active');
    if (activeItem) {
      this.updateProgressFromNavigation(activeItem);
    }
  }
  
  updateProgressBar(percentage) {
    const progressBar = document.querySelector('.progress-bar');
    const globalProgressBar = document.querySelector('.global-progress-bar');
    
    if (progressBar) {
      progressBar.style.width = `${percentage}%`;
    }
    
    if (globalProgressBar) {
      globalProgressBar.style.width = `${percentage}%`;
    }
  }
  
  updateProgressText(current, total) {
    const progressText = document.querySelector('.sidebar-progress');
    if (progressText) {
      progressText.textContent = `${current} / ${total}`;
    }
  }
  
  open() {
    if (!this.sidebar) return;
    
    this.isOpen = true;
    this.sidebar.classList.add('sidebar-open');
    this.overlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Focus management
    this.trapFocus();
    
    this.saveState();
  }
  
  close() {
    if (!this.sidebar) return;
    
    this.isOpen = false;
    this.sidebar.classList.remove('sidebar-open');
    this.overlay?.classList.remove('active');
    document.body.style.overflow = '';
    
    // Return focus to toggle button
    const toggleButton = document.querySelector('[data-sidebar-toggle]');
    if (toggleButton) {
      toggleButton.focus();
    }
    
    this.saveState();
  }
  
  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }
  
  trapFocus() {
    if (!this.sidebar || !this.isOpen) return;
    
    const focusableElements = this.sidebar.querySelectorAll(
      'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    // Focus first element
    firstElement.focus();
    
    // Handle tab key
    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;
      
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };
    
    document.addEventListener('keydown', handleTabKey);
    
    // Cleanup when sidebar closes
    const cleanup = () => {
      document.removeEventListener('keydown', handleTabKey);
    };
    
    setTimeout(() => {
      if (!this.isOpen) cleanup();
    }, 100);
  }
  
  handleResize() {
    // Close sidebar on desktop if it was opened on mobile
    if (window.innerWidth >= 1024 && this.isOpen) {
      this.close();
    }
  }
  
  saveState() {
    try {
      const state = {
        isOpen: this.isOpen,
        timestamp: Date.now()
      };
      localStorage.setItem(this.storageKey, JSON.stringify(state));
    } catch (e) {
      console.warn('Failed to save sidebar state:', e);
    }
  }
  
  restoreState() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (!stored) return;
      
      const state = JSON.parse(stored);
      
      // Don't restore open state on mobile
      if (window.innerWidth < 1024) return;
      
      // Don't restore if state is too old (more than 1 day)
      if (Date.now() - state.timestamp > 24 * 60 * 60 * 1000) return;
      
      if (state.isOpen) {
        this.open();
      }
    } catch (e) {
      console.warn('Failed to restore sidebar state:', e);
    }
  }
  
  // Public API methods
  getCurrentState() {
    return {
      isOpen: this.isOpen,
      hasOverlay: !!this.overlay,
      isMobile: window.innerWidth < 1024
    };
  }
  
  setActiveItem(href) {
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    navItems.forEach(item => {
      item.classList.remove('active');
      if (item.getAttribute('href') === href) {
        item.classList.add('active');
        this.updateProgressFromNavigation(item);
      }
    });
  }
}

// Export for use in other modules
window.SidebarManager = SidebarManager;

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.sidebarManager = new SidebarManager();
  });
} else {
  window.sidebarManager = new SidebarManager();
}
