# MomentSync 2.0 - Real-time Media Sharing Platform

##  Introduction

MomentSync 2.0 is a modern, real-time media sharing and synchronization platform that enables instant sharing of photos and videos between devices and friends. Built with cutting-edge technologies, it provides seamless real-time communication, AI-powered features, and a beautiful user experience.
Moment Sync is an instant media syncing and sharing service that aims to simplify and 
speed up the process of syncing media between your devices or your friends. It has a 
permission system that makes full use of "channels". It enables both private and public 
sharing of images/videos instantly (no refresh needed!) between all authorized channel 
members (which could be your phone, laptop, or your friend's device that has a browser on 
it).

## Key Features

### Real-time Synchronization
- **Instant Media Sharing**: Upload and share media instantly across all connected devices
- **Live Updates**: Real-time notifications and updates via WebSocket connections
- **Cross-platform**: Works seamlessly on desktop, mobile, and tablet devices

###  Advanced Media Features
- **AI-Powered Processing**: Automatic image tagging, description generation, and content analysis
- **Smart Compression**: Optimized file sizes with modern formats (WebP/AVIF)
- **Camera Integration**: Native camera access with real-time capture
- **Media Gallery**: Beautiful grid layout with lazy loading and infinite scroll

### WebRTC Communication
- **Peer-to-Peer Video Calls**: Direct video communication between users
- **Screen Sharing**: Share your screen during video calls
- **Real-time Chat**: Text messaging with typing indicators

### Security & Privacy
- **JWT Authentication**: Secure token-based authentication
- **End-to-End Encryption**: Encrypted media transmission
- **Privacy Controls**: Granular permission management
- **Rate Limiting**: Protection against abuse

### Progressive Web App (PWA)
- **Offline Support**: Works without internet connection
- **Push Notifications**: Real-time notifications even when app is closed
- **Installable**: Install as native app on any device
- **Responsive Design**: Optimized for all screen sizes

## Technology Stack

### Backend
- **Django 5.0+**: Modern Python web framework with async support
- **Django REST Framework**: Powerful API framework
- **Django Channels**: WebSocket support for real-time features
- **PostgreSQL**: Robust database with JSON support
- **Redis**: Caching and session management
- **Celery**: Background task processing

### Frontend
- **React 18**: Modern UI library with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Smooth animations and transitions
- **React Query**: Server state management
- **Zustand**: Client state management

### Real-time Communication
- **WebSocket**: Real-time bidirectional communication
- **WebRTC**: Peer-to-peer video/audio communication
- **Socket.IO**: Enhanced WebSocket library

### Cloud & Storage
- **AWS S3**: Scalable cloud storage
- **CloudFront CDN**: Global content delivery
- **Image Processing**: OpenCV, Pillow for image optimization

### AI & Machine Learning
- **Computer Vision**: Face detection, object recognition
- **Natural Language Processing**: Image description generation
- **Content Moderation**: Automated content filtering

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Benaah/momentsync.git 
   git clone https://github.com/MarkYHZhang/momentsync.git
   cd momentsync
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

4. **Build for production**
   ```bash
   npm run build
   ```

## API Documentation

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Refresh access token
- `GET /api/users/me/` - Get current user profile

### Moments
- `GET /api/moments/` - List user's moments
- `POST /api/moments/` - Create new moment
- `GET /api/moments/{id}/` - Get moment details
- `PATCH /api/moments/{id}/` - Update moment
- `DELETE /api/moments/{id}/` - Delete moment

### Media
- `POST /api/moments/{id}/add_media/` - Upload media to moment
- `DELETE /api/moments/{id}/remove_media/` - Remove media from moment
- `GET /api/media/` - List user's media

### WebSocket Events
- `join_moment` - Join a moment room
- `leave_moment` - Leave a moment room
- `media_added` - Media added notification
- `media_removed` - Media removed notification
- `webrtc_offer` - WebRTC offer for video call
- `webrtc_answer` - WebRTC answer for video call
- `typing` - Typing indicator

## Configuration

### Environment Variables

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=momentsync
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=7
```

## Deployment

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Production Deployment

1. **Configure production settings**
   ```bash
   export DEBUG=False
   export ALLOWED_HOSTS=yourdomain.com
   ```

2. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn momentsync.wsgi:application
   ```

4. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /ws/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django community for the excellent framework
- React team for the amazing UI library
- All contributors who helped make this project better

## Support

For support, email support@momentsync.com or join our Discord server.

---

**MomentSync 2.0** - Bringing people together through shared moments 
