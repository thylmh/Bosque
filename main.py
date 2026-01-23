import os
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from google.cloud.sql.connector import Connector

# Auth: Cloud Run IAM / OIDC
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


app = FastAPI(title="bosque-api")

# =============================================================================
# ENV / CONFIG
# =============================================================================
ALLOWED_DOMAIN = os.environ.get("ALLOWED_DOMAIN", "humboldt.org.co").lower().strip()

CORS_ORIGINS_RAW = os.environ.get("CORS_ORIGINS", "*").strip()
if CORS_ORIGINS_RAW == "*":
    cors_origins = ["*"]
    allow_credentials = False
else:
    cors_origins = [o.strip() for o in CORS_ORIGINS_RAW.split(",") if o.strip()]
    if "https://storage.googleapis.com" not in cors_origins:
        cors_origins.append("https://storage.googleapis.com")
    allow_credentials = True

# Audience recomendado: URL del servicio Cloud Run.
AUDIENCE = os.environ.get("AUDIENCE", "").strip()

DB_USER = os.environ.get("DB_USER", "bosquebd").strip()
DB_NAME = os.environ.get("DB_NAME", "bosquebd").strip()
DB_PASS = os.environ.get("DB_PASS")  # obligatorio
CLOUDSQL_CONNECTION_NAME = os.environ.get("CLOUDSQL_CONNECTION_NAME", "").strip()

if not DB_PASS:
    raise RuntimeError("Falta variable de entorno DB_PASS (obligatoria).")

if not CLOUDSQL_CONNECTION_NAME:
    raise RuntimeError("Falta variable de entorno CLOUDSQL_CONNECTION_NAME (ej: proyecto:region:instancia).")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# CLOUD SQL CONNECTOR (GLOBAL) + SQLALCHEMY ENGINE
# =============================================================================
connector = Connector()


def getconn():
    # Cloud SQL MySQL via pymysql
    return connector.connect(
        CLOUDSQL_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
    )


engine = create_engine(
    "mysql+pymysql://",
    creator=getconn,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


@app.on_event("shutdown")
def shutdown_event():
    try:
        connector.close()
    except Exception:
        pass


# =============================================================================
# AUTH (CLOUD RUN IAM / OIDC)
# =============================================================================
def _get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta Authorization: Bearer <token>.")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato inválido de Authorization. Use Bearer <token>.")
    return parts[1].strip()


def _verify_google_token(token: str) -> Dict[str, Any]:
    req = google_requests.Request()
    try:
        if AUDIENCE:
            claims = id_token.verify_oauth2_token(token, req, AUDIENCE)
        else:
            # Fallback menos estricto
            claims = id_token.verify_oauth2_token(token, req)
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido o expirado: {str(e)}")


