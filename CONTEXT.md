# CONTEXT.md — Analizador de Encuestas JDR

## Descripción del Proyecto
Herramienta HTML standalone para consultores que analizan encuestas organizacionales (modelo JDR — Job Demands-Resources). Sin backend, todo corre en el navegador. Archivo único: `analizador_encuestas_v2.html`.

## Stack Técnico
- **Frontend**: HTML/CSS/JS vanilla — archivo único standalone
- **Librerías CDN**:
  - `XLSX.js 0.18.5` — lectura/escritura de Excel
  - `D3.js 7.8.5` — visualización del organigrama
  - `Chart.js 4.4.1` — gráficos
  - `JSZip 3.10.1` — generación de archivos PPT
- **Librería embebida**: `xlsx-style` (embebida inline para escritura con estilos — actualmente NO activa, se usa XLSX estándar)

## Arquitectura — 3 Secciones Principales

### Sección 1 — Previo Medición
Valida archivo de carga ANTES de subirlo a la plataforma.
- **Paso 1**: Columnas requeridas (`S1_REQ`)
- **Paso 2**: Duplicados de ID y correo + limpieza automática
- **Paso 3**: Validación formato correos
- **Paso 4**: Organigrama D3 con detección de auto-ciclos y jefaturas inexistentes

**Estado actual**: Funcional. Manejo especial de auto-ciclos (persona se reporta a sí misma → raíz).

### Sección 2 — Revisión Resultados
Analiza el archivo descargado de la plataforma. Flujo de 6 pasos (panels 0-5):
- **Panel 0**: Carga del archivo + verificación de columnas (`renderColVerification`)
- **Panel 1**: Dimensiones detectadas
- **Panel 2**: Rangos de respuesta
- **Panel 3**: Verificación de cálculos
- **Panel 4**: Consistencia (compara descargado vs archivo de carga original)
- **Panel 5**: Variables nuevas (VIGOR, DEDICATION, etc.)

**Variables de estado**: `G` (resultados), `C` (consistencia)

**Normalización**: `norm(s)` / `rNorm(s)` — lowercase, sin tildes, sin paréntesis

### Sección 3 — Reportería
Dos subsecciones independientes:

#### 3A — Tablas Excel
- Carga BBDD consolidada
- Detecta mediciones automáticamente (o medición única si no hay columna MEDICION)
- Selector dinámico de hojas a generar (clasificaciones detectadas automáticamente)
- Selector de dimensiones disponibles con checkboxes
- Genera Excel con hojas: General, Clasificaciones, Demográficos, eNPS integrado en tabla
- N < 5 → celda roja
- Colores por dimensión hardcodeados en `DIM_COLORS`

#### 3B — Gráficos
Dos sub-tabs:

**Gráficos Predeterminados** (`RCP`):
- 7 gráficos: Engagement, Agotamiento, Histórico, Recursos/Demandas, eNPS, Ranking Criticidad, Óptimo vs Crítico, Demográficos
- Gráficos Engagement/Agotamiento tienen: segmentación, N mínimo confidencialidad, ocultar/mostrar bajo N, líneas benchmark
- Líneas benchmark: valor fijo, promedio medición, promedio segmento; múltiples simultáneas; color + etiqueta + punteada/continua
- Canvas con scroll horizontal para muchas barras
- Descarga PNG y PPT

**Gráfico Libre** (`RC`):
- Tipos: barras, barras 100%, columnas, columnas 100%, líneas, dispersión, histograma
- Selector de mediciones, variables, segmentación, título

## Sistema de Detección de Columnas (Crítico)

### `colAliasLookup(nc, headers, normFn)`
Función compartida que busca columnas por alias. Usa `RCP_COL_ALIASES` (mapa de variaciones conocidas).

### `rcpColIdxFuzzy(col)` / `rColIdxFuzzy(name)`
Búsqueda fuzzy en 3 niveles:
1. Match exacto
2. Código al inicio de columna: `(WE1) - texto` → token = `we1`
3. Alias del mapa `RCP_COL_ALIASES`

