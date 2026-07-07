# BRAND_AND_PRODUCT_STRATEGY.md
# Estrategia de marca, plataforma y verticales de TotalChat

## 1. Propósito

Este documento define cómo debe manejarse la relación entre **TotalChat** y las soluciones verticales construidas sobre la plataforma.

La decisión principal es que **TotalChat no será tratado únicamente como una app o producto vertical**, sino como una **marca paraguas, plataforma técnica y familia de soluciones conversacionales**.

El primer producto vertical será **MediChat**, enfocado en citas médicas y profesionales de salud.

## 2. Decisión principal

TotalChat será la plataforma paraguas.

Las soluciones verticales oficiales iniciales serán:

```text
TotalChat
├── MediChat   → médicos y profesionales de salud
├── RestoChat  → restaurantes y bares
├── HotelChat  → hoteles
├── StayChat   → Airbnb y otros alojamientos
└── StoreChat  → tiendas, compras y comercio minorista
```

## 3. Definición de TotalChat

TotalChat representa:

- La marca paraguas.
- La plataforma técnica común.
- El framework SaaS multi-tenant.
- La base de conversación, canales, pagos, agenda, usuarios, providers, seguridad y automatizaciones.
- La familia de productos verticales.

TotalChat no debe entenderse como “la app médica”. La app médica es MediChat.

## 4. Definición de TotalChat Platform

**TotalChat Platform** es el conjunto de componentes técnicos compartidos que permiten construir verticales conversacionales.

Incluye:

- Multi-tenancy.
- Auth.
- Usuarios y roles.
- Tenant resolver.
- Canales conversacionales.
- Conversaciones y mensajes.
- LLMProvider.
- EmbeddingsProvider.
- PaymentProvider.
- SchedulingProvider.
- MeetingProvider.
- NotificationProvider.
- Eventos de dominio.
- Auditoría.
- Seguridad.
- Admin shell.
- Configuración base.
- Integraciones externas.
- Infraestructura.
- SDD/spec framework.

## 5. Definición de TotalChat Core

**TotalChat Core** representa capacidades comunes y reutilizables que no pertenecen a un vertical específico.

No debe contener reglas médicas, reglas de restaurantes, reglas hoteleras ni reglas de retail.

Ejemplos permitidos en core:

```text
tenant management
auth
roles
conversation sessions
messages
channel abstraction
LLM provider abstraction
payment provider abstraction
scheduling provider abstraction
meeting provider abstraction
audit
events
settings
logging
errors
security helpers
```

Ejemplos que NO deben ir en core:

```text
patients
medical specialties
practitioners as medical doctors
payer plans specific to healthcare
restaurant tables
hotel rooms as inventory
retail carts
```

Esos conceptos deben vivir en sus soluciones verticales.

## 6. Verticales oficiales

## 6.1. MediChat

Vertical para médicos y profesionales de salud.

### Propósito

Permitir a pacientes reservar citas médicas, psicológicas, odontológicas, terapéuticas o de otros profesionales de salud mediante conversación.

### Dominio específico

MediChat puede incluir:

- Pacientes.
- Profesionales de salud.
- Especialidades.
- Servicios del profesional.
- Modalidades de atención.
- Citas presenciales.
- Citas virtuales.
- Pagadores.
- Planes.
- Pólizas.
- Medicina prepagada.
- EPS.
- Tarifas por plan.
- Transferencias con revisión manual.
- Confirmación de asistencia.
- Integración Docplanner como proveedor externo.
- Restricción explícita de no diagnóstico médico.

### Regla

MediChat no debe contaminar TotalChat Core con conceptos médicos.

## 6.2. RestoChat

Vertical para restaurantes y bares.

### Propósito

Permitir reservas conversacionales en restaurantes, bares, cafés, gastrobares u otros negocios de comida y bebida.

### Dominio futuro posible

RestoChat puede incluir:

- Mesas.
- Zonas.
- Salones.
- Número de personas.
- Turnos.
- Tiempo máximo de ocupación.
- Lista de espera.
- Preferencias.
- Ocasiones especiales.
- Reservas para eventos.
- Depósitos.
- Políticas de cancelación.
- Confirmación de asistencia.
- Menú.
- Pedidos futuros.
- Integraciones POS futuras.

### Regla

RestoChat no debe reutilizar conceptos médicos como pacientes, EPS, pólizas o especialidades médicas.

## 6.3. HotelChat

Vertical para hoteles.

### Propósito

Permitir reservas conversacionales para hoteles tradicionales.

### Dominio futuro posible

