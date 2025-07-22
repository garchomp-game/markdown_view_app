// Theme Management Module
// =======================

class ThemeManager {
  constructor() {
    this.storageKey = 'markdown-reader-theme';
    this.themes = ['light', 'dark'];
    this.currentTheme = this.getStoredTheme() || this.getSystemTheme();
    
    this.init();
  }
  
  init() {
    // Apply initial theme immediately
    this.applyTheme(this.currentTheme);
    
    // Listen for system theme changes
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.addEventListener('change', (e) => {
        if (!this.getStoredTheme()) {
          this.applyTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
    
    // Set up theme toggle buttons
    this.setupThemeToggle();
    
    // Debug output
    console.log('Theme initialized:', this.currentTheme);
    console.log('Document data-theme:', document.documentElement.getAttribute('data-theme'));
  }
  
  getSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }
  
  getStoredTheme() {
    try {
      return localStorage.getItem(this.storageKey);
    } catch (e) {
      console.warn('Failed to access localStorage for theme:', e);
      return null;
    }
  }
  
  setStoredTheme(theme) {
    try {
      if (theme) {
        localStorage.setItem(this.storageKey, theme);
      } else {
        localStorage.removeItem(this.storageKey);
      }
    } catch (e) {
      console.warn('Failed to save theme to localStorage:', e);
    }
  }
  
  applyTheme(theme) {
    if (!this.themes.includes(theme)) {
      console.warn(`Invalid theme: ${theme}`);
      return;
    }
    
    this.currentTheme = theme;
    
    // Force remove any existing data-theme attribute first
    document.documentElement.removeAttribute('data-theme');
    
    // Apply new theme with a small delay to ensure CSS reprocessing
    requestAnimationFrame(() => {
      document.documentElement.setAttribute('data-theme', theme);
      
      // Force a style recalculation
      document.body.style.display = 'none';
      document.body.offsetHeight; // Trigger reflow
      document.body.style.display = '';
      
      console.log('Theme applied:', theme);
      console.log('HTML data-theme:', document.documentElement.getAttribute('data-theme'));
    });
    
    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(theme);
    
    // Dispatch theme change event
    window.dispatchEvent(new CustomEvent('themechange', {
      detail: { theme }
    }));
  }
  
  updateMetaThemeColor(theme) {
    const colors = {
      light: '#ffffff',
      dark: '#1a1a1a'
    };
    
    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.name = 'theme-color';
      document.head.appendChild(metaThemeColor);
    }
    
    metaThemeColor.content = colors[theme] || colors.light;
  }
  
  toggleTheme() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }
  
  setTheme(theme) {
    this.applyTheme(theme);
    this.setStoredTheme(theme);
  }
  
  resetToSystemTheme() {
    this.setStoredTheme(null);
    this.applyTheme(this.getSystemTheme());
  }
  
  setupThemeToggle() {
    const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
    
    toggleButtons.forEach(button => {
      button.addEventListener('click', () => {
        this.toggleTheme();
      });
      
      // Add keyboard support
      button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.toggleTheme();
        }
      });
    });
  }
  
  getCurrentTheme() {
    return this.currentTheme;
  }
  
  isSystemTheme() {
    return !this.getStoredTheme();
  }
}

// Export for use in other modules
window.ThemeManager = ThemeManager;

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
  });
} else {
  window.themeManager = new ThemeManager();
}
