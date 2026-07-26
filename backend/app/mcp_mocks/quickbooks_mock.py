from typing import Dict, Any, List
from backend.app.core.exceptions import ValidationError

# Static mock transactional records sandbox
QUICKBOOKS_DATABASE: Dict[str, Dict[str, Any]] = {
    "client_abc": {
        "outstanding_invoices_total": 8800.00,
        "invoice_count": 6,
        "invoices": [
            {"invoice_id": "inv_1021", "amount": 2500.00, "status": "Unpaid", "due_date": "2026-08-01", "period": "Q3"},
            {"invoice_id": "inv_1022", "amount": 2000.00, "status": "Unpaid", "due_date": "2026-08-15", "period": "Q3"},
            {"invoice_id": "inv_1023", "amount": 1200.00, "status": "Overdue", "due_date": "2026-04-10", "period": "Q1"},
            {"invoice_id": "inv_1024", "amount": 4500.00, "status": "Paid", "due_date": "2026-05-20", "period": "Q2"},
            {"invoice_id": "inv_1025", "amount": 12800.00, "status": "Paid", "due_date": "2026-02-28", "period": "Q1"},
            {"invoice_id": "inv_1026", "amount": 3100.00, "status": "Overdue", "due_date": "2026-07-01", "period": "Q2"}
        ],
        "currency": "USD"
    },
    "client_xyz": {
        "outstanding_invoices_total": 33800.00,
        "invoice_count": 6,
        "invoices": [
            {"invoice_id": "inv_9088", "amount": 12500.00, "status": "Unpaid", "due_date": "2026-08-10", "period": "Q3"},
            {"invoice_id": "inv_9089", "amount": 4500.00, "status": "Paid", "due_date": "2026-03-15", "period": "Q1"},
            {"invoice_id": "inv_9090", "amount": 12800.00, "status": "Unpaid", "due_date": "2026-09-01", "period": "Q3"},
            {"invoice_id": "inv_9091", "amount": 1200.00, "status": "Paid", "due_date": "2026-06-30", "period": "Q2"},
            {"invoice_id": "inv_9092", "amount": 8500.00, "status": "Overdue", "due_date": "2026-05-01", "period": "Q2"},
            {"invoice_id": "inv_9093", "amount": 19500.00, "status": "Paid", "due_date": "2026-01-20", "period": "Q1"}
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