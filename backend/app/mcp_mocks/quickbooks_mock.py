from typing import Dict, Any, List
from backend.app.core.exceptions import ValidationError

# Static mock transactional records sandbox
QUICKBOOKS_DATABASE: Dict[str, Dict[str, Any]] = {
    "client_abc": {
        "outstanding_invoices_total": 4500.00,
        "invoice_count": 2,
        "invoices": [
            {"invoice_id": "inv_1021", "amount": 2500.00, "status": "unpaid", "due_date": "2026-08-01"},
            {"invoice_id": "inv_1022", "amount": 2000.00, "status": "unpaid", "due_date": "2026-08-15"}
        ],
        "currency": "USD"
    },
    "client_xyz": {
        "outstanding_invoices_total": 12500.00,
        "invoice_count": 1,
        "invoices": [
            {"invoice_id": "inv_9088", "amount": 12500.00, "status": "unpaid", "due_date": "2026-08-10"}
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
