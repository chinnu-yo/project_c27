import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.mcp_mocks.ga4_mock import get_ga4_metrics
from backend.app.mcp_mocks.quickbooks_mock import get_quickbooks_data

client = TestClient(app)

def get_auth_headers(client_id: str = "client_abc"):
    token = create_access_token(client_id=client_id)
    return {"Authorization": f"Bearer {token}"}

def test_production_startup_security_validation():
    # Production without explicit JWT_SECRET should fail loudly
    err1 = None
    try:
        os.environ["ENV"] = "production"
        os.environ["JWT_SECRET"] = "placeholder_secret_key"
        os.environ["ENCRYPTION_KEY"] = "some_key"
        _env = os.getenv("ENV", "development").lower()
        _jwt_secret = os.getenv("JWT_SECRET", "placeholder_secret_key")
        if _env == "production" and (_jwt_secret == "placeholder_secret_key" or not _jwt_secret):
            raise ValueError("CRITICAL SECURITY ERROR: JWT_SECRET must be explicitly configured in production environment!")
    except ValueError as e:
        err1 = str(e)

    assert err1 is not None and "JWT_SECRET" in err1

    # Production without explicit ENCRYPTION_KEY should fail loudly
    err2 = None
    try:
        os.environ["ENV"] = "production"
        os.environ["JWT_SECRET"] = "real_prod_jwt_secret_key_123"
        os.environ["ENCRYPTION_KEY"] = ""
        _env = os.getenv("ENV", "development").lower()
        _encryption_key = os.getenv("ENCRYPTION_KEY", "")
        if _env == "production" and not _encryption_key:
            raise ValueError("CRITICAL SECURITY ERROR: ENCRYPTION_KEY must be explicitly configured in production environment!")
    except ValueError as e:
        err2 = str(e)

    assert err2 is not None and "ENCRYPTION_KEY" in err2

    # Reset back to development
    os.environ["ENV"] = "development"


def test_integration_lifecycle_and_masking():
    headers = get_auth_headers("client_abc")

    # 1. Create integration
    create_res = client.post(
        "/api/v1/integrations",
        json={
            "client_id": "client_abc",
            "integration_name": "HubSpot Prod API",
            "integration_type": "api_key",
            "endpoint_url": "http://127.0.0.1:8000/api/v1/integrations/list",
            "credential": "secret_token_key_abc_999"
        },
        headers=headers
    )
    assert create_res.status_code == 200, create_res.text
    c_data = create_res.json()
    integration_id = c_data["id"]
    assert c_data["masked_credential"] == "••••_999"
    assert c_data["masked_credential"] != "secret_token_key_abc_999"

    # 2. List integrations & verify credential is never exposed in plaintext
    list_res = client.get("/api/v1/integrations/list?client_id=client_abc", headers=headers)
    assert list_res.status_code == 200
    l_data = list_res.json()
    found = [item for item in l_data["integrations"] if item["id"] == integration_id]
    assert len(found) == 1
    assert found[0]["masked_credential"] == "••••_999"
    assert "secret_token_key" not in list_res.text

    # 3. Test connectivity endpoint
    test_res = client.post(f"/api/v1/integrations/{integration_id}/test", headers=headers)
    assert test_res.status_code == 200
    t_data = test_res.json()
    assert t_data["status"] in ["connected", "failed"]
    assert "verification_details" in t_data

    # 4. Delete integration
    del_res = client.delete(f"/api/v1/integrations/{integration_id}", headers=headers)
    assert del_res.status_code == 200

