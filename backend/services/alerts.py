"""
Alerts & Monitoring System
Detects sentiment spikes, trend changes, and generates alerts
"""
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert:
    """Individual alert object"""
    
    def __init__(self, 
                 alert_type: str,
                 product: str,
                 severity: AlertSeverity,
                 message: str,
                 details: Dict[str, Any] = None,
                 timestamp: datetime = None):
        self.id = f"{product}_{alert_type}_{int(datetime.now().timestamp())}"
        self.alert_type = alert_type
        self.product = product
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.timestamp = timestamp or datetime.now()
        self.read = False
        self.acknowledged = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.alert_type,
            "product": self.product,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read,
            "acknowledged": self.acknowledged
        }


class AlertSystem:
    """Centralized alert management system"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.subscribers = []  # For email/webhook subscriptions
        self.thresholds = {
            "sentiment_spike": 20,  # % change
            "sentiment_drop": 15,   # % change
            "topic_surge": 30,      # % increase in mentions
            "negative_trend": -0.1, # sentiment score change
        }
        logger.info("Alert system initialized")
    
    def check_sentiment_spike(self,
                            product: str,
                            previous_sentiment: float,
                            current_sentiment: float) -> Alert | None:
        """
        Check for sentiment spike
        
        Args:
            product: Product name
            previous_sentiment: Previous sentiment score
            current_sentiment: Current sentiment score
        
        Returns:
            Alert if spike detected, None otherwise
        """
        if previous_sentiment == 0:
            return None
        
        change_percent = abs((current_sentiment - previous_sentiment) / abs(previous_sentiment)) * 100
        
        if change_percent >= self.thresholds["sentiment_spike"]:
            severity = AlertSeverity.CRITICAL if change_percent >= 40 else AlertSeverity.WARNING
            direction = "[UP] spike" if current_sentiment > previous_sentiment else "[DOWN] drop"
            
            alert = Alert(
                alert_type="sentiment_spike",
                product=product,
                severity=severity,
                message=f"Sentiment {direction}: {change_percent:.1f}% change detected for {product}",
                details={
                    "previous": round(previous_sentiment, 3),
                    "current": round(current_sentiment, 3),
                    "change_percent": round(change_percent, 2),
                    "direction": "positive" if current_sentiment > previous_sentiment else "negative"
                }
            )
            
            return alert
        
        return None
    
    def check_negative_trend(self,
                           product: str,
                           sentiment_trend: float,
                           trend_strength: str) -> Alert | None:
        """
        Check for negative sentiment trend
        
        Args:
            product: Product name
            sentiment_trend: Trend slope (negative = declining)
            trend_strength: Trend strength description
        
        Returns:
            Alert if negative trend detected
        """
        if sentiment_trend < self.thresholds["negative_trend"] and trend_strength == "strong":
            alert = Alert(
                alert_type="negative_trend",
                product=product,
                severity=AlertSeverity.WARNING,
                message=f"Strong negative sentiment trend detected for {product}. Investigate customer concerns.",
                details={
                    "trend_slope": round(sentiment_trend, 4),
                    "trend_strength": trend_strength,
                    "recommendation": "Review recent customer feedback and address common complaints"
                }
            )
            
            return alert
        
        return None
    
    def check_topic_surge(self,
                        product: str,
                        topic_name: str,
                        previous_mention_count: int,
                        current_mention_count: int) -> Alert | None:
        """
        Check for topic surge (sudden increase in mentions)
        
        Args:
            product: Product name
            topic_name: Topic that surged
            previous_mention_count: Previous mentions
            current_mention_count: Current mentions
        
        Returns:
            Alert if surge detected
        """
        if previous_mention_count == 0:
            if current_mention_count >= 5:
                alert = Alert(
                    alert_type="topic_surge",
                    product=product,
                    severity=AlertSeverity.INFO,
                    message=f"New topic emerged for {product}: '{topic_name}' gaining attention",
                    details={
                        "topic": topic_name,
                        "mentions": current_mention_count
                    }
                )
                return alert
            return None
        
        surge_percent = ((current_mention_count - previous_mention_count) / previous_mention_count) * 100
        
        if surge_percent >= self.thresholds["topic_surge"]:
            severity = AlertSeverity.WARNING if surge_percent >= 50 else AlertSeverity.INFO
            
            alert = Alert(
                alert_type="topic_surge",
                product=product,
                severity=severity,
                message=f"Topic '{topic_name}' surged {surge_percent:.0f}% for {product}",
                details={
                    "topic": topic_name,
                    "previous_mentions": previous_mention_count,
                    "current_mentions": current_mention_count,
                    "surge_percent": round(surge_percent, 2)
                }
            )
            
            return alert
        
        return None
    
    def check_quality_concerns(self,
                             product: str,
                             negative_aspects: List[str],
                             negative_count: int) -> Alert | None:
        """
        Check for recurring quality concerns
        
        Args:
            product: Product name
            negative_aspects: List of aspects with negative sentiment
            negative_count: Count of negative reviews
        
        Returns:
            Alert if quality issues detected
        """
        if not negative_aspects or negative_count < 3:
            return None
        
        # Check if same aspects keep appearing
        if len(negative_aspects) >= 2:
            alert = Alert(
                alert_type="quality_concern",
                product=product,
                severity=AlertSeverity.WARNING,
                message=f"Multiple quality concerns reported for {product}: {', '.join(negative_aspects[:3])}",
                details={
                    "aspects": negative_aspects,
                    "concern_count": negative_count,
                    "recommendation": f"Prioritize improvements in: {negative_aspects[0]}, {negative_aspects[1] if len(negative_aspects) > 1 else 'and other areas'}"
                }
            )
            
            return alert
        
        return None
    
    def add_alert(self, alert: Alert) -> None:
        """Add alert to system"""
        self.alerts.append(alert)
        logger.info(f"Alert created: {alert.alert_type} for {alert.product}")
        self._notify_subscribers(alert)
    
    def _notify_subscribers(self, alert: Alert) -> None:
        """Notify subscribers of new alert (stub for email/webhook)"""
        # This would be extended to send emails, webhooks, etc.
        for subscriber in self.subscribers:
            if subscriber.get("enabled"):
                # Send notification
                logger.info(f"Notifying subscriber: {subscriber.get('email', 'webhook')}")
    
    def get_active_alerts(self, product: str = None, severity: AlertSeverity = None) -> List[Dict[str, Any]]:
        """
        Get active alerts
        
        Args:
            product: Filter by product (optional)
            severity: Filter by severity (optional)
        
        Returns:
            List of alert dictionaries
        """
        alerts = self.alerts
        
        if product:
            alerts = [a for a in alerts if a.product == product]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return [a.to_dict() for a in alerts]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
        return False
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total = len(self.alerts)
        critical = len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL])
        warning = len([a for a in self.alerts if a.severity == AlertSeverity.WARNING])
        info = len([a for a in self.alerts if a.severity == AlertSeverity.INFO])
        
        unacknowledged = len([a for a in self.alerts if not a.acknowledged])
        
        return {
            "total_active": total,
            "critical": critical,
            "warning": warning,
            "info": info,
            "unacknowledged": unacknowledged,
            "critical_percentage": round((critical / total * 100) if total > 0 else 0, 1)
        }
    
    def generate_daily_digest(self, product: str = None) -> Dict[str, Any]:
        """
        Generate daily alert digest
        
        Args:
            product: Generate digest for specific product (optional)
        
        Returns:
            Digest summary and alerts
        """
        cutoff_time = datetime.now() - timedelta(days=1)
        
        recent_alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
        
        if product:
            recent_alerts = [a for a in recent_alerts if a.product == product]
        
        # Group by type
        alerts_by_type = {}
        for alert in recent_alerts:
            if alert.alert_type not in alerts_by_type:
                alerts_by_type[alert.alert_type] = []
            alerts_by_type[alert.alert_type].append(alert)
        
        return {
            "period": "last_24_hours",
            "generated_at": datetime.now().isoformat(),
            "total_alerts": len(recent_alerts),
            "summary": {
                alert_type: len(alerts) for alert_type, alerts in alerts_by_type.items()
            },
            "alerts": [a.to_dict() for a in recent_alerts[:10]],  # Top 10 recent
            "products_affected": list(set(a.product for a in recent_alerts))
        }
    
    def clear_acknowledged_alerts(self, days: int = 7) -> int:
        """
        Clear old acknowledged alerts
        
        Args:
            days: Clear alerts older than N days
        
        Returns:
            Number of alerts cleared
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        original_count = len(self.alerts)
        
        self.alerts = [a for a in self.alerts 
                      if not (a.acknowledged and a.timestamp < cutoff_time)]
        
        cleared = original_count - len(self.alerts)
        logger.info(f"Cleared {cleared} old alerts")
        
        return cleared


# Global instance
_alert_system = None

def get_alert_system() -> AlertSystem:
    """Get or create alert system"""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system
