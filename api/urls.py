from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'moments', views.MomentViewSet, basename='moments')
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'media', views.MediaViewSet, basename='media')
router.register(r'analytics', views.AnalyticsViewSet, basename='analytics')
router.register(r'security', views.SecurityViewSet, basename='security')
router.register(r'mobile', views.MobileViewSet, basename='mobile')
router.register(r'ai', views.AIViewSet, basename='ai')
router.register(r'storage', views.StorageViewSet, basename='storage')

urlpatterns = [
    path('', include(router.urls)),
    # Authentication endpoints
    path('auth/google/', views.google_auth, name='google_auth'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
]
