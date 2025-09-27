// Dark mode toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Create dark mode toggle button
    const toggleButton = document.createElement('button');
    toggleButton.className = 'dark-mode-toggle';
    toggleButton.innerHTML = '🌙';
    toggleButton.title = 'Toggle dark mode';
    document.body.appendChild(toggleButton);

    // Check for saved theme preference or detect browser preference
    const savedTheme = localStorage.getItem('theme');
    const browserPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = savedTheme || (browserPrefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Update button icon based on current theme
    updateToggleIcon(currentTheme);

    // Toggle theme on button click
    toggleButton.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateToggleIcon(newTheme);
    });

    function updateToggleIcon(theme) {
        toggleButton.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    }

    // Listen for changes in browser dark mode preference
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            updateToggleIcon(newTheme);
        }
    });
});