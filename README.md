# TurSys - Gestión Profesional de Agencias de Turismo

**TurSys** es un módulo avanzado diseñado específicamente para agencias de turismo en **Odoo 18.0 CE**. Permite una administración integral de excursiones, logística de pasajeros, check-in en campo y generación de documentación profesional para clientes y guías.

## 🚀 Características Principales

### 1. Gestión de Excursiones
- **Instancias Dinámicas**: Crea salidas específicas basadas en servicios (productos tipo servicio).
- **Control de Capacidad**: Monitoreo en tiempo real de plazas totales, usadas, disponibles, en lista de espera, presentados y ausentes.
- **Vistas Inteligentes**:
    - **Lista**: Resumen de ocupación y estados con códigos de color.
    - **Calendario**: Planificación visual de todas las excursiones del mes/semana.
- **Flujo de Estados**: Programado, Finalizado y Cancelado.
- **Asignación de Guías**: un **guía responsable** y **guías auxiliares** por excursión (ver *Guías y Check-in desde el móvil*).

### 2. Sistema de Reservas y Captura de Pasajeros
- **Carga Ágil**: Formulario optimizado ("Booking Card") para entrada rápida de datos.
- **Captura Completa**: Registro de Nombre, DNI/CUIL, Email, Teléfono, Fecha de Nacimiento, Nacionalidad e Idioma.
- **Cálculo Automático**: La edad del pasajero se calcula y **se almacena** automáticamente (permite filtrar, ordenar y agrupar por edad).
- **Identidad Digital**: Cada reserva genera un **UUID único** para validaciones electrónicas futuras.

### 3. Ciclo de Vida de la Reserva

El estado de la reserva es independiente del estado del pago, para poder representar situaciones reales (por ejemplo, confirmado con seña, o cancelado con reembolso).

| Estado de la reserva | Descripción | ¿Ocupa cupo? |
|---|---|---|
| **Borrador** | Creada, pendiente de confirmar | No |
| **Lista de espera** | No hay cupo disponible | No |
| **Confirmado** | Pago/seña recibida, reserva firme | **Sí** |
| **Presentado** | El guía realizó el check-in | **Sí** |
| **Ausente** | Estaba confirmado y no se presentó | No (libera el cupo) |
| **Cancelado** | Reserva anulada | No |

**Estado del pago** (independiente): *No pagado*, *Seña*, *Pagado*, *Reembolsado*.

**Lista de espera automática**: cuando se cancela una reserva o se marca un ausente, el sistema promueve automáticamente a la primera reserva en espera si hay cupo.

**Motivo de cancelación**: cliente, decisión de la agencia, mínimo no alcanzado, clima u otro (con nota libre).

### 4. Guías y Check-in desde el móvil (Portal del Guía)

- **Los guías son usuarios marcados con el grupo TurSys** (nunca se crean desde el formulario de la excursión). Solo los usuarios marcados como guías aparecen como elegibles en los campos de asignación. Hay **dos grupos** según el caso:
    - **TurSys / Guide (Portal)** → guía de campo: implica el grupo *Guide* **y** el tipo de usuario *Portal*, así **nunca accede al backoffice** y solo ve sus excursiones asignadas.
    - **TurSys / Guide** → marca funcional de guía: se asigna a un usuario que **ya es de backend** (p. ej. un coordinador) para poder asignarle excursiones **sin** cambiar su tipo de usuario. El portal y las restricciones aplican solo a los guías de portal.
    - *Nota*: Odoo no permite que un mismo usuario sea *Interno* y *Portal* a la vez, por eso la **marca de guía** está separada del **acceso portal**.
