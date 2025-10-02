from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from annoying.fields import AutoOneToOneField
import uuid


class InviteCode(models.Model):
    code = models.CharField(max_length=100)
    uses_left = models.IntegerField()

    def __str__(self):
        return "[" + str(self.uses_left) +"] " +self.code


class Moment(models.Model):
    momentID = models.CharField(primary_key=True, max_length=60)
    name = models.CharField(max_length=100, null=True)
    owner_username = models.CharField(max_length=35, null=True)
    allowed_usernames = ArrayField(models.CharField(max_length=35), default=list, null=True)
    description = models.CharField(max_length=1000, default="Click here to customize the description of this moment page.")
    
    # Media management
    imgIDs = ArrayField(models.CharField(max_length=32), default=list, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # Privacy settings
    is_public = models.BooleanField(default=False)
    allow_guests = models.BooleanField(default=False)
    
    # AI features
    ai_tags = ArrayField(models.CharField(max_length=50), default=list, null=True)
    ai_description = models.TextField(blank=True, null=True)
    
    # WebRTC settings
    webrtc_enabled = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=10)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['owner_username']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return self.momentID
    
    def add_member(self, username):
        """Add a member to the moment"""
        if username not in self.allowed_usernames:
            self.allowed_usernames.append(username)
            self.save()
    
    def remove_member(self, username):
        """Remove a member from the moment"""
        if username in self.allowed_usernames:
            self.allowed_usernames.remove(username)
            self.save()
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])



class Profile(models.Model):
    user = AutoOneToOneField(User, on_delete=models.CASCADE)
    googleID = models.CharField(primary_key=True, max_length=35)
    
    # Enhanced profile fields
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Privacy settings
    is_public = models.BooleanField(default=True)
    allow_notifications = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(default=timezone.now)
    
    # Preferences
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ])
    language = models.CharField(max_length=10, default='en')
    
    def __str__(self):
        return self.user.username
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class MediaItem(models.Model):
    """Enhanced media model for better organization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE, related_name='media_items')
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # File information
    file_id = models.CharField(max_length=32, unique=True)  # MD5 hash
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=50)
    mime_type = models.CharField(max_length=100)
    
    # URLs
    original_url = models.URLField()
    thumbnail_url = models.URLField(blank=True, null=True)
    compressed_url = models.URLField(blank=True, null=True)
    
    # AI processing results
    ai_tags = ArrayField(models.CharField(max_length=50), default=list, null=True)
    ai_description = models.TextField(blank=True, null=True)
    face_count = models.IntegerField(default=0)
    object_tags = ArrayField(models.CharField(max_length=50), default=list, null=True)
    
    # Metadata
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # For videos
    camera_info = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_processed = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['moment', 'uploaded_at']),
            models.Index(fields=['uploader']),
            models.Index(fields=['file_type']),
        ]
    
    def __str__(self):
        return f"{self.file_name} ({self.moment.momentID})"


class WebRTCConnection(models.Model):
    """Track WebRTC connections for moments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE, related_name='webrtc_connections')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Connection details
    connection_id = models.CharField(max_length=100, unique=True)
    peer_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    connected_at = models.DateTimeField(auto_now_add=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-connected_at']
        indexes = [
            models.Index(fields=['moment', 'is_active']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.moment.momentID}"


class Notification(models.Model):
    """User notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification content
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=[
        ('moment_invite', 'Moment Invitation'),
        ('media_upload', 'Media Upload'),
        ('webrtc_call', 'WebRTC Call'),
        ('system', 'System'),
    ])
    
    # Related objects
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE, null=True, blank=True)
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"