# Side Project Research — Emprendimiento SaaS/API

**Fecha**: 2026-03-08
**Objetivo**: Encontrar un side project que genere ingresos extra con proyeccion a sustituir ingreso actual de $3K/mes.

## Perfil del fundador

- Backend developer (FastAPI, SQLAlchemy, PostgreSQL)
- Ubicado en El Salvador (costo de vida bajo = ventaja competitiva)
- Tiempo limitado (side project, no full-time)
- Presupuesto bajo para arrancar (< $100/mes)
- Preferencia por modelo API-as-a-Service / Backend-as-a-Service

## Ideas descartadas

| Idea | Razon de descarte |
|------|-------------------|
| Facturacion electronica SV | Saturado, pagan poco localmente |
| Portal de noticias con IA (competir con Marca/Sport) | SEO toma 6-12 meses, ingresos por ads son bajos, Google penaliza contenido IA |
| SaaS para prestamistas (solo local) | Ciclo de venta largo, clientes informales, churn alto |
| WhatsApp bot para citas | No se extrapola a USA (no usan WhatsApp para el dia a dia) |

## Principios clave identificados

1. **No vender al mercado local unicamente** — apuntar a USA/Europa donde pagan $50-200/mes sin problemas
2. **Ser de El Salvador es ventaja** — costo de vida bajo, conocimiento cultural para mercado hispano en USA
3. **Vertical SaaS > Horizontal** — herramientas para un nicho especifico venden mejor que genericas
4. **Validar antes de construir** — pre-vender a 5 personas antes de escribir codigo
5. **API/Backend puro es el sweet spot** — no requiere frontend complejo, escala bien

## Datos de mercado relevantes

- **AI SaaS market**: $71.54B (2024) -> proyectado $775.44B (2031), CAGR 38.28%
- **Vertical SaaS market**: proyectado $720.44B (2028), CAGR 25.89%
- **Trades/construction USA**: ~$2.1-2.2T anuales, una de las industrias MENOS digitalizadas
- **Negocios hispanos en USA**: 4.7M+, segmento de mas rapido crecimiento (McKinsey)
- **Chatbase (1 persona)**: llego a $8M ARR vendiendo chatbots IA
- **Micro-SaaS sweet spot**: $5K-50K MRR, solo o duo, con < $1K inversion inicial

### Fuentes consultadas
- SignalFire: Vertical AI in Trades and Construction
- a16z: AI Opens New Markets for Vertical SaaS
- Bessemer: The Future of AI is Vertical
- McKinsey: Economic State of Latinos in America
- Indie Hackers: multiples case studies de $22K-64K MRR
- Chatbase/Supabase case study: $1M en 5 meses

## 5 Ideas finalistas (con probabilidad de exito)

### Idea 1: Agente IA para Contratistas/Trades (40-45%)

**Problema**: Sector de trades en USA ($2.1T) es el menos digitalizado. Contratistas pierden clientes por no responder rapido.

**Solucion**: Backend/API que ofrece:
- Agente IA que responde llamadas/SMS de clientes potenciales (ingles + espanol)
- Genera estimados automaticos basados en templates
- Agenda visitas en calendario
- Envia follow-ups automaticos post-servicio

**Stack tecnico**: Twilio (SMS/voz) + LLM API (Claude/GPT) + Calendar API + PDF generation
**Mercado**: USA (trades: plomeros, electricistas, HVAC, landscaping)
**Precio**: $99-299/mes por contratista
**Meta $3K**: 15-30 clientes
**Costo inicial**: ~$50/mes
**Ventaja competitiva**: ServiceTitan (competencia enterprise) cobra $500+/mes y es complejo. Espacio para algo simple y barato. Ser hispano = acceso a 600K+ negocios latinos de trades en USA.

---

### Idea 2: API de Procesamiento de Documentos LATAM (35-40%)

