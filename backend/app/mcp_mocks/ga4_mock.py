from typing import Dict, Any, List
from backend.app.core.exceptions import ValidationError

# Static mock analytical records sandbox
GA4_DATABASE: Dict[str, List[Dict[str, Any]]] = {
    "client_abc": [
        {"period": "Q4", "sessions": 12400, "pageviews": 31000, "bounce_rate": 0.39, "traffic_source": "Organic Search"},
        {"period": "Q3", "sessions": 10000, "pageviews": 25000, "bounce_rate": 0.42, "traffic_source": "Organic Search"},
        {"period": "Q2", "sessions": 8500, "pageviews": 21000, "bounce_rate": 0.45, "traffic_source": "Social Media"},
        {"period": "Q1", "sessions": 7200, "pageviews": 18500, "bounce_rate": 0.48, "traffic_source": "Email Campaigns"},
    ],
    "client_xyz": [
        {"period": "Q4", "sessions": 52000, "pageviews": 128000, "bounce_rate": 0.35, "traffic_source": "Direct"},
        {"period": "Q3", "sessions": 45000, "pageviews": 110000, "bounce_rate": 0.38, "traffic_source": "Direct"},
        {"period": "Q2", "sessions": 39800, "pageviews": 96500, "bounce_rate": 0.41, "traffic_source": "Paid Search"},
        {"period": "Q1", "sessions": 33500, "pageviews": 82000, "bounce_rate": 0.44, "traffic_source": "Referrals"},
    ]
}

def get_ga4_metrics(client_id: str) -> List[Dict[str, Any]]:
    """Retrieves Google Analytics mock traffic data, enforcing client_id bounds."""
    if not client_id:
        raise ValidationError("client_id parameter is required for GA4 lookup.")
    return GA4_DATABASE.get(client_id, [])