- **Asignación**: en la ficha de cada excursión, los campos **Guía responsable** y **Guías auxiliares** solo permiten **elegir** entre los usuarios marcados como guías (no se pueden crear usuarios desde ese formulario).
- **Aviso automático**: al asignar un guía (responsable o auxiliar) se le genera una **actividad** ("Excursion Assigned") y se lo notifica por email. Si se le quita la asignación, la actividad pendiente se elimina.
- **Portal del guía**: al ingresar, ve la tarjeta **"Excursions assigned to you"** con la lista de sus excursiones asignadas y el detalle de cada una con sus pasajeros.
- **Check-in en un toque**: desde el celular, el guía marca a cada pasajero como **Presentado** o **Ausente**, y puede **deshacer**. Se registra **fecha/hora** y **qué usuario** lo hizo.
- **Seguridad**: cada **guía de portal** solo puede ver las excursiones (y sus reservas) donde figura como **responsable o auxiliar**; el acceso a cualquier otra se deniega. Los guías que además son usuarios de backend no quedan restringidos.
- **Vista móvil**: el detalle de la excursión se adapta al teléfono (una tarjeta por pasajero, con botones grandes de check-in), cómodo para usarlo en pleno tour.
- **Buscador instantáneo**: sobre la lista de pasajeros hay un campo que filtra en tiempo real por nombre, apellido, DNI/CUIL, teléfono o email, sin recargar la página (muy útil para encontrar a alguien en la puerta del micro).
- **Auditoría desde el backend**: en la ficha de la excursión, el botón **"View in Portal"** (visible para administradores) abre la pantalla del guía en una pestaña nueva para revisar el check-in.
- **Notas del guía**: desde el portal, el guía escribe comentarios de la excursión (clima, incidentes, algo particular) y quedan publicados en el **chatter** de la excursión, con autor y fecha.
- **Inicio y fin de la excursión**: el guía responsable (o un administrador) puede **iniciar** la excursión desde el portal y queda guardado el **timestamp** y quién lo hizo; al **finalizar**, se registra el cierre, se marcan los ausentes y la excursión pasa a **Finalizada**.
- La **Lista de Pasajeros** impresa incluye una columna **Check** (☑ presentado · ☐ pendiente · ✗ ausente) para uso manual.
- El backoffice conserva además el menú **TurSys → Check-in** (vista Kanban) para el personal administrativo.

### 5. CRM Automatizado
- **Integración con Contactos**: Al confirmar una reserva, el sistema busca automáticamente al pasajero por su DNI en la base de datos de Odoo.
- **Creación Inteligente**: Si el pasajero no existe, crea un nuevo contacto (`res.partner`); si existe, **completa solo los datos faltantes** sin sobrescribir la información ya cargada.
- **Preparado para Facturar**: Al estar vinculados a `res.partner`, los pasajeros quedan listos para procesos de venta y facturación estándar de Odoo.

### 6. Reportes de Alta Calidad (PDF A4)
- **Voucher de Reserva**:
    - Diseño profesional y corporativo.
    - Optimizado para impresión en **una sola hoja A4**.
    - Incluye logo, datos del servicio, instrucciones de seguridad y código de validación.
- **Lista de Pasajeros (Hoja de Ruta)**:
    - Formato apaisado (**Landscape**) para máxima legibilidad.
    - Datos de pasajeros agrandados para uso en campo por los guías.
    - Incluye teléfonos, edades, necesidades especiales, observaciones y **columna de check-in**.
    - Solo incluye reservas **confirmadas, presentadas y ausentes** (excluye borradores, lista de espera y canceladas).

### 7. Automatizaciones (Tareas Programadas)
- **Actualización de edades** (diaria): recalcula la edad de los pasajeros y contactos al cumplir años.
- **Cierre de excursiones vencidas** (cada hora): finaliza automáticamente las excursiones cuya fecha ya pasó y marca como **Ausente** a los confirmados que no hicieron check-in.
- **Concurrencia segura**: la confirmación de reservas usa bloqueo de base de datos para evitar sobreventa.

### 8. Configuración y Maestros
- **Nacionalidades**: Tabla pre-poblada con países comunes, ampliable por el usuario.
- **Idiomas**: Gestión centralizada de los idiomas principales de los pasajeros.
- El menú **Configuración** (y los maestros) están restringidos al grupo *Ajustes / Administración*.

## 🛠️ Instalación y Uso

1. Instalar el módulo en el backoffice de Odoo.
2. Acceder al menú principal **TurSys**.
3. Crear primero una **Excursión** definiendo el servicio, fecha y capacidad total.
4. Desde la ficha de la excursión, añadir pasajeros en la pestaña **Pasajeros**.
5. Completar la **Ficha del Pasajero** y hacer clic en **Confirmar** (o **Lista de espera** si no hay cupo).
6. Asignar los **guías** de la salida (responsable y auxiliares). Para que un usuario sea guía: *Ajustes → Usuarios* → asignarle **TurSys / Guide (Portal)** si es un guía de campo que solo usará el portal, o **TurSys / Guide** si además es un usuario de backend. Al asignarlo recibe una **actividad** de aviso.
7. El día de la salida, el guía ingresa a su **portal** desde el celular, abre la excursión asignada y marca cada pasajero (**Presentado** / **Ausente** / **Deshacer**).
8. Imprimir el **Voucher** para el cliente o la **Lista de Pasajeros** para el guía desde los botones de la cabecera.

## 📝 Soporte Técnico
Desarrollado por **Alitux**
Sitio Web: [https://alitux.com.ar](https://alitux.com.ar)
Licencia: LGPL-3