**Problema**: Fintechs y empresas necesitan extraer datos de documentos. Las soluciones existentes (ABBYY, Mindee $0.10/pag) no manejan bien documentos en espanol o formatos latinos.

**Solucion**: API REST que:
- Recibe imagen/PDF de factura, recibo, contrato
- Extrae datos estructurados usando vision models + post-procesamiento
- Retorna JSON limpio
- Especializado en documentos de LATAM (SV, GT, MX, etc.)

**Stack tecnico**: FastAPI + Claude/GPT vision API + validacion de formatos locales
**Mercado**: Fintechs LATAM/USA con operaciones en Latinoamerica
**Precio**: $0.03-0.08/documento o $99-499/mes por volumen
**Meta $3K**: ~50K docs/mes o 10-30 clientes enterprise
**Costo inicial**: ~$30/mes

---

### Idea 3: Backend para Chatbots Verticales con IA (35-40%)

**Problema**: Chatbase llego a $8M ARR con chatbots genericos. Los negocios necesitan chatbots que HAGAN cosas (agendar, cobrar, actualizar pedidos), no solo responder preguntas.

**Solucion**: API/plataforma para crear agentes IA por industria:
- Restaurantes: ordenes, reservaciones, menu
- Clinicas: citas, preguntas frecuentes, cancelaciones
- E-commerce: tracking, devoluciones, recomendaciones

**Stack tecnico**: FastAPI + LLM + integraciones verticales (POS, calendar, e-commerce APIs)
**Mercado**: USA + LATAM, vendido a negocios directos o agencias (whitelabel)
**Precio**: $49-199/mes directo, $299-999/mes agencias
**Meta $3K**: 20-60 clientes directos o 5-10 agencias
**Costo inicial**: ~$20/mes

---

### Idea 4: API Reconciliacion de Pagos para Hispanos en USA (35-40%)

**Problema**: 4.7M negocios hispanos en USA manejan pagos en cash, Zelle, Venmo, tarjeta sin forma de reconciliar. QuickBooks es complicado y en ingles.

**Solucion**: API/servicio que:
- Conecta multiples fuentes de pago (Stripe, Square, Zelle, cash)
- Reconcilia automaticamente
- Reportes en espanol e ingles
- Exporta a QuickBooks/Xero
- Alertas de discrepancias

**Stack tecnico**: FastAPI + APIs de payment processors + logica de reconciliacion
**Mercado**: Negocios hispanos en USA (restaurantes, tiendas, servicios)
**Precio**: $49-149/mes
**Meta $3K**: 25-60 clientes
**Costo inicial**: ~$20/mes

---

### Idea 5: Estimados/Quotes Automatizados con IA para Services (40-45%)

**Problema**: Negocios de servicios (landscaping, limpieza, pintura, mudanzas) pierden tiempo y clientes haciendo cotizaciones manualmente.

**Solucion**: API/app donde:
- Cliente manda fotos + descripcion del trabajo
- IA analiza fotos y descripcion
- Genera estimado profesional en PDF basado en reglas de pricing del negocio
- Envia al cliente automaticamente en minutos
- Cliente acepta y agenda directamente

**Stack tecnico**: FastAPI + Vision API + PDF generation + template engine + scheduling
**Mercado**: USA, service businesses (6M+ negocios, mayoria pequenos)
**Precio**: $79-199/mes + $2-5 por estimado generado
**Meta $3K**: 20-40 clientes
**Costo inicial**: ~$30/mes

---

## Recomendacion final

Las ideas #1 y #5 tienen la probabilidad mas alta (40-45%) y se pueden **combinar** en un solo producto:

> **Un agente IA para contratistas/service businesses que responde leads, genera estimados automaticos con fotos, y agenda trabajos.**

