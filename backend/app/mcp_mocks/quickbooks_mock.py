from typing import Dict, Any, List
from backend.app.core.exceptions import ValidationError

# Static mock transactional records sandbox
QUICKBOOKS_DATABASE: Dict[str, Dict[str, Any]] = {
    "client_abc": {
        "outstanding_invoices_total": 8200.00,
        "invoice_count": 3,
        "quarterly_totals": {
            "Q1": 3100.00,
            "Q2": 5400.00,
            "Q3": 4500.00,
            "Q4": 8200.00
        },
        "invoices": [
            {"invoice_id": "inv_1023", "amount": 3200.00, "status": "unpaid", "quarter": "Q4", "due_date": "2026-08-01"},
            {"invoice_id": "inv_1024", "amount": 2800.00, "status": "unpaid", "quarter": "Q4", "due_date": "2026-08-15"},
            {"invoice_id": "inv_1025", "amount": 2200.00, "status": "unpaid", "quarter": "Q4", "due_date": "2026-08-30"}
        ],
        "currency": "USD"
    },
    "client_xyz": {
        "outstanding_invoices_total": 12800.00,
        "invoice_count": 2,
        "quarterly_totals": {
            "Q1": 18500.00,
            "Q2": 15200.00,
            "Q3": 12500.00,
            "Q4": 12800.00
        },
        "invoices": [
            {"invoice_id": "inv_9088", "amount": 7800.00, "status": "unpaid", "quarter": "Q4", "due_date": "2026-08-10"},
            {"invoice_id": "inv_9089", "amount": 5000.00, "status": "unpaid", "quarter": "Q4", "due_date": "2026-08-25"}
        ],
        "currency": "USD"
    }
}

def get_quickbooks_data(client_id: str) -> Dict[str, Any]:
    """Retrieves QuickBooks mock billing/invoice data, enforcing client_id bounds."""
    if not client_id:
        raise ValidationError("client_id parameter is required for QuickBooks lookup.")
    return QUICKBOOKS_DATABASE.get(client_id, {
        "outstanding_invoices_total": 0.0,
        "invoice_count": 0,
        "invoices": [],
        "currency": "USD"
    })
