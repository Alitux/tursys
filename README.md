# TurSys - Gestión Profesional de Agencias de Turismo

**TurSys** es un módulo avanzado diseñado específicamente para agencias de turismo en **Odoo 18.0 CE**. Permite una administración integral de excursiones, logística de pasajeros y generación de documentación profesional para clientes y guías.

## 🚀 Características Principales

### 1. Gestión de Excursiones
- **Instancias Dinámicas**: Crea salidas específicas basadas en servicios (productos tipo servicio).
- **Control de Capacidad**: Monitoreo en tiempo real de plazas totales, usadas y disponibles.
- **Vistas Inteligentes**: 
    - **Lista**: Resumen de ocupación y estados con códigos de color.
    - **Calendario**: Planificación visual de todas las excursiones del mes/semana.
- **Flujo de Estados**: Programado, Finalizado y Cancelado.

### 2. Sistema de Reservas y Captura de Pasajeros
- **Carga Ágil**: Formulario optimizado ("Booking Card") para entrada rápida de datos.
- **Captura Completa**: Registro de Nombre, DNI/CUIL, Email, Teléfono, Fecha de Nacimiento, Nacionalidad e Idioma.
- **Cálculo Automático**: La edad del pasajero se calcula automáticamente al ingresar la fecha de nacimiento.
- **Identidad Digital**: Cada reserva genera un **UUID único** para validaciones electrónicas futuras.

### 3. CRM Automatizado
- **Integración con Contactos**: Al confirmar una reserva, el sistema busca automáticamente al pasajero por su DNI en la base de datos de Odoo.
- **Creación Inteligente**: Si el pasajero no existe, crea un nuevo contacto (`res.partner`); si existe, actualiza su información de contacto y médica.
- **Preparado para Facturar**: Al estar vinculados a `res.partner`, los pasajeros quedan listos para procesos de venta y facturación estándar de Odoo.

### 4. Reportes de Alta Calidad (PDF A4)
- **Voucher de Reserva**:
    - Diseño profesional y corporativo.
    - Optimizado para impresión en **una sola hoja A4**.
    - Incluye logo, datos del servicio, instrucciones de seguridad y código de validación.
- **Lista de Pasajeros (Hoja de Ruta)**:
    - Formato apaisado (**Landscape**) para máxima legibilidad.
    - Datos de pasajeros agrandados para uso en campo por los guías.
    - Incluye teléfonos, edades, necesidades especiales y observaciones de la reserva.

### 5. Configuración y Maestros
- **Nacionalidades**: Tabla pre-poblada con países comunes, ampliable por el usuario.
- **Idiomas**: Gestión centralizada de los idiomas principales de los pasajeros.

## 🛠️ Instalación y Uso

1. Instalar el módulo en el backoffice de Odoo.
2. Acceder al menú principal **TurSys**.
3. Crear primero una **Excursión** definiendo el servicio, fecha y capacidad total.
4. Desde la ficha de la excursión, añadir pasajeros haciendo clic en "Agregar una línea" en la pestaña de Pasajeros.
5. Completar la **Ficha del Pasajero** y hacer clic en **Confirmar**.
6. Imprimir el **Voucher** para el cliente o la **Lista de Pasajeros** para el guía desde los botones de la cabecera.

## 📝 Soporte Técnico
Desarrollado por **Alitux**
Sitio Web: [https://alitux.com.ar](https://alitux.com.ar)
Licencia: LGPL-3