### Por que esta combinacion es la mejor apuesta:
- Mercado mas grande ($2.1T trades) y menos digitalizado
- VCs top (a16z, SignalFire, Bessemer) lo identifican como oportunidad #1
- Ser hispano es ventaja (acceso a 600K+ negocios latinos en USA)
- Es backend-heavy, no necesita frontend complejo
- Dolor cuantificable: "perdi este cliente porque no respondi rapido"
- Competencia enterprise (ServiceTitan $500+/mes) deja espacio para solucion simple y barata

## Descubrimiento clave: contacto directo con contratista

### Contexto

Primo del fundador en **Dallas, Texas** — contratista electricista, dueño de **M-Electric**.
Ya se le han construido 4 proyectos de software como freelance:

| Proyecto | Que hacia | Estado |
|----------|-----------|--------|
| Sitio web | Presencia online de M-Electric | Entregado y en uso |
| Sistema de pedidos/costos | Control de materiales y costos por trabajo | Entregado, **nunca lo uso** |
| Control de permisos de obra | Permisos por estado/ciudad donde labora | Entregado, **nunca lo uso** |
| Tracking de empleados + payroll | GPS via navegador, horas por ubicacion, calculo de pago semanal | Entregado, **nunca lo uso** |

### Analisis: por que esto es una ventaja enorme

El fundador ya supero las etapas mas dificiles sin darse cuenta:
1. **Nicho identificado** — contratistas electricistas en USA
2. **Cliente potencial real** — primo con negocio activo en Dallas
3. **Dolores conocidos** — costos, permisos, payroll, tracking
4. **Confianza ganada** — relacion familiar + historial de trabajo juntos
5. **Conocimiento de la industria** — 4 proyectos construidos para el sector

### Insight critico: 3 de 4 sistemas no fueron adoptados

Esto revela un patron fundamental del mercado de trades:

> Los contratistas SABEN que tienen problemas y QUIEREN soluciones, pero NO ADOPTAN software complejo.

La industria es la menos digitalizada no porque no haya software, sino porque
**el software existente no se adapta a como trabajan ellos** (en la calle, desde el telefono, sin tiempo para meter datos).

### Hipotesis sobre por que no uso los sistemas

| Posible razon | Implicacion para el producto |
|---------------|------------------------------|
| "No tengo tiempo para meterle datos" | Necesita automatizacion — IA que haga el trabajo por el |
| "Es muy complicado" | Necesita algo ultra simple, tipo responder un SMS |
| "Mis empleados no lo usan" | El producto debe estar disenado para los empleados, no solo el dueno |
| "Lo resuelvo con Excel/papel" | La solucion tiene que ser MEJOR que Excel, no solo diferente |
| "Se me olvidaba entrar" | Necesita notificaciones push y automatizacion, no un dashboard |

**PENDIENTE**: Llamar al primo y preguntar directamente la razon real.

### Preguntas clave para validacion (llamada con primo)

1. "¿Por que no usaste los sistemas que te hice?" (sin juzgar, solo escuchar)
2. "¿Que es lo que mas tiempo te quita en el dia a dia?"
3. "¿Como conseguis nuevos clientes? ¿Cuantos leads perdes por no responder rapido?"
4. "¿Cuanto pagas por software al mes? (ServiceTitan, Jobber, Housecall Pro, algo?)"
5. "¿Tenes amigos contratistas que tengan los mismos problemas?"
6. "Si pudieras resolver UN solo problema con tecnologia, ¿cual seria?"
7. "¿Como manejas los estimados/cotizaciones hoy?"

## Proximos pasos

- [ ] **PRIORIDAD 1**: Llamar al primo (M-Electric, Dallas) — entrevista de validacion
- [ ] Entender por que no adopto los 3 sistemas anteriores
- [ ] Identificar el dolor #1 real (no el que asumimos)
- [ ] Definir MVP tecnico minimo basado en la entrevista
- [ ] Construir MVP (2-4 semanas)
- [ ] Validar con primo como primer usuario beta
- [ ] Pedir referidos a otros contratistas en Dallas
- [ ] Escalar a 5-10 clientes pagando
