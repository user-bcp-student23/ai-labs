---
name: bug-triage-report-checklist
description: Estandariza el triage y reporte de bugs generando un reporte mínimo y trazable que cubra resumen, pasos de reproducción, severidad, impacto, evidencia, causa probable y plan de validación de la corrección.
---

# Skill: Bug Triage -> Report Checklist

## 1) Metadata
- **Skill ID:** bug-triage-report-checklist
- **Version:** 0.1.0
- **Purpose:** Estandarizar el triage y reporte de bugs para que cualquier integrante del equipo pueda reproducir, priorizar y validar la corrección sin depender de conversaciones informales.
- **Audience (roles):** QA, Backend, Frontend, Tech Lead, Chapter/PO, Cyber
- **When to use:** Al recibir un reporte de defecto de usuario, QA o monitoreo que deba priorizarse o asignarse.
- **When NOT to use:** Incidentes P1 en producción que requieren respuesta inmediata (usar el proceso de incidentes), solicitudes de nueva funcionalidad o errores de tipeo sin impacto funcional.
- **Sensitive inputs:** No incluyas datos reales de clientes, credenciales, tokens, números de cuenta, logs con datos personales ni URLs internas no autorizadas. Usa datos de prueba o valores enmascarados.
- **Expected output:** Markdown estructurado mediante la sección Output a continuación.

## 2) Inputs
Proporciona la información en este formato:

- **Título corto del defecto:**
- **Reporte original (texto libre, capturas describidas):**
- **Entorno (ambiente, versión, navegador/cliente):**
- **Pasos para reproducir (si se conocen):**
- **Resultado esperado vs. resultado actual:**
- **Frecuencia y usuarios afectados (estimado):**
- **Logs o mensajes de error (sin datos sensibles):**
- **Módulos o servicios involucrados:**
- **Workaround disponible (sí/no y cuál):**
- **Team Definition of Done (DoD):** (si está disponible)

## 3) Output
Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Summary**
2. **Entorno y precondiciones**
3. **Pasos para reproducir**
4. **Resultado esperado vs. actual**
5. **Severidad y prioridad**
    - Severidad técnica (Critical / High / Medium / Low)
    - Prioridad de negocio (P1 / P2 / P3 / P4)
    - Justificación
6. **Impacto**
    - Usuarios o procesos afectados
    - Frecuencia estimada
    - Workaround disponible
7. **Evidencia adjunta**
8. **Causa probable y hipótesis**
9. **Criterios de aceptación de la corrección (medibles)**
10. **Plan de validación**
    - Pruebas unitarias
    - Pruebas de regresión funcional
    - Seguridad (comprobaciones mínimas)
    - Evidencia requerida (qué adjuntar)
11. **Tareas sugeridas por rol**
    - QA
    - Backend
    - Frontend
    - Tech Lead
    - Cyber
12. **Preguntas abiertas**

## 4) Constraints
- No inventes pasos de reproducción, versiones ni causas: si falta información, inclúyela bajo **Preguntas abiertas**.
- No propongas herramientas fuera del stack permitido.
- No incluyas datos sensibles, secretos ni logs con información personal; enmascara o reemplaza por valores de prueba.
- La severidad debe justificarse con impacto observable, no con opiniones.
- Los criterios de aceptación deben ser verificables; no escribas “corregir el error” sin una condición comprobable.
- El plan de validación debe incluir al menos un elemento de evidencia concreto, como salida de pruebas, un caso reproducible o un archivo actualizado.
- Mantén la salida en un máximo de 1-2 páginas para que siga siendo usable.

## 5) Validation Rules
La salida es válida si:
- Incluye todas las secciones definidas en Output.
- Tiene pasos de reproducción numerados, o indica explícitamente que no son reproducibles con la información disponible.
- Tiene al menos 3 criterios de aceptación medibles.
- Tiene al menos 3 tareas para cada rol central: QA, Backend y Tech Lead, o explica por qué un rol no aplica.
- La severidad y prioridad incluyen justificación.
- No contiene datos sensibles ni secretos.
- No contiene supuestos no declarados.

## 6) Evidence
Adjunta o referencia estos elementos en el ticket o PR:
- `SKILL.md` versionado.
- `examples/input.sample.md`.
- `examples/output.sample.md`.
- Tag de versión para el Skill, como `skill-bug-triage-v0.1.0`.
