import { useWorkspaceStore } from './store';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');

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
      const errText = await response.text();
      throw new Error(errText || `HTTP error! Status code: ${response.status}`);
    }

    return await response.json();
  } catch (error: any) {
    throw new Error(`API Gateway Connection Error on ${endpoint}: ${error.message}`);
  }
}
