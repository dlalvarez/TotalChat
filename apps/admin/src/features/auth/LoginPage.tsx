import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { login, getMe, type AuthUser } from '../../api/auth';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { FieldWrapper, Input } from '../../components/ui/Form';

const schema = z.object({
  email: z.string().email('Ingresa un correo válido'),
  password: z.string().min(1, 'Ingresa tu contraseña'),
});

type LoginForm = z.infer<typeof schema>;

export function LoginPage({ onLogin }: { onLogin: (token: string, user: AuthUser) => void }) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: { email: 'admin@clinica-demo.com' },
  });

  async function submit(values: LoginForm) {
    setError(null);
    setLoading(true);
    try {
      const session = await login(values.email, values.password);
      window.localStorage.setItem('totalchat_admin_access_token', session.access_token);
      const user = await getMe(session.access_token);
      onLogin(session.access_token, user);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No pudimos iniciar sesión.');
      window.localStorage.removeItem('totalchat_admin_access_token');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-clinic-600 px-4 py-10 text-slate-900 lg:grid-cols-[1fr_460px]">
      <section className="hidden items-center p-12 text-white lg:flex">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-brand-100">TotalChat · MediChat</p>
          <h1 className="mt-4 max-w-2xl text-5xl font-bold leading-tight">Consola administrativa profesional para reservas médicas.</h1>
          <p className="mt-5 max-w-xl text-lg text-brand-50">Ingresa con tu usuario administrativo. Los tenants disponibles se cargan desde tu sesión, sin exponer schemas internos.</p>
        </div>
      </section>

      <Card className="m-auto w-full max-w-md p-8">
        <h2 className="text-2xl font-bold text-slate-950">Iniciar sesión</h2>
        <p className="mt-2 text-sm text-slate-500">Usa email y contraseña del usuario creado por CLI operativo.</p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit(submit)}>
          <FieldWrapper label="Correo" error={errors.email?.message}><Input {...register('email')} /></FieldWrapper>
          <FieldWrapper label="Contraseña" error={errors.password?.message}><Input type="password" placeholder="••••••••" {...register('password')} /></FieldWrapper>
          {error ? <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button className="w-full" type="submit" disabled={loading}>{loading ? 'Validando…' : 'Entrar al administrador'}</Button>
        </form>
      </Card>
    </main>
  );
}