**IMPORTANTE**: `RCP_COL_ALIASES` y `rcpColIdxFuzzy` deben definirse ANTES de `rcpMean` y de cualquier función que las llame. Han causado errores de TDZ/undefined múltiples veces.

## Maestro de Dimensiones (`R_DIMS` / `RCP_DEFS`)

```javascript
// Dimensiones con sus preguntas (maestro hardcodeado)
Engagement (WE1-9, escala 0-6)
  - Vigor (WE1,WE2,WE5)
  - Dedicación (WE3,WE4,WE7)
  - Absorción (WE6,WE8,WE9)
Agotamiento (EX1-4, escala 1-4)
Autoeficacia (SE1-3)
Optimismo (optim1,2,4,5)
Oportunidades (oppor1-3)
Coaching (coach1,2,3,5)
Retroalimentación (feedb1-3)
Colaboración (soc1-3)
Autonomía (auto1-3)
Presión (wp1-4)
Cognitivas (cogn1-4)
Emocionales (emo1,2,3,4,6)
Conflicto de Rol (rolcon1,3,4)
Trabas (hassle2,3,4,5)
```

**eNPS**: `ENPS_CAT` / `eNPS_tag`. Etiquetas: `Promotor(es)`, `Neutro(s)`, `Detractor(es)`, `Pasivo(s)`.
Match siempre con regex: `/^promotor/i`, `/^detractor/i`, `/^neutro|^pasivo/i`

## Verificación Universal de Columnas (`renderColVerification`)
Componente reutilizable que muestra panel de mapeo antes de avanzar en cualquier sección.
- Siempre visible al cargar Excel en S1, S2 Resultados, S2 Consistencia
- Bloquea avance si faltan columnas obligatorias
- Permite ajuste manual de cualquier columna

## Variables de Estado Globales
```javascript
G    // Sección 2 resultados
C    // Consistencia  
S1   // Previo medición
R    // Reportería tablas
RC   // Gráfico libre
RCP  // Gráficos predeterminados
```

## Bugs Conocidos / Historial de Problemas Recurrentes

1. **`rcpColIdxFuzzy` / `RCP_COL_ALIASES` undefined**: Se definen tarde. Solución: colocar antes de `rcpColIdx`.
2. **`fileInfo` null**: El elemento no existe. Usar `panel0` como contenedor en `process()`.
3. **Auto-ciclos organigrama**: Persona con jef===id. Se trata como raíz con `selfCycleIds`.
4. **eNPS siempre 0**: Usar regex en vez de `===` para comparar tags.
5. **Medición única sin columna MEDICION**: Detectar con `medCol === '__single__'`.
6. **TDZ `isOrgSegRC`**: Declarar antes de usar, no después.
7. **Canvas `rcp-canvas-wrap` null**: Verificar existencia antes de `.style`.

## Pendientes Importantes
- [ ] Versión offline (incrustar librerías CDN)
- [ ] Formato con colores en Excel (requiere xlsx-style activado — actualmente tablas sin color)
- [ ] Completar gráficos predeterminados: Histórico, Recursos/Demandas, eNPS, Ranking, Óptimo vs Crítico, Demográficos (solo Engagement/Agotamiento funciona completamente)
- [ ] Módulo comparación entre años en reportería
- [ ] Validación alerta cuando archivo S2 tiene 0 dimensiones detectadas

## Flujo de Trabajo Recomendado
Al hacer cambios en Claude Code:
1. Siempre verificar sintaxis JS con `node --check` después de editar
2. Buscar errores de TDZ: funciones usadas antes de declararse
3. Nunca usar `document.getElementById('fileInfo')` — no existe
4. Al agregar funciones JS nuevas que usen `RCP`, verificar que `RCP_COL_ALIASES` esté definido antes

## Cómo Ejecutar
Abrir `analizador_encuestas_v2.html` directamente en Chrome/Edge/Firefox.
Requiere internet para cargar las librerías CDN (D3, Chart.js, JSZip, XLSX).