def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> Dict[str, Any]:
    token = _get_bearer_token(authorization)
    claims = _verify_google_token(token)

    email = (claims.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="El token no contiene email.")

    if not email.endswith(f"@{ALLOWED_DOMAIN}"):
        raise HTTPException(status_code=403, detail=f"Dominio @{ALLOWED_DOMAIN} requerido.")

    q = text("SELECT role FROM BWhitelist WHERE email = :email LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(q, {"email": email}).fetchone()

    if not row:
        raise HTTPException(
            status_code=403,
            detail="Usuario no autorizado. Solicita acceso para ser incluido en BWhitelist.",
        )

    role = row[0]
    if role not in ("admin", "user"):
        raise HTTPException(status_code=403, detail="Rol inválido en BWhitelist.")

    return {"email": email, "role": role, "source": "db"}


def require_role(user: Dict[str, Any], allowed: List[str]) -> None:
    if user.get("role") not in allowed:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta operación.")


# =============================================================================
# MODELOS
# =============================================================================
class TramoFinanciacion(BaseModel):
    id: Optional[str] = Field(default=None, description="id_financiacion")
    cedula: str
    fechaInicio: date
    fechaFin: date
    salario: float
    proyecto: str
    rubro: Optional[str] = None
    fuente: Optional[str] = None
    componente: Optional[str] = None
    subcomponente: Optional[str] = None
    categoria: Optional[str] = None
    responsable: Optional[str] = None


# =============================================================================
# HELPERS
# =============================================================================
def to_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            return None
    return None


def month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def mensualizar_base_30(tramos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mensualiza usando base 30 y el salario_total calculado por query (salario_t) o, si no existe,
    usa salario_base.
    """
    acc: Dict[str, Dict[str, Any]] = {}

    for tramo in tramos:
        ini = to_date(tramo.get("fecha_inicio"))
        fin = to_date(tramo.get("fecha_fin"))
        if not ini or not fin:
            continue

        salario_para_calculo = float(tramo.get("salario_t") or tramo.get("salario_base") or 0)

        cur = month_start(ini)
        last = month_start(fin)

        while cur <= last:
            is_start_month = (cur.year == ini.year and cur.month == ini.month)
            is_end_month = (cur.year == fin.year and cur.month == fin.month)

            dias = 30
            if is_start_month:
                dias = 30 - ini.day + 1
            if is_end_month:
                dias = min(dias, fin.day)
            if dias < 0:
                dias = 0

            valor_mes = round(salario_para_calculo * (dias / 30))
            key = cur.strftime("%Y-%m-01")

            if key not in acc:
                acc[key] = {"anioMes": key, "total": 0, "detalle": []}

            acc[key]["total"] += valor_mes
            acc[key]["detalle"].append(
                {
                    "id": tramo.get("id_financiacion"),
                    "contrato": tramo.get("id_contrato"),
                    "proyecto": tramo.get("id_proyecto"),
                    "rubro": tramo.get("rubro") or "",
                    "fuente": tramo.get("id_fuente") or tramo.get("fuente"),
                    "componente": tramo.get("id_componente") or tramo.get("componente"),
                    "subcomponente": tramo.get("id_subcomponente") or tramo.get("subcomponente"),
                    "categoria": tramo.get("id_categoria") or tramo.get("categoria"),
                    "responsable": tramo.get("id_responsable") or tramo.get("responsable"),
                    "valor": valor_mes,
                    "dias": dias,
                    "salarioMensual": salario_para_calculo,
                }
            )

            # siguiente mes
            if cur.month == 12:
                cur = date(cur.year + 1, 1, 1)
            else:
                cur = date(cur.year, cur.month + 1, 1)

    return sorted(acc.values(), key=lambda item: item["anioMes"])


# =============================================================================
# SQL: pago (factor) replicando AppSheet (horas ajustadas / 720)
# Nota: mantener SIN comentarios '--' dentro de la expresión para evitar 1064.
# =============================================================================
PAGO_EXPR = """
(
  (
    TIMESTAMPDIFF(HOUR, f.fecha_inicio, f.fecha_fin)
    +
    CASE
      WHEN DATE(f.fecha_fin) <> LAST_DAY(DATE(f.fecha_fin)) THEN 24
      WHEN MONTH(f.fecha_inicio) = 2 AND DAY(f.fecha_fin) = 28 THEN 72
      WHEN MONTH(f.fecha_inicio) = 2 AND DAY(f.fecha_fin) = 29 THEN 48
      WHEN MONTH(f.fecha_inicio) = 2 THEN 48
      WHEN MONTH(f.fecha_inicio) IN (4,6,9,11) THEN 24
      ELSE 0
    END
  ) / 720
)
"""


# =============================================================================
# ENDPOINTS
# =============================================================================
@app.get("/")
async def read_root():
    return {"ok": True, "service": "bosque-api"}


@app.get("/api/me")
def check_session(user: Dict[str, Any] = Depends(get_current_user)):
    return {"ok": True, "user": {"email": user["email"], "role": user["role"], "source": user["source"]}}


@app.get("/api/financiacion/{cedula}")
def obtener_financiacion(cedula: str, _user: Dict[str, Any] = Depends(get_current_user)):
    # Query con cálculo de pago en SQL (replica AppSheet) + cálculo prestacional
    query = text(f"""
    WITH CalculosBase AS (
        SELECT 
            f.id_financiacion, f.id_contrato, f.fecha_inicio, f.fecha_fin, f.id_proyecto,
            f.salario_base,
            {PAGO_EXPR} AS pago,
            f.rubro, f.id_fuente, f.id_componente, f.id_subcomponente, f.id_categoria, f.id_responsable,
            c.cargo, c.banda, c.familia, c.posicion AS posicion_c,
            i.anio, i.smlv, i.transporte, i.porcentaje_aumento, i.dotacion AS i_dotacion,

            CEILING((f.salario_base * (1 + COALESCE(i.porcentaje_aumento, 0) / 100)) / 1000) * 1000 AS salario_calc
        FROM BFinanciacion f
        LEFT JOIN BContrato c ON f.id_contrato = c.id_contrato
        LEFT JOIN BIncremento i ON YEAR(f.fecha_inicio) = i.anio
        WHERE f.cedula = :cedula
    ),
    CalculosPrestacionales AS (
        SELECT 
            *,
            CASE 
                WHEN salario_calc <= (2 * COALESCE(smlv, 0)) THEN COALESCE(transporte, 0)
                ELSE 0 
            END AS aux_transporte,
            CASE
                WHEN cargo = 'Lectiva' OR salario_calc > (COALESCE(smlv, 0) * 2) THEN 0
                ELSE CEILING(COALESCE(i_dotacion, 0) / 12) * pago
            END AS dotacion
        FROM CalculosBase
    ),
    CalculosFinales AS (
        SELECT 
            *,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                WHEN banda = 'B01' THEN 0 
                ELSE CEILING((salario_calc + aux_transporte) * 0.0834)
            END AS primas,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                ELSE CEILING(salario_calc * 0.0417) 
            END AS s_vacaciones,
            
            CASE
                WHEN cargo = 'Lectiva' THEN 0
                ELSE CEILING((salario_calc * pago) * 0.0417)
            END AS sueldo_vacaciones,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                WHEN banda = 'B01' THEN 0 
                ELSE CEILING((salario_calc + aux_transporte) * 0.0834) 
            END AS cesantias,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                WHEN banda = 'B01' THEN 0 
                ELSE CEILING((salario_calc + aux_transporte) * 0.01) 
            END AS i_cesantias,
            
            CASE
                WHEN cargo = 'Lectiva' THEN 0
                ELSE CEILING((salario_calc * pago) * 0.085)
            END AS salud,
            
            CASE
                WHEN cargo = 'Lectiva' OR posicion_c IN ('IHPO_119', 'IHPO_6ac') THEN 0
                WHEN banda = 'B01' THEN (CEILING(((salario_calc * pago * 0.7) * 0.16) / 100) * 100) - (CEILING((salario_calc * pago * 0.7)) * 0.04)
                ELSE (CEILING((salario_calc * pago * 0.16) / 100) * 100) - (CEILING(salario_calc * pago) * 0.04)
            END AS pension,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0
                WHEN banda = 'B01' THEN CEILING((salario_calc * 0.7 * 0.04)/100)*100
                ELSE CEILING((salario_calc * 0.04)/100)*100
            END AS ccf,

            CASE 
                WHEN familia = 'Aprendiz' THEN 0
                WHEN banda = 'B01' THEN CEILING((salario_calc * 0.7 * 0.02)/100)*100
                ELSE CEILING((salario_calc * 0.02)/100)*100
            END AS sena,

            CASE 
                WHEN familia = 'Aprendiz' THEN 0
                WHEN banda = 'B01' THEN CEILING((salario_calc * 0.7 * 0.03)/100)*100
                ELSE CEILING((salario_calc * 0.03)/100)*100
            END AS icbf

        FROM CalculosPrestacionales
    )
    SELECT 
        *,
        (salario_calc + aux_transporte + dotacion + primas + s_vacaciones + sueldo_vacaciones + 
         cesantias + i_cesantias + salud + pension + ccf + sena + icbf) AS salario_t
    FROM CalculosFinales;
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"cedula": cedula})
        rows = result.mappings().all()

    tramos = []
    for row in rows:
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, '__float__') and v is not None:
                d[k] = float(v)
        tramos.append(d)

    return {"ok": True, "tramos": tramos}


