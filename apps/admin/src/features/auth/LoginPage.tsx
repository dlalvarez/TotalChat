import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { FieldWrapper, Input, Select } from '../../components/ui/Form';
import { DEVELOPMENT_TENANTS } from '../../config/tenant';

const schema = z.object({
  email: z.string().email('Ingresa un correo válido'),
  password: z.string().min(6, 'Mínimo 6 caracteres'),
  tenant: z.string().min(1),
});

type LoginForm = z.infer<typeof schema>;

export function LoginPage({ onLogin }: { onLogin: (tenantId: string) => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: { email: 'admin@clinica-demo.test', tenant: DEVELOPMENT_TENANTS[0].id },
  });

  return (
    <main className="grid min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-clinic-600 px-4 py-10 text-slate-900 lg:grid-cols-[1fr_460px]">
      <section className="hidden items-center p-12 text-white lg:flex">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-brand-100">
            TotalChat · MediChat
          </p>
          <h1 className="mt-4 max-w-2xl text-5xl font-bold leading-tight">
            Consola administrativa profesional para reservas médicas.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-brand-50">
            Base visual y UX para gestionar datos operativos sin exponer complejidad técnica ni pedir
            UUIDs a usuarios administrativos.
          </p>
        </div>
      </section>

      <Card className="m-auto w-full max-w-md p-8">
        <h2 className="text-2xl font-bold text-slate-950">Iniciar sesión</h2>
        <p className="mt-2 text-sm text-slate-500">
          Flujo placeholder preparado para email/password, JWT y selector de tenant futuro.
        </p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit((values) => onLogin(values.tenant))}>
          <FieldWrapper label="Correo" error={errors.email?.message}>
            <Input {...register('email')} />
          </FieldWrapper>
          <FieldWrapper label="Contraseña" error={errors.password?.message}>
            <Input type="password" placeholder="••••••••" {...register('password')} />
          </FieldWrapper>
          <FieldWrapper label="Tenant" hint="Selector amigable; el identificador técnico queda interno.">
            <Select {...register('tenant')}>
              {DEVELOPMENT_TENANTS.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.label} · {tenant.environmentNote}
                </option>
              ))}
            </Select>
          </FieldWrapper>
          <Button className="w-full" type="submit">
            Entrar al administrador
          </Button>
        </form>
      </Card>
    </main>
  );
}
