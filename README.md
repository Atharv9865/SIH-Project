# Swachhata Sentinel - Production Deployment

This document outlines the production deployment setup for the Swachhata Sentinel application with real-time functionality.

## Quick Start

```bash
# Initialize your project
git clone your-repo-url
cd swachhata-sentinel
pip install -r requirements.txt

# Run the application (development mode)
python start.py

# Run the application (production mode)
python start.py --mode production

# Start only specific components
python app.py                                  # Backend server
celery -A ml.image_processor worker --loglevel=info  # Image processing worker
```

### Access URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Dashboard**: http://localhost:8000/admin

## Architecture Overview

The application uses a modern stack designed for real-time processing and spatial data:

- **Backend**: FastAPI with WebSocket support
- **Database**: PostgreSQL with PostGIS for spatial queries
- **Caching/Messaging**: Redis for WebSocket connections and Pub/Sub
- **Async Processing**: Celery for image analysis
- **Frontend**: React.js with PWA capabilities

## Deployment Instructions

### Prerequisites

- Docker and Docker Compose
- 4GB+ RAM recommended
- 10GB+ disk space

### Environment Setup

1. Clone the repository
2. Configure environment variables in `.env` files (backend and frontend)
3. Ensure the ML model is placed in the `/models` directory

### Deployment Steps

```bash
# Build and start all services
docker-compose up -d

# Monitor logs
docker-compose logs -f

# Scale workers if needed
docker-compose up -d --scale celery_worker=3
```

### Accessing the Application

- **Frontend**: http://localhost
- **API**: http://localhost/api
- **Health Check**: http://localhost/health

## Key Features

### Real-time Infrastructure

- **WebSocket Server**: Provides live updates to connected clients
- **Redis Pub/Sub**: Broadcasts zone changes to all services
- **Background Workers**: Process images asynchronously

### Offline Capabilities

The frontend includes PWA features for offline functionality:
- Service workers for caching
- IndexedDB for local storage
- Background sync for uploads

## Monitoring and Maintenance

### Health Checks

- API endpoint: `/health`
- Database connection status
- Redis connection status

### Scaling

The application can be scaled horizontally:
- API servers can be load-balanced
- Celery workers can be scaled independently
- Redis can be configured for clustering

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check PostgreSQL container logs
   - Verify environment variables

2. **WebSocket Connection Issues**
   - Check NGINX configuration
   - Verify proxy settings

3. **Image Processing Failures**
   - Check Celery worker logs
   - Verify ML model path

## Security Considerations

- All services run in isolated containers
- Environment variables for sensitive information
- NGINX configured for proper headers
- No secrets in code repositories