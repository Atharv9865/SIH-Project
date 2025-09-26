/**
 * Mobile-specific features for Swachhata Sentinel
 * Handles camera integration and touch-friendly interface
 */

// Camera access and photo capture
const MobileCamera = {
    videoElement: null,
    canvasElement: null,
    stream: null,
    
    // Initialize camera functionality
    init: function(videoEl, canvasEl) {
        this.videoElement = videoEl;
        this.canvasElement = canvasEl;
        
        // Add mobile detection
        document.body.classList.toggle('mobile-device', this.isMobileDevice());
        
        // Setup event listeners for mobile-specific features
        this.setupEventListeners();
    },
    
    // Check if user is on a mobile device
    isMobileDevice: function() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    // Setup mobile-specific event listeners
    setupEventListeners: function() {
        // Add touch events for map interactions
        if (this.isMobileDevice()) {
            // Enable pinch-to-zoom on map (already supported by Leaflet)
            // Add swipe detection for photo gallery
            this.setupSwipeDetection();
            
            // Add offline support
            this.setupOfflineSupport();
            
            // Add large buttons for mobile
            document.querySelectorAll('.submit-btn, .report-btn').forEach(btn => {
                btn.classList.add('mobile-button');
            });
        }
    },
    
    // Start camera stream
    startCamera: async function() {
        try {
            // Request camera access with rear camera preference
            const constraints = { 
                video: { 
                    facingMode: { ideal: 'environment' },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            if (this.videoElement) {
                this.videoElement.srcObject = this.stream;
                this.videoElement.play();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Could not access camera. Please check permissions and try again.');
            return false;
        }
    },
    
    // Stop camera stream
    stopCamera: function() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            
            if (this.videoElement) {
                this.videoElement.srcObject = null;
            }
        }
    },
    
    // Take a picture from the video stream
    takePicture: function() {
        if (!this.videoElement || !this.canvasElement) return null;
        
        const context = this.canvasElement.getContext('2d');
        const width = this.videoElement.videoWidth;
        const height = this.videoElement.videoHeight;
        
        if (width && height) {
            // Set canvas dimensions to match video
            this.canvasElement.width = width;
            this.canvasElement.height = height;
            
            // Draw video frame to canvas
            context.drawImage(this.videoElement, 0, 0, width, height);
            
            // Convert to blob
            return new Promise(resolve => {
                this.canvasElement.toBlob(blob => {
                    resolve(blob);
                }, 'image/jpeg', 0.85);
            });
        }
        
        return null;
    },
    
    // Setup swipe detection for photo gallery
    setupSwipeDetection: function() {
        let touchStartX = 0;
        let touchEndX = 0;
        
        const photoDetails = document.getElementById('photoDetailsModal');
        if (!photoDetails) return;
        
        photoDetails.addEventListener('touchstart', e => {
            touchStartX = e.changedTouches[0].screenX;
        }, false);
        
        photoDetails.addEventListener('touchend', e => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe(touchStartX, touchEndX);
        }, false);
    },
    
    // Handle swipe gestures
    handleSwipe: function(startX, endX) {
        const swipeThreshold = 50;
        
        if (endX < startX - swipeThreshold) {
            // Swipe left - next photo
            this.nextPhoto();
        }
        
        if (endX > startX + swipeThreshold) {
            // Swipe right - previous photo
            this.prevPhoto();
        }
    },
    
    // Navigate to next photo in current zone
    nextPhoto: function() {
        // This will be implemented when viewing zone photos
        if (window.currentZonePhotos && window.currentPhotoIndex !== undefined) {
            const nextIndex = (window.currentPhotoIndex + 1) % window.currentZonePhotos.length;
            window.showPhotoDetails(window.currentZonePhotos[nextIndex]);
            window.currentPhotoIndex = nextIndex;
        }
    },
    
    // Navigate to previous photo in current zone
    prevPhoto: function() {
        // This will be implemented when viewing zone photos
        if (window.currentZonePhotos && window.currentPhotoIndex !== undefined) {
            const prevIndex = (window.currentPhotoIndex - 1 + window.currentZonePhotos.length) % window.currentZonePhotos.length;
            window.showPhotoDetails(window.currentZonePhotos[prevIndex]);
            window.currentPhotoIndex = prevIndex;
        }
    },
    
    // Setup offline support for photo uploads
    setupOfflineSupport: function() {
        // Check if browser supports IndexedDB
        if (!window.indexedDB) {
            console.log('This browser doesn\'t support IndexedDB for offline storage');
            return;
        }
        
        // Initialize offline queue
        this.initOfflineQueue();
        
        // Listen for online/offline events
        window.addEventListener('online', this.processOfflineQueue.bind(this));
        window.addEventListener('offline', () => {
            console.log('Device is offline. Photos will be queued for later upload.');
            document.body.classList.add('offline-mode');
        });
        
        if (navigator.onLine) {
            this.processOfflineQueue();
        } else {
            document.body.classList.add('offline-mode');
        }
    },
    
    // Initialize IndexedDB for offline queue
    initOfflineQueue: function() {
        const request = indexedDB.open('WasteReportDB', 1);
        
        request.onerror = function(event) {
            console.error('IndexedDB error:', event.target.errorCode);
        };
        
        request.onupgradeneeded = function(event) {
            const db = event.target.result;
            
            // Create object store for offline photo queue
            if (!db.objectStoreNames.contains('offlinePhotos')) {
                const store = db.createObjectStore('offlinePhotos', { keyPath: 'id', autoIncrement: true });
                store.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    },
    
    // Add photo to offline queue
    addToOfflineQueue: function(photoBlob, latitude, longitude) {
        const request = indexedDB.open('WasteReportDB', 1);
        
        request.onsuccess = function(event) {
            const db = event.target.result;
            const transaction = db.transaction(['offlinePhotos'], 'readwrite');
            const store = transaction.objectStore('offlinePhotos');
            
            // Create record
            const record = {
                photo: photoBlob,
                latitude: latitude,
                longitude: longitude,
                timestamp: new Date().toISOString(),
                user_id: '1' // Default user ID
            };
            
            // Add to store
            const addRequest = store.add(record);
            
            addRequest.onsuccess = function() {
                console.log('Photo saved to offline queue');
                alert('You are offline. Photo saved and will be uploaded when connection is restored.');
            };
            
            addRequest.onerror = function() {
                console.error('Error saving photo to offline queue');
            };
        };
    },
    
    // Process offline queue when online
    processOfflineQueue: function() {
        document.body.classList.remove('offline-mode');
        
        const request = indexedDB.open('WasteReportDB', 1);
        
        request.onsuccess = function(event) {
            const db = event.target.result;
            const transaction = db.transaction(['offlinePhotos'], 'readwrite');
            const store = transaction.objectStore('offlinePhotos');
            const index = store.index('timestamp');
            
            index.openCursor().onsuccess = function(event) {
                const cursor = event.target.result;
                
                if (cursor) {
                    const record = cursor.value;
                    
                    // Upload the photo
                    const formData = new FormData();
                    formData.append('photo', record.photo);
                    formData.append('latitude', record.latitude);
                    formData.append('longitude', record.longitude);
                    formData.append('user_id', record.user_id);
                    
                    fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Remove from queue after successful upload
                            const deleteRequest = store.delete(cursor.primaryKey);
                            deleteRequest.onsuccess = function() {
                                console.log('Offline photo uploaded and removed from queue');
                            };
                            
                            // Move to next item
                            cursor.continue();
                        } else {
                            console.error('Failed to upload offline photo:', data.error);
                            // Keep in queue and try again later
                            cursor.continue();
                        }
                    })
                    .catch(error => {
                        console.error('Error uploading offline photo:', error);
                        // Keep in queue and try again later
                        cursor.continue();
                    });
                } else {
                    console.log('All offline photos processed');
                }
            };
        };
    }
};

// Export for use in main application
window.MobileCamera = MobileCamera;