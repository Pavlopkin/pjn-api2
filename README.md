# PJN API 🏛️

API para consultar expedientes judiciales del **Poder Judicial de la Nación Argentina**.

## Deploy en Google Cloud Run (gratis)

### Requisitos
- Cuenta de Google
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) instalado

### Pasos

```bash
# 1. Clonar / descargar el proyecto
cd pjn-api

# 2. Autenticarse en Google Cloud
gcloud auth login

# 3. Crear proyecto (o usar uno existente)
gcloud projects create pjn-api-2026 --name="PJN API"
gcloud config set project pjn-api-2026

# 4. Habilitar facturación y Cloud Run (necesario aunque sea gratis)
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 5. Deploy directo desde el código (sin Docker manual)
gcloud run deploy pjn-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars API_TOKEN=tu-token-secreto-aqui
```

¡Listo! Cloud Run te da la URL pública.

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/docs` | Documentación interactiva (Swagger) |
| POST | `/expedientes/buscar` | Busca expediente por número/año/fuero |
| POST | `/expedientes/mis-causas` | Lista causas del usuario |

## Ejemplos de uso

### Buscar expediente
```bash
curl -X POST https://TU-URL.run.app/expedientes/buscar \
  -H "Authorization: Bearer tu-token-secreto-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "20-12345678-9",
    "password": "tu_contraseña_pjn",
    "numero": "7639",
    "anio": "2026",
    "jurisdiccion": "COM"
  }'
```

### Mis causas
```bash
curl -X POST https://TU-URL.run.app/expedientes/mis-causas \
  -H "Authorization: Bearer tu-token-secreto-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "20-12345678-9",
    "password": "tu_contraseña_pjn"
  }'
```

## Fueros disponibles

| Código | Fuero |
|--------|-------|
| COM | Comercial |
| CIV | Civil |
| CNT | Trabajo |
| CAF | Contencioso Administrativo Federal |
| CFP | Criminal y Correccional Federal |
| CSJ | Corte Suprema |

## Capa gratuita de Cloud Run
- **2 millones de requests/mes** gratis
- **360,000 GB-segundos** de cómputo gratis
- Más que suficiente para uso personal/profesional
