const API_BASE_URL =
  import.meta.env.VITE_TOTALCHAT_API_BASE_URL?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000';

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

type ApiOptions = RequestInit & {
  tenantId?: string;
  accessToken?: string | null;
  skipAuth?: boolean;
  skipTenant?: boolean;
};

type ApiEnvelope<T> = { data: T };

function getFriendlyErrorMessage(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== 'object') return fallback;

  if ('error' in payload) {
    const error = (payload as { error?: unknown }).error;
    if (error && typeof error === 'object' && 'message' in error) {
      return String((error as { message?: unknown }).message);
    }
  }

  if ('detail' in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return String((detail as { message?: unknown }).message);
    }
    if (typeof detail === 'string') return detail;
  }

  return fallback;
}

export async function apiRequest<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { tenantId, accessToken, skipAuth = false, skipTenant = false, headers, body, ...init } = options;
  const storedToken = typeof window !== 'undefined' ? window.localStorage.getItem('totalchat_admin_access_token') : null;
  const bearerToken = accessToken ?? storedToken;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    body,
    headers: {
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(!skipAuth && bearerToken ? { Authorization: `Bearer ${bearerToken}` } : {}),
      ...(!skipTenant && tenantId ? { 'X-TotalChat-Tenant-Id': tenantId } : {}),
      ...headers,
    },
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await response.json().catch(() => undefined) : undefined;

  if (!response.ok) {
    throw new ApiError(
      getFriendlyErrorMessage(payload, 'No pudimos completar la solicitud. Intenta nuevamente.'),
      response.status,
      payload,
    );
  }

  return (payload as ApiEnvelope<T>).data;
}