@app.get("/api/consulta/{cedula}")
def obtener_consulta_individual(
    cedula: str,
    _user: Dict[str, Any] = Depends(get_current_user),
):
    empleado_query = text("""
        SELECT
            cedula,
            p_nombre,
            s_nombre,
            p_apellido,
            s_apellido,
            correo_electronico
        FROM BData
        WHERE cedula = :cedula
        LIMIT 1
    """)

    contrato_query = text("""
        SELECT
            id_contrato,
            posicion,
            cargo,
            rol,
            banda,
            salario,
            nivel_riesgo,
            atep,
            direccion,
            gerencia,
            area,
            subarea,
            planta,
            tipo_contrato,
            num_contrato,
            fecha_ingreso,
            fecha_terminacion,
            prorrogas_fecha,
            estado
        FROM BContrato
        WHERE cedula = :cedula
        ORDER BY
            CASE
                WHEN estado IS NOT NULL AND LOWER(estado) LIKE '%activo%' THEN 0
                ELSE 1
            END,
            fecha_ingreso DESC
        LIMIT 1
    """)

    # Reutilizamos el mismo cálculo del endpoint financiacion para asegurar consistencia y evitar duplicación.
    tramos_query = text(f"""
    WITH CalculosBase AS (
        SELECT 
            f.id_financiacion, f.id_contrato, f.cedula,
            f.fecha_inicio, f.fecha_fin, f.id_proyecto,
            f.salario_base,
            {PAGO_EXPR} AS pago,
            f.rubro, f.id_fuente, f.id_componente, f.id_subcomponente, f.id_categoria, f.id_responsable,
            c.cargo, c.banda, c.familia, c.posicion AS posicion_c,
            i.anio, i.smlv, i.transporte, i.porcentaje_aumento, i.dotacion AS i_dotacion,

            CEILING((f.salario_base * (1 + COALESCE(i.porcentaje_aumento, 0) / 100)) / 1000) * 1000 AS salario_calc
        FROM BFinanciacion f
        LEFT JOIN BContrato c ON f.id_contrato = c.id_contrato
        LEFT JOIN BIncremento i ON YEAR(f.fecha_inicio) = i.anio
        WHERE f.cedula = :cedula
    ),
    CalculosPrestacionales AS (
        SELECT 
            *,
            CASE 
                WHEN salario_calc <= (2 * COALESCE(smlv, 0)) THEN COALESCE(transporte, 0)
                ELSE 0 
            END AS aux_transporte,
            CASE
                WHEN cargo = 'Lectiva' OR salario_calc > (COALESCE(smlv, 0) * 2) THEN 0
                ELSE CEILING(COALESCE(i_dotacion, 0) / 12) * pago
            END AS dotacion
        FROM CalculosBase
    ),
    CalculosFinales AS (
        SELECT 
            *,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                WHEN banda = 'B01' THEN 0 
                ELSE CEILING((salario_calc + aux_transporte) * 0.0834)
            END AS primas,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                ELSE CEILING(salario_calc * 0.0417) 
            END AS s_vacaciones,
            
            CASE
                WHEN cargo = 'Lectiva' THEN 0
                ELSE CEILING((salario_calc * pago) * 0.0417)
            END AS sueldo_vacaciones,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                WHEN banda = 'B01' THEN 0 
                ELSE CEILING((salario_calc + aux_transporte) * 0.0834) 
            END AS cesantias,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0 
                WHEN banda = 'B01' THEN 0 
                ELSE CEILING((salario_calc + aux_transporte) * 0.01) 
            END AS i_cesantias,
            
            CASE
                WHEN cargo = 'Lectiva' THEN 0
                ELSE CEILING((salario_calc * pago) * 0.085)
            END AS salud,
            
            CASE
                WHEN cargo = 'Lectiva' OR posicion_c IN ('IHPO_119', 'IHPO_6ac') THEN 0
                WHEN banda = 'B01' THEN (CEILING(((salario_calc * pago * 0.7) * 0.16) / 100) * 100) - (CEILING((salario_calc * pago * 0.7)) * 0.04)
                ELSE (CEILING((salario_calc * pago * 0.16) / 100) * 100) - (CEILING(salario_calc * pago) * 0.04)
            END AS pension,

            CASE 
                WHEN cargo = 'Lectiva' THEN 0
                WHEN banda = 'B01' THEN CEILING((salario_calc * 0.7 * 0.04)/100)*100
                ELSE CEILING((salario_calc * 0.04)/100)*100
            END AS ccf,

            CASE 
                WHEN familia = 'Aprendiz' THEN 0
                WHEN banda = 'B01' THEN CEILING((salario_calc * 0.7 * 0.02)/100)*100
                ELSE CEILING((salario_calc * 0.02)/100)*100
            END AS sena,

            CASE 
                WHEN familia = 'Aprendiz' THEN 0
                WHEN banda = 'B01' THEN CEILING((salario_calc * 0.7 * 0.03)/100)*100
                ELSE CEILING((salario_calc * 0.03)/100)*100
            END AS icbf

        FROM CalculosPrestacionales
    )
    SELECT 
        *,
        (salario_calc + aux_transporte + dotacion + primas + s_vacaciones + sueldo_vacaciones + 
         cesantias + i_cesantias + salud + pension + ccf + sena + icbf) AS salario_t
    FROM CalculosFinales
    ORDER BY fecha_inicio ASC;
    """)

    with engine.connect() as conn:
        empleado = conn.execute(empleado_query, {"cedula": cedula}).mappings().first()
        if not empleado:
            raise HTTPException(status_code=404, detail="No se encontró el trabajador.")

        contrato = conn.execute(contrato_query, {"cedula": cedula}).mappings().first()
        tramos_rows = conn.execute(tramos_query, {"cedula": cedula}).mappings().all()

    nombre_parts = [
        empleado.get("p_nombre"),
        empleado.get("s_nombre"),
        empleado.get("p_apellido"),
        empleado.get("s_apellido"),
    ]
    nombre = " ".join(part for part in nombre_parts if part).strip()

    # Convertimos los resultados a dict y aseguramos que tipos como Decimal sean serializables
    tramos_data = []
    for row in tramos_rows:
        d = dict(row)
        # Limpieza de tipos para JSON (Decimal -> float, date -> str)
        for k, v in d.items():
            if hasattr(v, '__float__') and v is not None: 
                d[k] = float(v)
        tramos_data.append(d)

    mensualizado = mensualizar_base_30(tramos_data)

    cabecera = None
    if contrato:
        c_dict = dict(contrato)
        # Limpieza similar para la cabecera
        for k, v in c_dict.items():
            if hasattr(v, '__float__') and v is not None:
                c_dict[k] = float(v)
        
        cabecera = {
            "CEDULA": cedula,
            "IDCONTRATO": c_dict.get("id_contrato"),
            "POSICION": c_dict.get("posicion"),
            "NOMBRE": nombre,
            "CARGO": c_dict.get("cargo"),
            "ROL": c_dict.get("rol"),
            "BANDA": c_dict.get("banda"),
            "SALARIO": c_dict.get("salario"),
            "NIVEL_RIESGO": c_dict.get("nivel_riesgo"),
            "ATEP": c_dict.get("atep"),
            "DIRECCION": c_dict.get("direccion"),
            "GERENCIA": c_dict.get("gerencia"),
            "AREA": c_dict.get("area"),
            "SUBAREA": c_dict.get("subarea"),
            "PLANTA": c_dict.get("planta"),
            "TPLANTA": c_dict.get("tipo_contrato"),
            "NUM_CONTRATO": c_dict.get("num_contrato"),
            "F_CONTRATO": c_dict.get("fecha_ingreso"),
            "F_TERMINACION": c_dict.get("fecha_terminacion"),
            "PRORROGAS": c_dict.get("prorrogas_fecha"),
        }

    return {
        "ok": True,
        "empleado": {
            "cedula": empleado["cedula"],
            "nombre": nombre,
            "correo": empleado.get("correo_electronico"),
        },
        "cabecera": cabecera,
        "tramos": tramos_data,
        "months": mensualizado,
    }


