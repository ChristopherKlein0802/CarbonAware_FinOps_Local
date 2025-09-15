#!/usr/bin/env python3
"""
Health Check Dashboard Integration
Carbon-Aware FinOps Dashboard - Bachelor Thesis

Provides health monitoring for dashboard integration:
- Startup health verification
- Runtime monitoring endpoints
- Health status for dashboard tabs
"""

import logging
from typing import Dict, List
from datetime import datetime
from dash import html
from .health_checks import health_check_manager, quick_health_check

logger = logging.getLogger(__name__)


class DashboardHealthIntegration:
    """Health monitoring integration for dashboard components."""

    def __init__(self):
        """Initialize health integration."""
        self.last_health_check = None
        self.health_cache = None
        self.cache_duration = 60  # Cache health results for 1 minute

    def get_startup_health_check(self) -> Dict:
        """
        Perform comprehensive health check during dashboard startup.
        
        Returns:
            Dict: Health status and recommendations
        """
        logger.info("🔍 Starting dashboard startup health check...")
        
        health_results = health_check_manager.check_all_apis()
        overall_health = health_results['system_overall']
        
        startup_status = {
            'ready_to_start': overall_health['dashboard_ready'],
            'health_summary': health_check_manager.get_health_summary(),
            'api_details': {
                'electricitymap': {
                    'status': health_results['electricitymap']['status'],
                    'api_key_configured': health_results['electricitymap']['api_key_configured'],
                    'response_time': health_results['electricitymap']['response_time_ms']
                },
                'boavizta': {
                    'status': health_results['boavizta']['status'],
                    'response_time': health_results['boavizta']['response_time_ms']
                },
                'aws_cost_explorer': {
                    'status': health_results['aws_cost_explorer']['status'],
                    'aws_profile_configured': health_results['aws_cost_explorer']['aws_profile_configured'],
                    'response_time': health_results['aws_cost_explorer']['response_time_ms']
                }
            },
            'recommendations': self._generate_startup_recommendations(health_results)
        }
        
        return startup_status

    def _generate_startup_recommendations(self, health_results: Dict) -> List[str]:
        """Generate startup recommendations based on health status."""
        recommendations = []
        
        # ElectricityMap recommendations
        em_status = health_results['electricitymap']
        if em_status['status'] == 'error':
            if not em_status['api_key_configured']:
                recommendations.append("⚠️ Set ELECTRICITYMAP_API_KEY in .env file for real-time German grid data")
            else:
                recommendations.append("⚠️ ElectricityMap API unavailable - check network connection")
        
        # AWS recommendations  
        aws_status = health_results['aws_cost_explorer']
        if aws_status['status'] == 'error':
            if not aws_status['aws_profile_configured']:
                recommendations.append("⚠️ Configure AWS profile with 'aws configure sso' for cost data")
            else:
                recommendations.append("⚠️ AWS Cost Explorer access denied - check IAM permissions")
        
        # Boavizta recommendations
        boavizta_status = health_results['boavizta']
        if boavizta_status['status'] == 'error':
            recommendations.append("⚠️ Boavizta API unavailable - power consumption data will be missing")
        
        # Overall recommendations
        overall_status = health_results['system_overall']['overall_status']
        if overall_status == 'healthy':
            recommendations.append("✅ All APIs operational - dashboard fully functional")
        elif overall_status == 'degraded':
            recommendations.append("⚠️ Some APIs degraded - dashboard functional with limited features")
        else:
            recommendations.append("❌ Multiple API issues - dashboard will show limited data")
            
        return recommendations

    def create_health_status_card(self) -> html.Div:
        """Create health status card for dashboard display."""
        try:
            # Use cached results if recent
            now = datetime.now()
            if (self.health_cache and self.last_health_check and 
                (now - self.last_health_check).seconds < self.cache_duration):
                health_results = self.health_cache
            else:
                health_results = health_check_manager.check_all_apis()
                self.health_cache = health_results
                self.last_health_check = now
            
            overall_status = health_results['system_overall']['overall_status']
            
            # Status colors and icons
            status_config = {
                'healthy': {'icon': '✅', 'color': '#28a745', 'text': 'All Systems Operational'},
                'degraded': {'icon': '⚠️', 'color': '#ffc107', 'text': 'Some Services Degraded'},
                'error': {'icon': '❌', 'color': '#dc3545', 'text': 'System Issues Detected'}
            }
            
            config = status_config.get(overall_status, status_config['error'])
            
            # Create API status details
            api_statuses = []
            for api_name, api_data in health_results.items():
                if api_name != 'system_overall':
                    status = api_data.get('status', 'unknown')
                    response_time = api_data.get('response_time_ms', 0)
                    
                    api_statuses.append(
                        html.Div([
                            html.Span(f"{api_name.replace('_', ' ').title()}: "),
                            html.Span(
                                status.upper(), 
                                style={'color': status_config.get(status, {}).get('color', '#6c757d')}
                            ),
                            html.Span(f" ({response_time:.0f}ms)" if response_time > 0 else "")
                        ], className="api-status-item")
                    )
            
            return html.Div([
                html.Div([
                    html.Div([
                        html.Div(config['icon'], className="health-icon"),
                        html.Div([
                            html.H4("System Health", className="health-title"),
                            html.P(config['text'], className="health-status-text"),
                            html.Div([
                                html.P(f"Services: {health_results['system_overall']['services_healthy']}/{health_results['system_overall']['total_services']} operational"),
                                html.P(f"Last Check: {datetime.now().strftime('%H:%M:%S')}")
                            ], className="health-details")
                        ], className="health-content")
                    ], className="health-header"),
                    
                    html.Div([
                        html.H5("API Status Details", className="health-subtitle"),
                        html.Div(api_statuses, className="api-statuses")
                    ], className="health-api-details")
                ], className="health-card-inner")
            ], className="health-status-card", style={
                'border-left': f'4px solid {config["color"]}',
                'background': 'rgba(255,255,255,0.95)',
                'border-radius': '8px',
                'padding': '16px',
                'margin': '16px 0',
                'box-shadow': '0 2px 8px rgba(0,0,0,0.1)'
            })
            
        except Exception as e:
            logger.error(f"Failed to create health status card: {e}")
            return html.Div([
                html.P("⚠️ Health monitoring unavailable", 
                       style={'color': '#ffc107', 'padding': '16px'})
            ], className="health-error-card")

    def get_health_metrics_for_monitoring(self) -> Dict:
        """Get health metrics for external monitoring systems."""
        try:
            health_results = health_check_manager.check_all_apis()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': health_results['system_overall']['overall_status'],
                'services_healthy': health_results['system_overall']['services_healthy'],
                'services_total': health_results['system_overall']['total_services'],
                'dashboard_ready': health_results['system_overall']['dashboard_ready'],
                'api_response_times': {
                    api_name: api_data.get('response_time_ms', 0)
                    for api_name, api_data in health_results.items()
                    if api_name != 'system_overall' and 'response_time_ms' in api_data
                }
            }
        except Exception as e:
            logger.error(f"Failed to get health metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }

    def check_critical_dependencies(self) -> bool:
        """
        Quick check of critical dependencies for dashboard operation.
        
        Returns:
            bool: True if dashboard can operate with current API status
        """
        try:
            return quick_health_check()
        except Exception as e:
            logger.error(f"Critical dependency check failed: {e}")
            return False

    def get_troubleshooting_guide(self, health_results: Dict = None) -> Dict:
        """Generate troubleshooting guide based on current health status."""
        if health_results is None:
            try:
                health_results = health_check_manager.check_all_apis()
            except Exception:
                return {"error": "Unable to generate troubleshooting guide"}
        
        troubleshooting = {
            'electricitymap_issues': [],
            'aws_issues': [],
            'boavizta_issues': [],
            'general_issues': []
        }
        
        # ElectricityMap troubleshooting
        em_status = health_results.get('electricitymap', {})
        if em_status.get('status') != 'healthy':
            if not em_status.get('api_key_configured'):
                troubleshooting['electricitymap_issues'].append({
                    'issue': 'API key not configured',
                    'solution': 'Add ELECTRICITYMAP_API_KEY=your_key to .env file',
                    'get_key_url': 'https://app.electricitymap.org/map'
                })
            else:
                troubleshooting['electricitymap_issues'].append({
                    'issue': 'API connection failed',
                    'solution': 'Check network connection and API key validity',
                    'test_command': 'curl -H "auth-token: YOUR_KEY" https://api-access.electricitymaps.com/v3/carbon-intensity/latest?zone=DE'
                })
        
        # AWS troubleshooting
        aws_status = health_results.get('aws_cost_explorer', {})
        if aws_status.get('status') != 'healthy':
            troubleshooting['aws_issues'].append({
                'issue': 'AWS Cost Explorer access failed',
                'solutions': [
                    'Configure AWS profile: aws configure sso',
                    'Check IAM permissions for Cost Explorer',
                    'Verify AWS_PROFILE environment variable'
                ]
            })
        
        # Boavizta troubleshooting
        boavizta_status = health_results.get('boavizta', {})
        if boavizta_status.get('status') != 'healthy':
            troubleshooting['boavizta_issues'].append({
                'issue': 'Boavizta API unavailable',
                'solution': 'Check network connection to api.boavizta.org',
                'impact': 'Power consumption data will be unavailable'
            })
        
        return troubleshooting


# Create global instance for easy importing
dashboard_health = DashboardHealthIntegration()


def print_startup_health_check():
    """Print comprehensive health check during dashboard startup."""
    startup_health = dashboard_health.get_startup_health_check()
    
    print("\n" + "="*60)
    print("🏥 DASHBOARD HEALTH CHECK")
    print("="*60)
    
    print(startup_health['health_summary'])
    
    if startup_health['recommendations']:
        print("\n📋 Startup Recommendations:")
        for rec in startup_health['recommendations']:
            print(f"   {rec}")
    
    print("\n" + "="*60)
    
    return startup_health['ready_to_start']


if __name__ == "__main__":
    # CLI health dashboard
    print("🏥 Dashboard Health Check System")
    ready = print_startup_health_check()
    
    if ready:
        print("✅ Dashboard ready to start!")
    else:
        print("⚠️ Dashboard may have limited functionality")
        
    # Show troubleshooting guide
    guide = dashboard_health.get_troubleshooting_guide()
    if any(guide.values()):
        print("\n🔧 Troubleshooting Guide:")
        for category, issues in guide.items():
            if issues:
                print(f"\n{category.replace('_', ' ').title()}:")
                for issue in issues:
                    if isinstance(issue, dict):
                        print(f"  • {issue.get('issue', 'Unknown issue')}")
                        print(f"    Solution: {issue.get('solution', 'No solution available')}")