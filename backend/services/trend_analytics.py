"""
Trend Analytics & Forecasting Engine
Analyzes sentiment trends, detects anomalies, and forecasts future sentiment
"""
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

class TrendAnalyticsEngine:
    """Analyze and forecast sentiment trends with anomaly detection"""
    
    def __init__(self):
        logger.info("Trend analytics engine initialized")
        self.anomaly_threshold = 2.0  # Standard deviations
    
    def analyze_sentiment_trend(self, 
                               sentiments: List[float],
                               dates: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment trend over time
        
        Args:
            sentiments: Sentiment scores over time
            dates: Corresponding dates
        
        Returns:
            Trend analysis with direction, strength, and forecast
        """
        try:
            if len(sentiments) < 2:
                return {"status": "insufficient_data", "message": "Need at least 2 data points"}
            
            df = self._prepare_data(sentiments, dates)
            
            # Calculate trend metrics
            trend = self._calculate_trend(df)
            volatility = self._calculate_volatility(df)
            momentum = self._calculate_momentum(df)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(df)
            
            # Forecast next 30 days
            forecast = self._forecast_sentiment(df)
            
            return {
                "trend": trend,
                "volatility": volatility,
                "momentum": momentum,
                "anomalies": anomalies,
                "forecast": forecast,
                "data_points": len(df),
                "trend_strength": self._strength_description(momentum)
            }
        except Exception as e:
            logger.error(f"Trend analysis error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _prepare_data(self, sentiments: List[float], dates: List[str]) -> pd.DataFrame:
        """Prepare data for analysis"""
        df = pd.DataFrame({
            'date': pd.to_datetime(dates, errors='coerce'),
            'sentiment': sentiments
        })
        df = df.dropna()
        df = df.sort_values('date')
        df.set_index('date', inplace=True)
        return df
    
    def _calculate_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall trend direction"""
        if len(df) < 2:
            return {"direction": "unknown", "strength": 0}
        
        # Calculate slope using simple linear regression
        x = np.arange(len(df))
        y = df['sentiment'].values
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]
        
        # Determine direction
        if slope > 0.01:
            direction = "increasing"
        elif slope < -0.01:
            direction = "decreasing"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "slope": round(float(slope), 4),
            "change_per_day": round(slope, 4),
            "start_value": round(float(y[0]), 3),
            "end_value": round(float(y[-1]), 3),
            "total_change": round(float(y[-1] - y[0]), 3)
        }
    
    def _calculate_volatility(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate sentiment volatility"""
        sentiments = df['sentiment'].values
        
        std_dev = np.std(sentiments)
        var = np.var(sentiments)
        cv = std_dev / (np.mean(sentiments) + 1e-6)  # Coefficient of variation
        
        return {
            "std_deviation": round(float(std_dev), 4),
            "variance": round(float(var), 4),
            "coefficient_of_variation": round(float(cv), 4),
            "volatility_level": "high" if std_dev > 0.2 else "medium" if std_dev > 0.1 else "low"
        }
    
    def _calculate_momentum(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate momentum (rate of change)"""
        sentiments = df['sentiment'].values
        
        if len(sentiments) < 2:
            return {"momentum": 0, "trend_strength": "weak"}
        
        # Recent momentum (last 3 points vs first 3 points)
        recent_trend = np.mean(sentiments[-min(3, len(sentiments)):]) - np.mean(sentiments[:min(3, len(sentiments))])
        
        # Calculate rate of change
        changes = np.diff(sentiments)
        avg_change = np.mean(changes)
        
        momentum_score = recent_trend * np.abs(avg_change)
        
        return {
            "momentum": round(float(momentum_score), 4),
            "rate_of_change": round(float(avg_change), 4),
            "trend_strength": "strong" if abs(momentum_score) > 0.1 else "moderate" if abs(momentum_score) > 0.05 else "weak"
        }
    
    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect sentiment anomalies using statistical methods"""
        sentiments = df['sentiment'].values
        
        if len(sentiments) < 3:
            return []
        
        # Calculate z-scores
        mean = np.mean(sentiments)
        std = np.std(sentiments) + 1e-6
        z_scores = np.abs((sentiments - mean) / std)
        
        anomalies = []
        for idx, (date, z_score) in enumerate(zip(df.index, z_scores)):
            if z_score > self.anomaly_threshold:
                anomalies.append({
                    "date": date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date),
                    "value": round(float(sentiments[idx]), 3),
                    "z_score": round(float(z_score), 3),
                    "type": "spike" if sentiments[idx] > mean else "dip",
                    "severity": "high" if z_score > 3 else "medium"
                })
        
        return anomalies[:5]  # Top 5 anomalies
    
    def _forecast_sentiment(self, df: pd.DataFrame, days_ahead: int = 30) -> Dict[str, Any]:
        """Forecast sentiment for next N days"""
        try:
            sentiments = df['sentiment'].values
            
            if len(sentiments) < 3:
                return {"status": "insufficient_data", "forecast": []}
            
            # Simple exponential smoothing
            alpha = 0.3
            forecast_values = []
            last_value = sentiments[-1]
            last_trend = sentiments[-1] - sentiments[-2] if len(sentiments) > 1 else 0
            
            for day in range(1, days_ahead + 1):
                # Linear extrapolation with damping
                forecast = last_value + (last_trend * (1 - (day / days_ahead) * 0.5))
                forecast = np.clip(forecast, -1, 1)  # Keep in reasonable range
                forecast_values.append({
                    "days_ahead": int(day),
                    "predicted_sentiment": round(float(forecast), 3),
                    "confidence": round(1.0 / (1.0 + day * 0.05), 3)  # Confidence decreases over time
                })
            
            # Calculate confidence interval
            std_error = np.std(sentiments) * np.sqrt(1 + 1/len(sentiments))
            
            return {
                "status": "success",
                "forecast": forecast_values[::5],  # Every 5 days for readability
                "next_week_trend": self._get_forecast_trend(forecast_values[:7]),
                "forecast_confidence": round(float(1.0 - std_error), 3)
            }
        except Exception as e:
            logger.error(f"Forecasting error: {str(e)}")
            return {"status": "error", "forecast": []}
    
    def _get_forecast_trend(self, weekly_forecast: List[Dict]) -> str:
        """Determine trend from weekly forecast"""
        if not weekly_forecast or len(weekly_forecast) < 2:
            return "stable"
        
        start = weekly_forecast[0]["predicted_sentiment"]
        end = weekly_forecast[-1]["predicted_sentiment"]
        
        change = end - start
        if change > 0.1:
            return "improving"
        elif change < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _strength_description(self, momentum: Dict[str, Any]) -> str:
        """Convert momentum score to strength description"""
        return momentum.get("trend_strength", "unknown")
    
    def detect_sentiment_spikes(self,
                              sentiments: List[float],
                              threshold_percentage: float = 20.0) -> List[Dict[str, Any]]:
        """
        Detect sudden sentiment changes
        
        Args:
            sentiments: List of sentiment scores
            threshold_percentage: Percentage change threshold
        
        Returns:
            List of spike events
        """
        spikes = []
        
        for i in range(1, len(sentiments)):
            if sentiments[i-1] == 0:
                continue
            
            percent_change = abs((sentiments[i] - sentiments[i-1]) / abs(sentiments[i-1])) * 100
            
            if percent_change >= threshold_percentage:
                spikes.append({
                    "position": i,
                    "from": round(sentiments[i-1], 3),
                    "to": round(sentiments[i], 3),
                    "change_percent": round(percent_change, 2),
                    "direction": "spike_up" if sentiments[i] > sentiments[i-1] else "spike_down",
                    "severity": self._calculate_spike_severity(percent_change)
                })
        
        return sorted(spikes, key=lambda x: x["change_percent"], reverse=True)[:5]
    
    def _calculate_spike_severity(self, percent_change: float) -> str:
        """Calculate severity of sentiment spike"""
        if percent_change >= 50:
            return "critical"
        elif percent_change >= 30:
            return "high"
        elif percent_change >= 20:
            return "medium"
        else:
            return "low"
    
    def compare_product_trends(self,
                             products: Dict[str, List[float]],
                             dates: List[str]) -> Dict[str, Any]:
        """
        Compare sentiment trends across multiple products
        
        Args:
            products: Dictionary of {product_name: [sentiment_values]}
            dates: Common date range
        
        Returns:
            Comparative analysis
        """
        comparison = {}
        
        for product_name, sentiments in products.items():
            df = self._prepare_data(sentiments, dates)
            trend = self._calculate_trend(df)
            volatility = self._calculate_volatility(df)
            
            comparison[product_name] = {
                "trend": trend["direction"],
                "momentum": trend["total_change"],
                "volatility": volatility["volatility_level"],
                "average_sentiment": round(float(df['sentiment'].mean()), 3)
            }
        
        # Find winner/loser
        products_by_momentum = sorted(comparison.items(), 
                                     key=lambda x: x[1]["momentum"], 
                                     reverse=True)
        
        return {
            "comparison": comparison,
            "best_performer": products_by_momentum[0][0] if products_by_momentum else None,
            "worst_performer": products_by_momentum[-1][0] if products_by_momentum else None,
            "most_volatile": max(comparison, key=lambda x: comparison[x]["volatility"]) if comparison else None
        }


# Global instance
_engine = None

def get_trend_engine() -> TrendAnalyticsEngine:
    """Get or create trend analytics engine"""
    global _engine
    if _engine is None:
        _engine = TrendAnalyticsEngine()
    return _engine