@app.post("/api/guardar")
def guardar_tramo(
    dato: TramoFinanciacion,
    user: Dict[str, Any] = Depends(get_current_user),
):
    # Si quieres que solo admin pueda editar:
    # require_role(user, ["admin"])

    if dato.fechaFin < dato.fechaInicio:
        raise HTTPException(status_code=400, detail="fechaFin no puede ser menor que fechaInicio.")

    try:
        if dato.id:
            sql = text("""
                UPDATE BFinanciacion
                SET fecha_inicio = :ini,
                    fecha_fin = :fin,
                    salario_base = :sal,
                    id_proyecto = :proy,
                    rubro = :rub,
                    id_fuente = :fue,
                    id_componente = :com,
                    id_subcomponente = :sub,
                    id_categoria = :cat,
                    id_responsable = :res
                WHERE id_financiacion = :id
            """)
            params = {
                "ini": dato.fechaInicio,
                "fin": dato.fechaFin,
                "sal": dato.salario,
                "proy": dato.proyecto,
                "rub": dato.rubro,
                "fue": dato.fuente,
                "com": dato.componente,
                "sub": dato.subcomponente,
                "cat": dato.categoria,
                "res": dato.responsable,
                "id": dato.id,
            }
        else:
            # Generar ID si es nuevo
            new_id = str(uuid.uuid4())[:12]

            sql = text("""
                INSERT INTO BFinanciacion (id_financiacion, cedula, fecha_inicio, fecha_fin, salario_base, id_proyecto, rubro, id_fuente, id_componente, id_subcomponente, id_categoria, id_responsable)
                VALUES (:id, :ced, :ini, :fin, :sal, :proy, :rub, :fue, :com, :sub, :cat, :res)
            """)
            params = {
                "id": new_id,
                "ced": dato.cedula,
                "ini": dato.fechaInicio,
                "fin": dato.fechaFin,
                "sal": dato.salario,
                "proy": dato.proyecto,
                "rub": dato.rubro,
                "fue": dato.fuente,
                "com": dato.componente,
                "sub": dato.subcomponente,
                "cat": dato.categoria,
                "res": dato.responsable,
            }

        # Transacción correcta en SQLAlchemy
        with engine.begin() as conn:
            conn.execute(sql, params)

        return {"ok": True, "mensaje": "Guardado exitoso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/borrar/{id_f}")
def eliminar_tramo(
    id_f: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    # require_role(user, ["admin"])
    try:
        sql = text("DELETE FROM BFinanciacion WHERE id_financiacion = :id")
        with engine.begin() as conn:
            conn.execute(sql, {"id": id_f})
        return {"ok": True, "mensaje": "Eliminado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
