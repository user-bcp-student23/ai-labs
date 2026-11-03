# Bug Triage -> Report Checklist

## 1. Summary
Transferencias duplicadas cuando el usuario presiona "Enviar" más de una vez
con latencia alta. Afecta aproximadamente al 3% de transferencias en horario
pico y hoy solo tiene workaround manual vía soporte.

## 2. Entorno y precondiciones
- Frontend web de transferencias, versión 2.4.1, en Chrome y Edge.
- Red con latencia alta (reproducible con throttling "Slow 3G").
- Usuario de prueba con saldo suficiente en entorno de QA.

## 3. Pasos para reproducir
1. Iniciar sesión con un usuario de prueba.
2. Activar throttling "Slow 3G" en DevTools.
3. Completar una transferencia de prueba.
4. Presionar "Enviar" dos veces seguidas.
5. Revisar el historial: aparecen dos transferencias con el mismo monto y destino.

## 4. Resultado esperado vs. actual
- **Esperado:** una sola transferencia; el botón queda deshabilitado mientras se procesa.
- **Actual:** dos transferencias registradas.

## 5. Severidad y prioridad
- **Severidad técnica:** High (duplica movimientos financieros).
- **Prioridad de negocio:** P2 (impacto recurrente, con workaround manual).
- **Justificación:** genera movimientos no autorizados y carga operativa a soporte, pero no bloquea el servicio completo.

## 6. Impacto
- **Usuarios o procesos afectados:** usuarios que transfieren desde red lenta; equipo de soporte para reversiones.
- **Frecuencia estimada:** ~3% de transferencias en horario pico (estimación de soporte, por validar).
- **Workaround:** reversión manual solicitada a soporte.

## 7. Evidencia adjunta
- Logs del servicio de transferencias con dos solicitudes POST, mismo monto e identificadores de solicitud distintos (datos enmascarados).
- Captura del historial con la duplicidad (datos de prueba).
- Video corto de reproducción con throttling activo.

## 8. Causa probable y hipótesis
- Hipótesis 1: el botón no se deshabilita tras el primer clic, así que el frontend envía dos solicitudes.
- Hipótesis 2: el API no valida idempotencia; no existe clave de solicitud compartida entre reintentos.

## 9. Criterios de aceptación de la corrección (medibles)
- Al presionar "Enviar" 5 veces en menos de 1 segundo se envía exactamente 1 solicitud al API.
- Con throttling "Slow 3G", el botón permanece deshabilitado hasta recibir respuesta.
- Reintentos con la misma clave de idempotencia devuelven la misma transferencia sin crear otra.
- 0 transferencias duplicadas en la prueba de regresión de 100 envíos en QA.

## 10. Plan de validación
- **Pruebas unitarias:** lógica de deshabilitado del botón; validación de clave de idempotencia en el servicio.
- **Pruebas de regresión funcional:** flujo completo de transferencia en Chrome y Edge con red lenta.
- **Seguridad (mínimo):** la clave de idempotencia no expone datos sensibles; los logs siguen enmascarados.
- **Evidencia requerida:** salida de pruebas unitarias, reporte de la prueba de 100 envíos y captura de historial sin duplicados.

## 11. Tareas sugeridas por rol
- **QA:**
  - Automatizar el caso de doble clic con throttling.
  - Ejecutar la prueba de regresión de 100 envíos.
  - Verificar el historial tras la corrección.
- **Backend:**
  - Agregar clave de idempotencia al endpoint de transferencias.
  - Devolver la transferencia existente ante una clave repetida.
  - Agregar pruebas unitarias del caso de reintento.
- **Frontend:**
  - Deshabilitar el botón desde el primer clic hasta la respuesta.
  - Enviar la clave de idempotencia en cada intento del mismo formulario.
  - Agregar pruebas del estado del botón.
- **Tech Lead:**
  - Revisar el contrato de idempotencia con el servicio de cuentas.
  - Aprobar el PR y la prioridad.
  - Confirmar la estrategia de despliegue.
- **Cyber:**
  - Revisar que los logs no expongan datos sensibles.
  - Validar el manejo de claves de idempotencia.

## 12. Preguntas abiertas
- ¿Qué fuente mide el 3% de frecuencia y en qué periodo?
- ¿Qué servicio es dueño del contrato de idempotencia?
- ¿Existe una reversión automática o siempre es manual?