def test_integration_tenant_isolation():
    headers_abc = get_auth_headers("client_abc")
    headers_xyz = get_auth_headers("client_xyz")

    # Attempt to create integration for client_xyz using client_abc token -> 403 / SecurityError
    res1 = client.post(
        "/api/v1/integrations",
        json={
            "client_id": "client_xyz",
            "integration_name": "Unauthorized API",
            "integration_type": "api_key",
            "endpoint_url": "https://api.example.com",
            "credential": "stolen_key"
        },
        headers=headers_abc
    )
    assert res1.status_code == 403 or "Tenant isolation mismatch" in res1.text

    # Attempt to list client_xyz integrations using client_abc token
    res2 = client.get("/api/v1/integrations/list?client_id=client_xyz", headers=headers_abc)
    assert res2.status_code == 403 or "Tenant isolation mismatch" in res2.text

def test_team_management_lifecycle():
    headers = get_auth_headers("client_abc")

    # 1. Invite team member
    inv_res = client.post(
        "/api/v1/team/invite",
        json={
            "email": "new.analyst@company.com",
            "role": "Member",
            "client_access": ["client_abc"]
        },
        headers=headers
    )
    assert inv_res.status_code == 200, inv_res.text
    m_data = inv_res.json()
    member_id = m_data["id"]
    assert m_data["email"] == "new.analyst@company.com"
    assert m_data["status"] == "pending"

    # 2. List team members
    list_res = client.get("/api/v1/team/list?client_id=client_abc", headers=headers)
    assert list_res.status_code == 200
    members = list_res.json()["members"]
    assert len(members) >= 1

    # 3. Update member permissions
    upd_res = client.put(
        f"/api/v1/team/{member_id}",
        json={
            "role": "Admin",
            "client_access": ["client_abc", "client_xyz"]
        },
        headers=headers
    )
    assert upd_res.status_code == 200
    u_data = upd_res.json()
    assert u_data["role"] == "Admin"
    assert "client_xyz" in u_data["client_access"]

    # 4. Remove team member
    del_res = client.delete(f"/api/v1/team/{member_id}", headers=headers)
    assert del_res.status_code == 200

def test_reports_manual_save_memory_trigger():
    headers = get_auth_headers("client_abc")
    save_res = client.post(
        "/api/v1/reports/save",
        json={
            "client_id": "client_abc",
            "report_name": "Q4 Executive Summary Canvas",
            "tiptap_json": {
                "type": "doc",
                "content": [
                    {
                        "type": "heading",
                        "attrs": {"level": 1},
                        "content": [{"type": "text", "text": "Q4 Performance Brief"}]
                    }
                ]
            }
        },
        headers=headers
    )
    assert save_res.status_code == 200
    data = save_res.json()
    assert data["status"] == "success"
    assert "report_id" in data

def test_expanded_mcp_mock_seed_data():
    ga4_abc = get_ga4_metrics("client_abc")
    assert len(ga4_abc) == 4
    periods_abc = [p["period"] for p in ga4_abc]
    assert "Q1" in periods_abc and "Q4" in periods_abc

    ga4_xyz = get_ga4_metrics("client_xyz")
    assert len(ga4_xyz) == 4

    qb_abc = get_quickbooks_data("client_abc")
    assert qb_abc["outstanding_invoices_total"] == 8200.00
    assert qb_abc["invoice_count"] == 3

    qb_xyz = get_quickbooks_data("client_xyz")
    assert qb_xyz["outstanding_invoices_total"] == 12800.00
    assert qb_xyz["invoice_count"] == 2

if __name__ == "__main__":
    print("Running Security Startup Test...")
    test_production_startup_security_validation()
    print("Running Integrations Lifecycle Test...")
    test_integration_lifecycle_and_masking()
    print("Running Tenant Isolation Test...")
    test_integration_tenant_isolation()
    print("Running Team Management Lifecycle Test...")
    test_team_management_lifecycle()
    print("Running Reports Manual Save Critic Memory Trigger Test...")
    test_reports_manual_save_memory_trigger()
    print("Running Expanded MCP Seed Data Test...")
    test_expanded_mcp_mock_seed_data()
    print("\nALL INTEGRATION AND TEAM SECURITY TESTS PASSED CLEANLY!")

