## Título corto del defecto
Transferencia duplicada al presionar "Enviar" dos veces con conexión lenta.

## Reporte original
Usuarios de la app web reportan que, al ver que la pantalla tarda, presionan "Enviar" otra vez y la transferencia aparece dos veces. Hay tickets de soporte con capturas de pantalla del historial.

## Entorno
Web frontend en producción, versión 2.4.1. Navegador Chrome y Edge. Red móvil con latencia alta.

## Pasos para reproducir (si se conocen)
1. Iniciar sesión con un usuario de prueba.
2. Activar throttling de red a "Slow 3G" en DevTools.
3. Completar una transferencia de prueba y presionar "Enviar" dos veces.

## Resultado esperado vs. resultado actual
Esperado: una sola transferencia y el botón deshabilitado mientras se procesa.
Actual: dos transferencias registradas con el mismo monto y destino.

## Frecuencia y usuarios afectados
Estimado: 3% de transferencias en horario pico, según soporte.

## Logs o mensajes de error (sin datos sensibles)
Sin error visible en UI. En logs del servicio de transferencias aparecen dos solicitudes POST con distinto identificador de solicitud y el mismo monto.

## Módulos o servicios involucrados
Frontend de transferencias, API REST de transferencias, servicio de cuentas.

## Workaround disponible
Sí: el usuario revisa el historial y solicita la reversión manual a soporte.

## Team Definition of Done (DoD)
Pruebas unitarias, prueba de regresión funcional, PR revisado y documentación breve del cambio.