HotelChat puede incluir:

- Habitaciones.
- Tipos de habitación.
- Tarifas por noche.
- Ocupación.
- Check-in.
- Check-out.
- Temporadas.
- Disponibilidad por rango de fechas.
- Políticas de cancelación.
- Pagos parciales.
- Confirmaciones.
- Integraciones PMS.
- Channel managers.

### Regla

HotelChat maneja inventario por noche/rango de fechas, por lo que no debe asumirse que usa el mismo modelo de slots horarios de MediChat.

## 6.4. StayChat

Vertical para Airbnb y otros alojamientos.

### Propósito

Permitir reservas conversacionales para alojamientos no necesariamente hoteleros.

### Dominio futuro posible

StayChat puede incluir:

- Apartamentos.
- Casas.
- Fincas.
- Cabañas.
- Hostales.
- Glamping.
- Estadías por noche.
- Limpieza.
- Depósitos.
- Reglas de casa.
- Check-in autónomo.
- Huéspedes.
- Integraciones con plataformas externas.

### Regla

StayChat puede compartir conceptos con HotelChat, pero no debe forzarse a ser igual. Airbnb y alojamientos particulares suelen tener reglas distintas a hoteles.

## 6.5. StoreChat

Vertical para tiendas, compras y comercio minorista.

### Propósito

Permitir atención conversacional para tiendas y comercio minorista.

### Dominio futuro posible

StoreChat puede incluir:

- Catálogo de productos.
- Categorías.
- Inventario.
- Carrito.
- Pedidos.
- Entregas.
- Recogida en tienda.
- Pagos.
- Promociones.
- Clientes.
- Conversación de venta.
- Integraciones e-commerce.
- Integraciones POS.

### Regla

StoreChat no debe mezclarse con reservas médicas ni agenda por defecto. Puede usar pagos, canales, conversación y notificaciones del core, pero su dominio principal es venta/pedido/inventario.

## 7. Naming oficial

## 7.1. Marca paraguas

```text
TotalChat
```

## 7.2. Plataforma técnica

```text
TotalChat Platform
```

## 7.3. Core compartido

```text
TotalChat Core
```

## 7.4. Soluciones verticales

```text
MediChat
RestoChat
HotelChat
StayChat
StoreChat
```

## 7.5. Códigos internos de solución

Para carpetas, slugs, paquetes, specs y configuración, usar minúsculas:

```text
medichat
restochat
hotelchat
staychat
storechat
```

## 8. Reglas de comunicación comercial

### 8.1. Cuando se hable de la familia

Usar:

```text
TotalChat
```

Ejemplo:

> TotalChat es una plataforma conversacional multi-solución para reservas, atención y comercio.

### 8.2. Cuando se hable de salud

Usar:

```text
MediChat
```

Ejemplo:

> MediChat permite a médicos y profesionales de salud gestionar citas conversacionales con pagos, recordatorios y agenda.

### 8.3. Cuando se hable de restaurantes

Usar:

```text
RestoChat
```

Ejemplo:

> RestoChat permite a restaurantes y bares gestionar reservas, confirmaciones y lista de espera por canales conversacionales.

### 8.4. Cuando se hable de hoteles

Usar:

```text
HotelChat
```

### 8.5. Cuando se hable de Airbnb/alojamientos

Usar:

```text
StayChat
```

### 8.6. Cuando se hable de tiendas

Usar:

```text
StoreChat
```

## 9. Reglas para documentación

Los documentos generales deben decir:

```text
TotalChat Platform
```

cuando hablen de capacidades comunes.

Los documentos del vertical médico deben decir:

```text
MediChat
```

cuando hablen de pacientes, profesionales de salud, especialidades, pólizas, prepagada, EPS, citas médicas o Docplanner.

## 10. Regla anti-contaminación de dominio

El dominio de MediChat no debe invadir TotalChat Core.

Ejemplos incorrectos:

```text
packages/core/patients.py
packages/core/medical_specialties.py
packages/core/eps.py
```

Ejemplos correctos:

```text
solutions/medichat/domain/patients.py
solutions/medichat/domain/specialties.py
solutions/medichat/domain/payers.py
```

## 11. Regla para Codex

Codex debe respetar esta separación:

```text
core = reusable platform capabilities
solutions/medichat = healthcare domain
solutions/restochat = restaurant domain
solutions/hotelchat = hotel domain
solutions/staychat = accommodation domain
solutions/storechat = retail domain
```

Codex no debe implementar lógica médica en paquetes compartidos salvo abstracciones genéricas.
