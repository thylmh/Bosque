# Despliegue en Cloud Run + Cloud Storage

## Prerrequisitos
- Proyecto de GCP con facturación activa.
- `gcloud` configurado (`gcloud auth login` y `gcloud config set project <PROYECTO>`).
- APIs habilitadas:
  - Cloud Run
  - Cloud Build
  - Artifact Registry
  - Cloud SQL Admin
  - Identity Platform (cuando se active login)

## 1) Backend (FastAPI) en Cloud Run

### 1.1 Crear repositorio en Artifact Registry
```bash
gcloud artifacts repositories create bosque-api \
  --repository-format=docker \
  --location=southamerica-east1
```

### 1.2 Construir y subir la imagen
```bash
gcloud builds submit \
  --region=southamerica-east1 \
  --tag southamerica-east1-docker.pkg.dev/PROYECTO/bosque-api/bosque-api:latest \
  .
```
> **Importante:** ejecuta el comando desde la carpeta del repo (donde vive el `Dockerfile`) o ajusta la ruta final por el directorio correcto.

### 1.3 Desplegar Cloud Run con Cloud SQL
> Sustituye `PROYECTO` y el nombre de la instancia (`CONNECTION_NAME`).
```bash
gcloud run deploy bosque-api \
  --image southamerica-east1-docker.pkg.dev/PROYECTO/bosque-api/bosque-api:latest \
  --platform managed \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --add-cloudsql-instances CONNECTION_NAME \
  --set-env-vars ALLOWED_DOMAIN=humboldt.org.co,ADMIN_EMAILS=rbetancur@humboldt.org.co,aplicaciones@humboldt.org.co,hbettin@humboldt.org.co,DB_PASS=CAMBIAR,CORS_ORIGINS=*
```

> **Nota:** ajusta `CORS_ORIGINS` al dominio del bucket cuando esté publicado el frontend.
> **Nota:** si quieres permitir a cualquier usuario del dominio, deja `ADMIN_EMAILS` vacío.

## 2) Frontend (Index.html + app.css) en Cloud Storage

### 2.1 Crear bucket estático
```bash
gsutil mb -l southamerica-east1 gs://bosque-frontend
```

### 2.2 Configurar hosting estático
```bash
gsutil web set -m Index.html -e Index.html gs://bosque-frontend
```

### 2.3 Subir archivos
```bash
gsutil cp Index.html app.css gs://bosque-frontend
```

### 2.3.1 Forzar UTF-8 en el HTML (recomendado)
Si ves tildes o emojis dañados, asegura el `Content-Type` con charset UTF-8:
```bash
gsutil setmeta -h "Content-Type:text/html; charset=utf-8" gs://bosque-frontend/Index.html
```

### 2.4 Hacer público el bucket (opcional en pruebas)
```bash
gsutil iam ch allUsers:objectViewer gs://bosque-frontend
```

## 3) Conectar frontend con backend
- En el navegador, el frontend pedirá iniciar sesión con Google y enviará el correo corporativo como `X-User-Email`.
- La primera vez también pedirá la **URL del backend** (Cloud Run), por ejemplo:
  - `https://bosque-api-xyz.a.run.app`
  - Ese valor se guarda en `localStorage` como `api_base_url`.
- Configura `CORS_ORIGINS` en Cloud Run para permitir el dominio del bucket.
  - Ejemplo: `CORS_ORIGINS=https://storage.googleapis.com` o el dominio del website bucket.
- Para el inicio de sesión con Google, configura el Client ID real en `Index.html` (variable `GOOGLE_CLIENT_ID`) o guarda el valor en `localStorage` con la clave `google_client_id`.
- Si ves errores como “The given client ID is not found”, revisa que el Client ID exista y que el dominio del frontend esté autorizado en Google Cloud Console.

## 4) Siguientes pasos recomendados
- Activar Google Identity Platform (login real con cuentas corporativas).
- Crear tabla de permisos (por rol) en Cloud SQL para reemplazar la lista estática.
- Migrar catálogos/dashboards a endpoints REST.
