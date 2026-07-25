import { useWorkspaceStore } from './store';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  
  // Set default JSON Content-Type only if body is NOT FormData
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  // Inject authentication state header if token exists in Zustand session store
  const { jwtToken } = useWorkspaceStore.getState();
  if (jwtToken) {
    headers.set('Authorization', `Bearer ${jwtToken}`);
  }

  const cleanBase = API_BASE_URL.replace(/\/$/, '');
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = (cleanBase.endsWith('/api/v1') && cleanEndpoint.startsWith('/api/v1'))
    ? `${cleanBase.replace(/\/api\/v1$/, '')}${cleanEndpoint}`
    : `${cleanBase}${cleanEndpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      let errText = await response.text();
      try {
        const errJson = JSON.parse(errText);
        errText = errJson.detail || errText;
      } catch (e) {
        // use raw text
      }
      throw new Error(errText || `HTTP error! Status code: ${response.status}`);
    }

    return await response.json();
  } catch (error: any) {
    throw new Error(error.message || `API Gateway Connection Error on ${endpoint}`);
  }
}

export async function downloadFileRequest(
  endpoint: string
): Promise<{ blob: Blob; filename: string }> {
  const headers = new Headers();
  const { jwtToken } = useWorkspaceStore.getState();
  if (jwtToken) {
    headers.set('Authorization', `Bearer ${jwtToken}`);
  }

  const cleanBase = API_BASE_URL.replace(/\/$/, '');
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = (cleanBase.endsWith('/api/v1') && cleanEndpoint.startsWith('/api/v1'))
    ? `${cleanBase.replace(/\/api\/v1$/, '')}${cleanEndpoint}`
    : `${cleanBase}${cleanEndpoint}`;

  const response = await fetch(url, { method: 'GET', headers });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || `Failed to download file (Status ${response.status})`);
  }

  const disposition = response.headers.get('Content-Disposition');
  let filename = 'downloaded_template';
  if (disposition && disposition.includes('filename=')) {
    filename = disposition.split('filename=')[1].replace(/["']/g, '');
  }

  const blob = await response.blob();
  return { blob, filename };
}
