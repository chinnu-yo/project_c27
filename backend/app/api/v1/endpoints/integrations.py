import time
import uuid
import socket
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, Depends
from cryptography.fernet import Fernet

from backend.app.core.config import settings
from backend.app.core.exceptions import ValidationError, SecurityError
from backend.app.api.dependencies import get_sqlite_service, get_current_client_id, verify_admin_role
from backend.app.services.sqlite_service import SQLiteService
from backend.app.schemas.integrations_schemas import (
    CreateIntegrationRequestModel,
    IntegrationResponseModel,
    IntegrationsListResponseModel,
    TestIntegrationResponseModel
)

router = APIRouter()

def get_fernet() -> Fernet:
    dev_key = b"uP9Q-nK8m1J4v7x2z5A8b3C6d9E2f5G8h1I4j7K0l3M="
    key = settings.encryption_key.encode() if settings.encryption_key else dev_key
    try:
        return Fernet(key)
    except Exception:
        # Fallback to dev key if invalid format in dev
        return Fernet(dev_key)

def encrypt_credential(plain: str) -> str:
    f = get_fernet()
    return f.encrypt(plain.encode('utf-8')).decode('utf-8')

def decrypt_credential(cipher: str) -> str:
    f = get_fernet()
    return f.decrypt(cipher.encode('utf-8')).decode('utf-8')

def mask_credential(secret: str) -> str:
    if not secret:
        return "••••"
    if len(secret) <= 4:
        return "••••"
    return f"••••{secret[-4:]}"

@router.post("/integrations", response_model=IntegrationResponseModel)
async def create_integration(
    payload: CreateIntegrationRequestModel,
    admin_claims: dict = Depends(verify_admin_role),
    auth_client_id: str = Depends(get_current_client_id),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Creates or updates a client integration with Fernet-encrypted secret credentials (Admin-only)."""
    if payload.client_id != auth_client_id:
        raise SecurityError("Tenant isolation mismatch: Cannot configure integrations for another client_id.")

    integration_id = f"integ_{uuid.uuid4().hex[:10]}"
    encrypted_cred = encrypt_credential(payload.credential)
    created_at = int(time.time())

    created = sqlite.create_integration(
        integration_id=integration_id,
        client_id=payload.client_id,
        integration_name=payload.integration_name,
        integration_type=payload.integration_type,
        endpoint_url=payload.endpoint_url,
        encrypted_credential=encrypted_cred,
        created_at=created_at
    )

    return IntegrationResponseModel(
        id=created["id"],
        client_id=created["client_id"],
        integration_name=created["integration_name"],
        integration_type=created["integration_type"],
        endpoint_url=created["endpoint_url"],
        masked_credential=mask_credential(payload.credential),
        created_at=created["created_at"],
        last_tested_at=created.get("last_tested_at"),
        last_test_status=created.get("last_test_status", "Connected")
    )

@router.get("/integrations/list", response_model=IntegrationsListResponseModel)
async def list_integrations(
    client_id: str,
    auth_client_id: str = Depends(get_current_client_id),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Lists integrations for a given client_id with masked credential placeholders."""
    if client_id != auth_client_id:
        raise SecurityError("Tenant isolation mismatch: Cannot view integrations for another client_id.")

    records = sqlite.get_integrations(client_id)
    items = []
    for r in records:
        masked = "••••"
        try:
            decrypted = decrypt_credential(r["encrypted_credential"])
            masked = mask_credential(decrypted)
        except Exception:
            masked = "••••"

        items.append(IntegrationResponseModel(
            id=r["id"],
            client_id=r["client_id"],
            integration_name=r["integration_name"],
            integration_type=r["integration_type"],
            endpoint_url=r["endpoint_url"],
            masked_credential=masked,
            created_at=r["created_at"],
            last_tested_at=r.get("last_tested_at"),
            last_test_status=r.get("last_test_status", "Not Configured")
        ))

    return IntegrationsListResponseModel(
        status="success",
        client_id=client_id,
        integrations=items
    )

@router.post("/integrations/{integration_id}/test", response_model=TestIntegrationResponseModel)
async def test_integration_connection(
    integration_id: str,
    auth_client_id: str = Depends(get_current_client_id),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Executes a real connectivity check against the integration endpoint URL."""
    record = sqlite.get_integration_by_id(integration_id, auth_client_id)
    if not record:
        raise ValidationError(f"Integration with ID '{integration_id}' not found for tenant '{auth_client_id}'.")

    endpoint_url = record["endpoint_url"]
    tested_at = int(time.time())

    try:
        decrypted_cred = decrypt_credential(record["encrypted_credential"])
    except Exception as e:
        sqlite.update_integration_test_status(integration_id, auth_client_id, "Failed", tested_at)
        return TestIntegrationResponseModel(
            status="failed",
            message="Decryption failure for stored credentials",
            verification_details=f"Failed to decrypt stored credential: {str(e)}",
            last_tested_at=tested_at
        )

    parsed = urlparse(endpoint_url)
    scheme = (parsed.scheme or "").lower()

    is_success = False
    details = ""
    err_msg = ""

    if scheme in ["http", "https"]:
        headers = {}
        if record["integration_type"].lower() == "api_key":
            headers["Authorization"] = f"Bearer {decrypted_cred}"

        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                res = await client.get(endpoint_url, headers=headers)
                # Any non-5xx response indicates server reachability
                if res.status_code < 500:
                    is_success = True
                    details = f"Verified HTTP GET reachability to {endpoint_url} (HTTP {res.status_code} {res.reason_phrase}). Credential sent in Authorization header."
                else:
                    details = f"Server responded with HTTP {res.status_code} server error."
                    err_msg = f"HTTP {res.status_code} server error"
        except Exception as ex:
            details = f"HTTP request failed: {str(ex)}"
            err_msg = str(ex)
    else:
        # DB connection string or socket endpoint (e.g. postgresql://host:port or host:port)
        host = parsed.hostname or endpoint_url.split(":")[0].replace("/", "")
        port = parsed.port or 5432
        try:
            sock = socket.create_connection((host, port), timeout=4.0)
            sock.close()
            is_success = True
            details = f"Verified TCP connection reachability to {host}:{port} over socket."
        except Exception as ex:
            details = f"TCP connection check to {host}:{port} failed: {str(ex)}"
            err_msg = str(ex)

    status_str = "Connected" if is_success else "Failed"
    sqlite.update_integration_test_status(integration_id, auth_client_id, status_str, tested_at)

    return TestIntegrationResponseModel(
        status="connected" if is_success else "failed",
        message=f"Integration test {status_str.lower()}",
        verification_details=details,
        last_tested_at=tested_at
    )

@router.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: str,
    admin_claims: dict = Depends(verify_admin_role),
    auth_client_id: str = Depends(get_current_client_id),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Deletes an integration configuration record for the authenticated tenant (Admin-only)."""
    deleted = sqlite.delete_integration(integration_id, auth_client_id)
    if not deleted:
        raise ValidationError(f"Integration with ID '{integration_id}' not found or already removed.")

    return {"status": "success", "message": f"Integration '{integration_id}' successfully deleted."}
