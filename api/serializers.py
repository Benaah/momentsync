from rest_framework import serializers
from django.contrib.auth.models import User
from moments.models import Moment, Profile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'google_id': profile.googleID,
                'avatar_url': getattr(profile, 'avatar_url', None)
            }
        except Profile.DoesNotExist:
            return None


class MomentSerializer(serializers.ModelSerializer):
    """Serializer for Moment model with enhanced features"""
    owner = UserSerializer(source='owner_username', read_only=True)
    member_count = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    
    class Meta:
        model = Moment
        fields = [
            'momentID', 'name', 'owner_username', 'owner', 
            'allowed_usernames', 'description', 'imgIDs',
            'member_count', 'media_count', 'last_updated'
        ]
        read_only_fields = ['momentID', 'owner_username']
    
    def get_member_count(self, obj):
        return len(obj.allowed_usernames) if obj.allowed_usernames else 0
    
    def get_media_count(self, obj):
        return len(obj.imgIDs) if obj.imgIDs else 0
    
    def get_last_updated(self, obj):
        # This would need to be tracked in the model
        return obj.updated_at if hasattr(obj, 'updated_at') else None


class MediaSerializer(serializers.Serializer):
    """Serializer for media items"""
    id = serializers.CharField()
    url = serializers.URLField()
    thumbnail_url = serializers.URLField()
    file_type = serializers.CharField()
    file_size = serializers.IntegerField()
    uploaded_at = serializers.DateTimeField()
    ai_tags = serializers.ListField(child=serializers.CharField(), required=False)
    ai_description = serializers.CharField(required=False)
    compression_ratio = serializers.FloatField(required=False)


class MomentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new moments"""
    
    class Meta:
        model = Moment
        fields = ['name', 'description']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['owner_username'] = user.username
        validated_data['allowed_usernames'] = [user.username]
        validated_data['imgIDs'] = []
        return super().create(validated_data)


class InviteUserSerializer(serializers.Serializer):
    """Serializer for inviting users to moments"""
    username = serializers.CharField(max_length=35)
    message = serializers.CharField(max_length=500, required=False)


class WebRTCOfferSerializer(serializers.Serializer):
    """Serializer for WebRTC offers"""
    offer = serializers.JSONField()
    moment_id = serializers.CharField()


class MediaUploadSerializer(serializers.Serializer):
    """Serializer for media uploads"""
    media = serializers.FileField()
    moment_id = serializers.CharField(required=False)
    ai_processing = serializers.BooleanField(default=True)
    compression_level = serializers.IntegerField(min_value=1, max_value=10, default=7)
