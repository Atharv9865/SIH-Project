// Main JavaScript for Waste Management App

document.addEventListener('DOMContentLoaded', function() {
    console.log('Waste Management App initialized');
    
    // Sample data for demonstration
    const wasteData = {
        totalCollected: 1250,
        recycled: 450,
        landfill: 800
    };
    
    // Update stats if needed
    function updateStats(data) {
        // This would be replaced with actual API calls in a real application
        document.querySelector('.stat-card:nth-child(1) .stat-value').textContent = `${data.totalCollected} kg`;
        document.querySelector('.stat-card:nth-child(2) .stat-value').textContent = `${data.recycled} kg`;
        document.querySelector('.stat-card:nth-child(3) .stat-value').textContent = `${data.landfill} kg`;
    }
    
    // Navigation handling
    const navLinks = document.querySelectorAll('nav ul li a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // In a real app, this would load different views
            const page = this.textContent.toLowerCase();
            console.log(`Navigating to ${page} page`);
        });
    });
    
    // Initialize with sample data
    updateStats(wasteData);
});