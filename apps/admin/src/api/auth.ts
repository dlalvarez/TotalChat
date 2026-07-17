import { apiRequest } from './client';

export type AuthTenant = {
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
  role: string;
};

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  tenants: AuthTenant[];
};

export type LoginResponse = {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
};

export function login(email: string, password: string) {
  return apiRequest<LoginResponse>('/api/auth/login', {
    method: 'POST',
    skipAuth: true,
    skipTenant: true,
    body: JSON.stringify({ email, password }),
  });
}

export function getMe(token: string) {
  return apiRequest<AuthUser>('/api/auth/me', {
    skipTenant: true,
    headers: { Authorization: `Bearer ${token}` },
  });
}
