from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'moments', views.MomentViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'media', views.MediaViewSet)
router.register(r'analytics', views.AnalyticsViewSet, basename='analytics')
router.register(r'security', views.SecurityViewSet, basename='security')
router.register(r'mobile', views.MobileViewSet, basename='mobile')
router.register(r'ai', views.AIViewSet, basename='ai')
router.register(r'storage', views.StorageViewSet, basename='storage')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework_simplejwt.urls')),
    path('docs/', include('drf_spectacular.urls')),
]
