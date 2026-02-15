# Modulos del Sistema — Back Office MLM Ganoherb

> Documento complementario al [Plan Maestro](plan.md). Detalle funcional de cada modulo del sistema.

---

## Roles y Usuarios del Sistema

| Rol | Descripcion |
|-----|-------------|
| **Super Administrador** | Control total del sistema. Configuracion global. |
| **Administrador** | Gestion operativa: usuarios, comisiones, productos, reportes. |
| **Gerente de Operaciones** | Supervision de la red, aprobacion de liquidaciones, reportes ejecutivos. |
| **Soporte / Atencion al Cliente** | Gestion de tickets, consultas de afiliados, ajustes manuales limitados. |
| **Afiliado / Distribuidor** | Acceso a su oficina virtual: genealogia, comisiones, pedidos, perfil. |
| **Bodega / Almacen** | Gestion de inventario, despacho de pedidos. |
| **Contabilidad / Finanzas** | Reportes financieros, conciliaciones, facturacion. |

---

## Tabla de Contenido

1. [Usuarios y Afiliados](#1-usuarios-y-afiliados)
2. [Genealogia (Arbol de Red)](#2-genealogia-arbol-de-red)
3. [Productos y Catalogo](#3-productos-y-catalogo)
4. [Pedidos y Ventas](#4-pedidos-y-ventas)
5. [Comisiones y Liquidacion](#5-comisiones-y-liquidacion)
6. [Inventario](#6-inventario)
7. [Reportes y Dashboard](#7-reportes-y-dashboard)
8. [Administracion del Sistema](#8-administracion-del-sistema)
9. [Comunicaciones y Notificaciones](#9-comunicaciones-y-notificaciones)
10. [Facturacion e Integraciones Fiscales](#10-facturacion-e-integraciones-fiscales)
11. [Pagos y Billetera Virtual](#11-pagos-y-billetera-virtual)
12. [Eventos y Capacitaciones](#12-eventos-y-capacitaciones)
13. [Normativas y Compliance](#13-normativas-y-compliance)

---

## 1. Usuarios y Afiliados

### 1.1 Registro e Inscripcion

- Formulario de inscripcion con datos personales, fiscales y de contacto.
- Asignacion de **ID unico** de afiliado (codigo alfanumerico o numerico secuencial).
- Seleccion de **kit de inscripcion** (obligatorio para activar la membresia).
- Vinculacion con **patrocinador** (por codigo o link de referido).
- Seleccion de **pierna** de colocacion (izquierda o derecha) o colocacion automatica.
- Aceptacion de terminos y condiciones, politica de privacidad y contrato de distribuidor independiente.
- Verificacion de identidad (documento, selfie — configurable).

### 1.2 Perfil del Afiliado

**Datos personales:**
- Nombre completo, fecha de nacimiento, genero.
- Documento de identidad (tipo y numero).
- Direccion de residencia.
- Telefono, email, redes sociales.
- Foto de perfil.

**Datos fiscales:**
- RUT / RFC / NIT / Tax ID segun pais.
- Regimen fiscal.
- Datos bancarios para pago de comisiones (banco, tipo de cuenta, numero).

**Datos de la red:**
- ID de afiliado.
- Fecha de inscripcion.
- Patrocinador directo.
- Posicion en el arbol (pierna izquierda o derecha de quien).
- Rango actual (pagado) y rango maximo historico.
- Estado: Activo / Inactivo / Suspendido / Cancelado.
- PV actual del periodo.
- BV acumulado pierna izquierda y derecha.

### 1.3 Estados del Afiliado

| Estado | Descripcion |
|--------|-------------|
| **Pendiente** | Registro iniciado pero no ha completado la compra del kit. |
| **Activo** | Kit comprado y PV del periodo vigente cumplido. |
| **Inactivo** | No cumplio el PV minimo del periodo. No genera comisiones pero mantiene su posicion. |
| **Suspendido** | Suspension temporal por incumplimiento de politicas. No puede operar. |
| **Cancelado** | Baja definitiva. Su posicion queda "congelada" o se comprime (segun configuracion). |

### 1.4 Auto-envio (Autoship)

- Compra recurrente programada (mensual, tipicamente).
- El afiliado selecciona productos y la fecha de cargo.
- Se procesa automaticamente contra su metodo de pago registrado.
- Si el cargo falla, se reintenta X veces (configurable) y se notifica al afiliado.
- Mantiene al afiliado activo automaticamente.

---

## 2. Genealogia (Arbol de Red)

### 2.1 Vistas del Arbol

| Vista | Descripcion |
|-------|-------------|
| **Arbol Binario** | Visualizacion de la estructura binaria (pierna izquierda/derecha). Muestra la posicion de colocacion (placement). |
| **Arbol de Patrocinio** | Visualizacion de quien patrocino a quien (sponsor tree). Puede ser mas amplio que binario (multiples directos). |
| **Vista de Lista** | Listado tabular con filtros y busqueda. |
| **Mapa de Calor** | Visualizacion con colores segun actividad, rango o volumen. |

### 2.2 Informacion Visible por Nodo

- ID y nombre del afiliado.
- Rango actual (icono/color).
- Estado (activo/inactivo).
- PV del periodo.
- BV acumulado en cada pierna (solo relevante en arbol binario).
- Numero de directos activos.
- Fecha de inscripcion.

### 2.3 Funcionalidades

- Navegacion interactiva (zoom, pan, expandir/colapsar nodos).
- Busqueda de afiliado dentro del arbol.
- Filtros por rango, estado, fecha de inscripcion, volumen.
- Indicadores de posiciones vacias en el arbol binario.
- Linea de patrocinio resaltada (path desde un nodo hasta la raiz).

### 2.4 Funciones Administrativas

- Mover afiliado de posicion (con justificacion, aprobacion dual y registro de auditoria).
- Cambiar patrocinador (con las mismas restricciones).
- Inyectar afiliado en una posicion especifica.
- Comprimir nodos cancelados.
- Exportar arbol (PDF, Excel).

---

## 3. Productos y Catalogo

### 3.1 Estructura de Producto

| Campo | Descripcion |
|-------|-------------|
| SKU | Codigo unico del producto. |
| Nombre | Nombre comercial. |
| Descripcion | Descripcion detallada y corta. |
| Categoria | Clasificacion (suplementos, cosmeticos, bebidas, etc.). |
| Precio publico | Precio de venta al publico general. |
| Precio distribuidor | Precio para afiliados. |
| BV (Business Volume) | Puntos de volumen de negocio para comisiones. |
| PV (Personal Volume) | Puntos de volumen personal. |
| Peso | Para calculo de envio. |
| Imagenes | Galeria de imagenes del producto. |
| Stock | Cantidad disponible. |
| Estado | Activo / Inactivo / Descontinuado. |
| Pais de disponibilidad | En que paises/mercados esta disponible. |
| Impuestos aplicables | IVA, ISR, etc. segun pais. |

### 3.2 Kits de Inscripcion

- Paquetes predefinidos de productos para nuevos afiliados.
- Cada kit tiene un nivel de entrada diferente (basico, intermedio, premium).
- El nivel del kit puede influir en el rango inicial o en el tope de comisiones del primer periodo.
- Configurables por la administracion.

### 3.3 Promociones y Ofertas

- Descuentos por volumen.
- Productos gratis por alcanzar metas.
- Paquetes promocionales temporales.
- Cupones de descuento.

---

## 4. Pedidos y Ventas

### 4.1 Tipos de Pedido

| Tipo | Descripcion |
|------|-------------|
| **Inscripcion** | Primera compra (kit) de un nuevo afiliado. Activa la membresia. |
| **Re-compra / Consumo** | Compra recurrente del afiliado para mantener actividad y/o autoconsumo. |
| **Auto-envio** | Pedido automatico recurrente programado. |
| **Venta a cliente final** | Venta realizada por el afiliado a un consumidor no afiliado (retail). |
| **Pedido administrativo** | Pedido generado por la administracion (ajustes, cortesias, reposiciones). |

### 4.2 Flujo de Pedido

```
Creacion -> Pago Pendiente -> Pago Confirmado -> En Preparacion -> Enviado -> Entregado
                                                                           -> Devuelto (parcial/total)
         -> Cancelado (antes de envio)
```

### 4.3 Campos del Pedido

- Numero de pedido (autogenerado).
- Afiliado comprador.
- Fecha y hora.
- Productos (detalle con cantidad, precio unitario, BV, PV).
- Subtotal, impuestos, descuentos, envio, total.
- BV total del pedido y PV total.
- Metodo de pago.
- Estado del pedido.
- Direccion de envio.
- Numero de seguimiento (tracking).
- Factura asociada.

### 4.4 Reglas de Negocio de Pedidos

- Un pedido de inscripcion **debe** contener al menos un kit de inscripcion.
- El BV y PV del pedido se acreditan al afiliado **solo cuando el pago es confirmado**.
- Las devoluciones generan reverso de BV/PV y, si ya se liquidaron comisiones, se generan debitos en la siguiente liquidacion.
- Politica de devolucion configurable (30, 60, 90 dias, condiciones, excepciones).
- El pedido de auto-envio se genera automaticamente pero el pago puede fallar; en ese caso, el pedido queda en estado "Pago Pendiente" y se reintenta.

---

## 5. Comisiones y Liquidacion

### 5.1 Ciclo de Liquidacion

```
Cierre de periodo -> Calculo de volumenes -> Calificacion de rangos -> Calculo de bonos ->
Revision/Aprobacion -> Generacion de liquidacion -> Pago -> Conciliacion
```

### 5.2 Proceso Detallado

1. **Cierre de periodo:** Se congela el snapshot de volumen (BV, PV, GV) al final del periodo.
2. **Calculo de volumenes:**
   - Se suman los BV de todos los pedidos confirmados en el periodo para cada pierna de cada afiliado.
   - Se aplican los carry-overs del periodo anterior.
   - Se calcula el PV personal de cada afiliado.
3. **Calificacion de rangos:**
   - Se evalua el rango de cada afiliado segun la tabla de rangos.
   - Se aplican periodos de gracia si corresponde.
   - Se actualiza el rango pagado.
4. **Calculo de bonos:** Se ejecutan los algoritmos de cada tipo de bono en orden:
   - Bono de patrocinio directo (si no fue pagado inmediatamente).
   - Bono binario.
   - Bono unilevel.
   - Bono de liderazgo (matching).
   - Bonos de rango.
   - Pool global.
5. **Revision y aprobacion:**
   - El sistema genera un reporte previo (pre-liquidacion).
   - El gerente de operaciones o administrador revisa y aprueba.
   - Se pueden hacer ajustes manuales (con justificacion y auditoria).
6. **Generacion de liquidacion:**
   - Se genera el registro de pago para cada afiliado.
   - Se aplican retenciones fiscales si corresponde.
   - Se descuentan deudas, devoluciones pendientes o cargos administrativos.
7. **Pago:**
   - Transferencia bancaria, billetera virtual interna o pasarela de pago.
8. **Conciliacion:**
   - Verificacion de pagos exitosos vs fallidos.
   - Reprocesamiento de pagos fallidos.

### 5.3 Reglas Antifraude en Comisiones

- **Autoconsumo excesivo:** Alertar si un afiliado genera un % desproporcionado del BV de su propia pierna.
- **Cuentas multiples:** Detectar afiliados con datos similares (mismo domicilio, mismo banco, mismo IP de registro).
- **Red fantasma:** Detectar patrones de inscripciones masivas sin actividad posterior.
- **Manipulacion de piernas:** Detectar movimientos inusuales de volumen entre piernas.
- **Tope de ganancias:** Limitar el ratio comisiones/compras personales a un maximo razonable.

### 5.4 Ajustes y Excepciones

- Ajuste manual de comisiones (incremento o decremento) con aprobacion del administrador.
- Bonos especiales / discrecionales.
- Congelamiento temporal de comisiones por investigacion.
- Reverso de comisiones por devolucion de productos.

---

## 6. Inventario

### 6.1 Funcionalidades

- Control de stock por producto y por bodega/almacen.
- Alertas de stock bajo (umbral configurable por producto).
- Registro de entradas (compra a proveedor, devolucion de cliente) y salidas (venta, merma, ajuste).
- Lotes y fechas de vencimiento (importante para suplementos y cosmeticos).
- Inventario fisico (conteos periodicos con ajuste).
- Transferencias entre bodegas.

### 6.2 Multi-bodega

- Soporte para multiples puntos de distribucion.
- Cada bodega con su inventario independiente.
- Los pedidos se asignan a la bodega mas cercana o segun reglas configurables.

---

## 7. Reportes y Dashboard

### 7.1 Dashboard Ejecutivo

- **Red:** Total de afiliados, nuevas inscripciones del periodo, afiliados activos vs inactivos, distribucion por rango.
- **Ventas:** Ventas totales del periodo, comparativo con periodos anteriores, top productos, ticket promedio.
- **Comisiones:** Total liquidado, promedio por afiliado, top ganadores, ratio comisiones/ventas.
- **Inventario:** Stock critico, valor del inventario, rotacion.
- **Geografico:** Distribucion de la red y ventas por pais/region/ciudad.

### 7.2 Reportes Operativos

| Reporte | Descripcion |
|---------|-------------|
| Listado de afiliados | Filtrable por estado, rango, fecha, patrocinador. Exportable. |
| Reporte de genealogia | Arbol completo o parcial con metricas. |
| Reporte de ventas | Por periodo, producto, afiliado, region. |
| Reporte de comisiones | Detalle por afiliado, tipo de bono, periodo. |
| Reporte de BV/PV | Volumen por afiliado, pierna, acumulado y del periodo. |
| Reporte de inscripciones | Nuevos afiliados por periodo, patrocinador, kit. |
| Reporte de deserciones | Afiliados que pasaron a inactivo o cancelado. |
| Reporte de auto-envios | Estado de auto-envios: activos, fallidos, cancelados. |
| Reporte de inventario | Stock actual, movimientos, valoracion. |
| Reporte fiscal | Retenciones, facturacion, obligaciones por pais. |

### 7.3 Exportacion

- PDF, Excel (XLSX), CSV.

---

## 8. Administracion del Sistema

### 8.1 Configuracion General

- Nombre de Ganoherb, logo, informacion fiscal.
- Moneda base y monedas soportadas (multimoneda).
- Paises/mercados activos.
- Configuracion de periodos de liquidacion (semanal, quincenal, mensual).
- Parametros del plan de compensacion (porcentajes, topes, tabla de rangos).
- Politicas de devolucion.
- Textos legales (terminos, privacidad, contrato).

### 8.2 Gestion de Usuarios Administrativos

- Roles y permisos granulares.
- Registro de actividad por usuario (quien hizo que y cuando).
- Autenticacion de dos factores (2FA) para administradores.

### 8.3 Parametrizacion del Plan de Compensacion

Todo el plan de compensacion debe ser **configurable desde la administracion sin necesidad de modificar codigo**:

- Tabla de rangos y requisitos.
- Porcentajes de cada tipo de bono.
- Topes de ganancias por rango.
- Profundidad del unilevel por rango.
- Generaciones del matching bonus.
- Porcentaje del pool global.
- Reglas de carry-over y flush.
- Reglas de compresion.
- Reglas de derrame (spillover).

### 8.4 Herramientas de Soporte

- Busqueda avanzada de afiliados.
- Simulador de comisiones (what-if).
- Impersonar afiliado (ver el sistema desde su perspectiva, solo lectura).
- Notas internas por afiliado.
- Sistema de tickets / incidencias.

---

## 9. Comunicaciones y Notificaciones

### 9.1 Canales

- **Email:** Transaccional (confirmacion de pedido, pago de comision, etc.) y marketing (promociones, noticias).
- **SMS:** Alertas criticas (pago recibido, bono importante).
- **Notificaciones en el portal:** En tiempo real.
- **WhatsApp:** Notificaciones y recordatorios (fase futura).

### 9.2 Eventos de Notificacion

| Evento | Canal Sugerido |
|--------|---------------|
| Nuevo afiliado inscrito en tu red | Email + Portal |
| Pedido confirmado | Email |
| Pago de comision procesado | Email + SMS |
| Rango alcanzado | Email + Portal |
| Auto-envio proximo a procesarse | Email |
| Auto-envio fallido | Email + SMS |
| PV minimo no alcanzado (alerta) | Email + Portal |
| Cambio de estado de cuenta | Email |
| Nueva promocion disponible | Email + Portal |
| Liquidacion aprobada | Portal (admin) |

### 9.3 Plantillas

- Plantillas de email/SMS editables desde la administracion.
- Variables dinamicas (nombre, monto, rango, etc.).
- Soporte multilenguaje.

---

## 10. Facturacion e Integraciones Fiscales

### 10.1 Facturacion Electronica

- Generacion automatica de factura al confirmar un pedido.
- Cumplimiento de normativas fiscales por pais:
  - **Colombia:** Facturacion electronica DIAN (resolucion de facturacion, CUFE, XML firmado).
  - **Mexico:** CFDI ante el SAT.
  - **Peru:** Facturacion electronica SUNAT.
  - **Otros paises:** Adaptable segun requerimientos locales.
- Notas credito y notas debito.
- Numeracion secuencial y prefijos por punto de venta.

### 10.2 Retenciones

- Calculo automatico de retenciones sobre comisiones segun el regimen fiscal del afiliado y la normativa del pais.
- Certificados de retencion generables desde el sistema.
- Reporte de retenciones para declaraciones fiscales.

### 10.3 Reportes Fiscales

- Reporte de ventas por periodo para declaracion de IVA/impuestos.
- Reporte de comisiones pagadas (para reportar a la autoridad fiscal como gastos).
- Medios magneticos / informacion exogena (Colombia).

---

## 11. Pagos y Billetera Virtual

### 11.1 Billetera Virtual Interna

- Cada afiliado tiene una billetera virtual dentro del sistema.
- Las comisiones se acreditan a la billetera.
- El afiliado puede:
  - **Retirar** a su cuenta bancaria (con monto minimo y cargo por transferencia).
  - **Usar el saldo** para comprar productos (re-compras, auto-envio).
  - **Transferir** saldo a otro afiliado (configurable, con limites).
- Historial de movimientos detallado.

### 11.2 Metodos de Pago para Compras

- Tarjeta de credito/debito.
- Transferencia bancaria.
- Billetera virtual interna.
- Pago en efectivo en punto de distribucion.
- Metodos locales: PSE (Colombia), OXXO (Mexico), PagoEfectivo (Peru), etc.

### 11.3 Metodos de Desembolso de Comisiones

- Transferencia bancaria (ACH, SWIFT).
- Billetera virtual interna (sin costo).
- Terceros de pagos masivos (Payoneer, Paypal — fase futura).

---

## 12. Eventos y Capacitaciones

### 12.1 Eventos

- Registro de eventos (convenciones, lanzamientos, conferencias).
- Inscripcion de afiliados a eventos.
- Control de cupos y pagos.
- Reportes de asistencia.

### 12.2 Capacitaciones

- Biblioteca de contenido (videos, documentos, presentaciones).
- Cursos con modulos y seguimiento de progreso.
- Certificaciones internas.
- Vinculacion de capacitaciones con requisitos de rango (fase futura).

---

## 13. Normativas y Compliance

- Cumplimiento de regulaciones de venta directa por pais (ej: Ley 1700/2013 en Colombia).
- Registro ante las camaras de comercio y entes reguladores correspondientes.
- Transparencia en el plan de compensacion (accesible para todos los afiliados).
- Politica de devolucion clara (tipicamente 30 dias con producto sin abrir).
- Prohibicion explicita de esquemas piramidales: el sistema debe demostrar que los ingresos provienen de la venta de productos reales, no solo del reclutamiento.
