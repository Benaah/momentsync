import os
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Max, Min, Q
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import statistics
import psutil
import aiohttp
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Real-time analytics and monitoring service for MomentSync
    """
    
    def __init__(self):
        self.metrics_cache_ttl = 300  # 5 minutes
        self.performance_cache_ttl = 60  # 1 minute
        self.alert_thresholds = {
            'cpu_usage': 80,
            'memory_usage': 85,
            'disk_usage': 90,
            'response_time': 2.0,
            'error_rate': 5.0,
            'active_users': 1000
        }
        
        # Initialize monitoring
        self.monitoring_active = True
        self.metrics_collector = None
    
    async def start_monitoring(self):
        """
        Start real-time monitoring
        """
        try:
            if self.monitoring_active:
                self.metrics_collector = asyncio.create_task(self._collect_metrics())
                logger.info("Analytics monitoring started")
        except Exception as e:
            logger.error(f"Error starting monitoring: {str(e)}")
    
    async def stop_monitoring(self):
        """
        Stop real-time monitoring
        """
        try:
            self.monitoring_active = False
            if self.metrics_collector:
                self.metrics_collector.cancel()
            logger.info("Analytics monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping monitoring: {str(e)}")
    
    async def _collect_metrics(self):
        """
        Collect system and application metrics
        """
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                
                # Collect application metrics
                app_metrics = await self._collect_application_metrics()
                
                # Store metrics
                await self._store_metrics(system_metrics, app_metrics)
                
                # Check for alerts
                await self._check_alerts(system_metrics, app_metrics)
                
                # Wait before next collection
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {str(e)}")
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collect system performance metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used = disk.used
            disk_total = disk.total
            
            # Network I/O
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process information
            process = psutil.Process()
            process_memory = process.memory_info().rss
            process_cpu = process.cpu_percent()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'used': memory_used,
                    'total': memory_total
                },
                'disk': {
                    'percent': disk_percent,
                    'used': disk_used,
                    'total': disk_total
                },
                'network': {
                    'bytes_sent': network_bytes_sent,
                    'bytes_recv': network_bytes_recv
                },
                'process': {
                    'memory': process_memory,
                    'cpu': process_cpu
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return {}
    
    async def _collect_application_metrics(self) -> Dict[str, Any]:
        """
        Collect application-specific metrics
        """
        try:
            # User metrics
            total_users = User.objects.count()
            active_users = await self._get_active_users()
            
            # Moment metrics
            from moments.models import Moment
            total_moments = Moment.objects.count()
            recent_moments = Moment.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Media metrics
            from moments.models import MediaItem
            total_media = MediaItem.objects.count()
            recent_media = MediaItem.objects.filter(
                uploaded_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # WebSocket connections
            websocket_connections = await self._get_websocket_connections()
            
            # API metrics
            api_metrics = await self._get_api_metrics()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'users': {
                    'total': total_users,
                    'active': active_users
                },
                'moments': {
                    'total': total_moments,
                    'recent': recent_moments
                },
                'media': {
                    'total': total_media,
                    'recent': recent_media
                },
                'websockets': {
                    'connections': websocket_connections
                },
                'api': api_metrics
            }
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {str(e)}")
            return {}
    
    async def _get_active_users(self) -> int:
        """
        Get count of active users (last 15 minutes)
        """
        try:
            active_threshold = timezone.now() - timedelta(minutes=15)
            # This would typically check user activity logs
            # For now, we'll use a placeholder
            return cache.get('active_users_count', 0)
        except Exception as e:
            logger.error(f"Error getting active users: {str(e)}")
            return 0
    
    async def _get_websocket_connections(self) -> int:
        """
        Get count of active WebSocket connections
        """
        try:
            # This would typically check WebSocket connection logs
            # For now, we'll use a placeholder
            return cache.get('websocket_connections', 0)
        except Exception as e:
            logger.error(f"Error getting WebSocket connections: {str(e)}")
            return 0
    
    async def _get_api_metrics(self) -> Dict[str, Any]:
        """
        Get API usage metrics
        """
        try:
            # Get API metrics from cache
            api_metrics = cache.get('api_metrics', {
                'requests_per_minute': 0,
                'average_response_time': 0,
                'error_rate': 0,
                'endpoints': {}
            })
            
            return api_metrics
            
        except Exception as e:
            logger.error(f"Error getting API metrics: {str(e)}")
            return {}
    
    async def _store_metrics(self, system_metrics: Dict[str, Any], app_metrics: Dict[str, Any]):
        """
        Store metrics in cache and database
        """
        try:
            # Store in cache for real-time access
            cache.set('system_metrics', system_metrics, timeout=self.metrics_cache_ttl)
            cache.set('app_metrics', app_metrics, timeout=self.metrics_cache_ttl)
            
            # Store historical data (this would typically go to a time-series database)
            timestamp = timezone.now().isoformat()
            historical_data = {
                'timestamp': timestamp,
                'system': system_metrics,
                'application': app_metrics
            }
            
            # Store in cache for historical analysis
            history_key = f'metrics_history_{timestamp[:10]}'  # Daily key
            history = cache.get(history_key, [])
            history.append(historical_data)
            
            # Keep only last 24 hours of data
            if len(history) > 1440:  # 24 hours * 60 minutes
                history = history[-1440:]
            
            cache.set(history_key, history, timeout=86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")
    
    async def _check_alerts(self, system_metrics: Dict[str, Any], app_metrics: Dict[str, Any]):
        """
        Check for alert conditions
        """
        try:
            alerts = []
            
            # Check CPU usage
            if system_metrics.get('cpu', {}).get('percent', 0) > self.alert_thresholds['cpu_usage']:
                alerts.append({
                    'type': 'cpu_usage',
                    'severity': 'warning',
                    'message': f"High CPU usage: {system_metrics['cpu']['percent']}%",
                    'timestamp': timezone.now().isoformat()
                })
            
            # Check memory usage
            if system_metrics.get('memory', {}).get('percent', 0) > self.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'memory_usage',
                    'severity': 'warning',
                    'message': f"High memory usage: {system_metrics['memory']['percent']}%",
                    'timestamp': timezone.now().isoformat()
                })
            
            # Check disk usage
            if system_metrics.get('disk', {}).get('percent', 0) > self.alert_thresholds['disk_usage']:
                alerts.append({
                    'type': 'disk_usage',
                    'severity': 'critical',
                    'message': f"High disk usage: {system_metrics['disk']['percent']}%",
                    'timestamp': timezone.now().isoformat()
                })
            
            # Check error rate
            api_metrics = app_metrics.get('api', {})
            if api_metrics.get('error_rate', 0) > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'error_rate',
                    'severity': 'warning',
                    'message': f"High error rate: {api_metrics['error_rate']}%",
                    'timestamp': timezone.now().isoformat()
                })
            
            # Store alerts
            if alerts:
                await self._store_alerts(alerts)
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    async def _store_alerts(self, alerts: List[Dict[str, Any]]):
        """
        Store alerts for monitoring
        """
        try:
            for alert in alerts:
                # Store in cache
                alert_key = f'alert_{alert["type"]}_{int(time.time())}'
                cache.set(alert_key, alert, timeout=86400)  # 24 hours
                
                # Log alert
                logger.warning(f"Alert: {alert['type']} - {alert['message']}")
                
        except Exception as e:
            logger.error(f"Error storing alerts: {str(e)}")
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for dashboard display
        """
        try:
            # Get current metrics
            system_metrics = cache.get('system_metrics', {})
            app_metrics = cache.get('app_metrics', {})
            
            # Get historical data for trends
            today = timezone.now().strftime('%Y-%m-%d')
            history_key = f'metrics_history_{today}'
            historical_data = cache.get(history_key, [])
            
            # Calculate trends
            trends = await self._calculate_trends(historical_data)
            
            # Get alerts
            alerts = await self._get_recent_alerts()
            
            return {
                'success': True,
                'system': system_metrics,
                'application': app_metrics,
                'trends': trends,
                'alerts': alerts,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _calculate_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trends from historical data
        """
        try:
            if not historical_data:
                return {}
            
            # Extract metrics over time
            cpu_usage = [data['system']['cpu']['percent'] for data in historical_data if 'system' in data]
            memory_usage = [data['system']['memory']['percent'] for data in historical_data if 'system' in data]
            active_users = [data['application']['users']['active'] for data in historical_data if 'application' in data]
            
            trends = {
                'cpu_trend': self._calculate_trend(cpu_usage),
                'memory_trend': self._calculate_trend(memory_usage),
                'users_trend': self._calculate_trend(active_users)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction (up, down, stable)
        """
        try:
            if len(values) < 2:
                return 'stable'
            
            # Calculate average of first half vs second half
            mid_point = len(values) // 2
            first_half_avg = statistics.mean(values[:mid_point])
            second_half_avg = statistics.mean(values[mid_point:])
            
            if second_half_avg > first_half_avg * 1.05:
                return 'up'
            elif second_half_avg < first_half_avg * 0.95:
                return 'down'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return 'stable'
    
    async def _get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent alerts
        """
        try:
            # This would typically query a database
            # For now, we'll return cached alerts
            alerts = []
            
            # Get alerts from cache (this is a simplified approach)
            for i in range(limit):
                alert_key = f'alert_cpu_{int(time.time()) - i}'
                alert = cache.get(alert_key)
                if alert:
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    async def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Get analytics for specific user
        """
        try:
            # Get user activity metrics
            user_metrics = {
                'moments_created': 0,
                'media_uploaded': 0,
                'last_activity': None,
                'favorite_moments': 0,
                'shared_moments': 0
            }
            
            # This would typically query the database
            # For now, we'll use cached data
            cache_key = f'user_analytics_{user_id}'
            cached_metrics = cache.get(cache_key, user_metrics)
            
            return {
                'success': True,
                'user_id': user_id,
                'metrics': cached_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_performance_report(self, time_range: str = '24h') -> Dict[str, Any]:
        """
        Get performance report for specified time range
        """
        try:
            # Calculate time range
            if time_range == '1h':
                start_time = timezone.now() - timedelta(hours=1)
            elif time_range == '24h':
                start_time = timezone.now() - timedelta(hours=24)
            elif time_range == '7d':
                start_time = timezone.now() - timedelta(days=7)
            else:
                start_time = timezone.now() - timedelta(hours=24)
            
            # Get historical data
            historical_data = []
            for i in range(7):  # Last 7 days
                date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                history_key = f'metrics_history_{date}'
                day_data = cache.get(history_key, [])
                historical_data.extend(day_data)
            
            # Filter by time range
            filtered_data = [
                data for data in historical_data
                if datetime.fromisoformat(data['timestamp']) >= start_time
            ]
            
            if not filtered_data:
                return {'success': False, 'error': 'No data available for the specified time range'}
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(filtered_data)
            
            return {
                'success': True,
                'time_range': time_range,
                'start_time': start_time.isoformat(),
                'end_time': timezone.now().isoformat(),
                'metrics': performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting performance report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _calculate_performance_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate performance metrics from historical data
        """
        try:
            # Extract metrics
            cpu_usage = [d['system']['cpu']['percent'] for d in data if 'system' in d]
            memory_usage = [d['system']['memory']['percent'] for d in data if 'system' in d]
            active_users = [d['application']['users']['active'] for d in data if 'application' in d]
            
            # Calculate statistics
            metrics = {
                'cpu': {
                    'average': statistics.mean(cpu_usage) if cpu_usage else 0,
                    'maximum': max(cpu_usage) if cpu_usage else 0,
                    'minimum': min(cpu_usage) if cpu_usage else 0
                },
                'memory': {
                    'average': statistics.mean(memory_usage) if memory_usage else 0,
                    'maximum': max(memory_usage) if memory_usage else 0,
                    'minimum': min(memory_usage) if memory_usage else 0
                },
                'users': {
                    'average': statistics.mean(active_users) if active_users else 0,
                    'maximum': max(active_users) if active_users else 0,
                    'minimum': min(active_users) if active_users else 0
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    async def export_analytics_data(self, format: str = 'json') -> Dict[str, Any]:
        """
        Export analytics data in specified format
        """
        try:
            # Get all historical data
            all_data = []
            for i in range(30):  # Last 30 days
                date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                history_key = f'metrics_history_{date}'
                day_data = cache.get(history_key, [])
                all_data.extend(day_data)
            
            if format == 'json':
                return {
                    'success': True,
                    'format': 'json',
                    'data': all_data,
                    'count': len(all_data)
                }
            elif format == 'csv':
                # Convert to CSV format
                csv_data = await self._convert_to_csv(all_data)
                return {
                    'success': True,
                    'format': 'csv',
                    'data': csv_data,
                    'count': len(all_data)
                }
            else:
                return {'success': False, 'error': 'Unsupported format'}
                
        except Exception as e:
            logger.error(f"Error exporting analytics data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _convert_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """
        Convert data to CSV format
        """
        try:
            if not data:
                return ''
            
            # Get headers from first record
            headers = ['timestamp']
            if data and 'system' in data[0]:
                headers.extend(['cpu_percent', 'memory_percent', 'disk_percent'])
            if data and 'application' in data[0]:
                headers.extend(['active_users', 'total_moments', 'total_media'])
            
            # Build CSV
            csv_lines = [','.join(headers)]
            
            for record in data:
                row = [record['timestamp']]
                
                if 'system' in record:
                    row.extend([
                        record['system']['cpu']['percent'],
                        record['system']['memory']['percent'],
                        record['system']['disk']['percent']
                    ])
                else:
                    row.extend(['', '', ''])
                
                if 'application' in record:
                    row.extend([
                        record['application']['users']['active'],
                        record['application']['moments']['total'],
                        record['application']['media']['total']
                    ])
                else:
                    row.extend(['', '', ''])
                
                csv_lines.append(','.join(map(str, row)))
            
            return '\n'.join(csv_lines)
            
        except Exception as e:
            logger.error(f"Error converting to CSV: {str(e)}")
            return ''
