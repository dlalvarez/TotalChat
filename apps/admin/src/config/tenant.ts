export type AdminTenant = {
  id: string;
  label: string;
  environmentNote: string;
};

// Development-only fixture used until real admin auth/JWT and tenant membership exist.
export const DEVELOPMENT_TENANTS: AdminTenant[] = [
  {
    id: '9bbfb0cd-df8f-4a7c-a60c-5c1232a74d2c',
    label: 'Clínica demo',
    environmentNote: 'Tenant local de integración',
  },
];

export const DEFAULT_DEVELOPMENT_TENANT = DEVELOPMENT_TENANTS[0];
