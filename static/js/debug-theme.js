// Debug Theme Testing
// ===================

document.addEventListener('DOMContentLoaded', function() {
    // テーマ切り替えのテスト関数
    window.testTheme = function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        console.log('Current theme:', currentTheme);
        console.log('Switching to:', newTheme);
        
        document.documentElement.setAttribute('data-theme', newTheme);
        
        console.log('Theme after switch:', document.documentElement.getAttribute('data-theme'));
        
        // CSS変数値をチェック
        const computedStyles = getComputedStyle(document.documentElement);
        console.log('--color-bg-primary:', computedStyles.getPropertyValue('--color-bg-primary'));
        console.log('--color-text-primary:', computedStyles.getPropertyValue('--color-text-primary'));
    };
    
    // ボタンを動的に追加してテスト
    const testButton = document.createElement('button');
    testButton.textContent = 'TEST THEME';
    testButton.style.cssText = 'position: fixed; top: 10px; right: 10px; z-index: 9999; padding: 10px; background: red; color: white; border: none; cursor: pointer;';
    testButton.onclick = window.testTheme;
    document.body.appendChild(testButton);
    
    // 初期状態をログ出力
    console.log('Initial theme setup:');
    console.log('data-theme:', document.documentElement.getAttribute('data-theme'));
    const computedStyles = getComputedStyle(document.documentElement);
    console.log('--color-bg-primary:', computedStyles.getPropertyValue('--color-bg-primary'));
    console.log('--color-text-primary:', computedStyles.getPropertyValue('--color-text-primary'));
});
