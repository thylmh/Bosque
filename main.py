import os
from datetime import date
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from google.cloud.sql.connector import Connector

app = FastAPI()

ALLOWED_DOMAIN = os.environ.get("ALLOWED_DOMAIN", "humboldt.org.co").lower()
ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.environ.get(
        "ADMIN_EMAILS",
        "rbetancur@humboldt.org.co,aplicaciones@humboldt.org.co, "
        "hbettin@humboldt.org.co",
    ).split(",")
    if email.strip()
}

cors_origins_raw = os.environ.get("CORS_ORIGINS", "*")
if cors_origins_raw.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. CONEXIÓN A CLOUD SQL ---
def getconn():
    connector = Connector()
    conn = connector.connect(
        "bosque-485105:southamerica-east1:bosquebd", # Tu instancia
        "pymysql",
        user="root",
        password=os.environ.get("DB_PASS", ";pFp:E>9o=h\"KbBy"),
        db="nominas_db"
    )
    return conn

engine = create_engine("mysql+pymysql://", creator=getconn)

# --- 2. MODELOS DE DATOS ---
class TramoFinanciacion(BaseModel):
    id: str | None = None
    cedula: str
    fechaInicio: str
    fechaFin: str
    salario: float
    proyecto: str


def get_current_user(
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
) -> dict[str, Any]:
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Falta el correo de usuario.")
    email = x_user_email.strip().lower()
    if not email.endswith(f"@{ALLOWED_DOMAIN}"):
        raise HTTPException(status_code=403, detail="Dominio no autorizado.")
    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Usuario no autorizado.")
    return {"email": email, "role": "admin"}


def month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def mensualizar_base_30(tramos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    acc: dict[str, dict[str, Any]] = {}
    for tramo in tramos:
        if not tramo.get("fecha_inicio") or not tramo.get("fecha_fin"):
            continue

        ini = tramo["fecha_inicio"]
        fin = tramo["fecha_fin"]
        salario_para_calculo = float(tramo.get("salario_t") or tramo.get("salario_base") or 0)

        cur = month_start(ini)
        last = month_start(fin)

        while cur <= last:
            is_start_month = cur.year == ini.year and cur.month == ini.month
            is_end_month = cur.year == fin.year and cur.month == fin.month

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
                    "fuente": tramo.get("id_fuente"),
                    "componente": tramo.get("id_componente"),
                    "subcomponente": tramo.get("id_subcomponente"),
                    "categoria": tramo.get("id_categoria"),
                    "responsable": tramo.get("id_responsable"),
                    "valor": valor_mes,
                    "dias": dias,
                    "salarioMensual": salario_para_calculo,
                }
            )

            if cur.month == 12:
                cur = date(cur.year + 1, 1, 1)
            else:
                cur = date(cur.year, cur.month + 1, 1)

    return sorted(acc.values(), key=lambda item: item["anioMes"])

# --- 3. API Y CÁLCULOS DE NÓMINA ---

@app.get("/")
async def read_root():
    return {"ok": True, "service": "bosque-api"}

@app.get("/api/financiacion/{cedula}")
def obtener_financiacion(cedula: str, _user: dict[str, Any] = Depends(get_current_user)):
    # Esta consulta traduce tus fórmulas de AppSheet a SQL
    query = text("""
    WITH CalculosBase AS (
        SELECT 
            f.id_financiacion, f.fecha_inicio, f.fecha_fin, f.id_proyecto,
            f.salario_base,
            c.cargo, c.banda, c.familia,
            i.anio, i.smlv, i.transporte, i.porcentaje_aumento,
            
            -- BASE 1: Salario Mensual Calculado (Redondeado a 1000 como en AppSheet)
            -- Asumimos que AUMENTO viene como 105.00 (porcentaje), por eso dividimos por 100.
            CEILING((f.salario_base * (i.porcentaje_aumento / 100)) / 1000) * 1000 AS Salario_Calc
            
        FROM BFinanciacion f
        LEFT JOIN BContrato c ON f.cedula = c.cedula
        LEFT JOIN BIncremento i ON YEAR(f.fecha_inicio) = i.anio
        WHERE f.cedula = :cedula
    ),
    CalculosPrestacionales AS (
        SELECT 
            *,
            -- AUXILIO DE TRANSPORTE (Regla general: Si salario <= 2 SMLV)
            CASE 
                WHEN Salario_Calc <= (2 * smlv) THEN transporte 
                ELSE 0 
            END AS Aux_Transporte
        FROM CalculosBase
    ),
    CalculosFinales AS (
        SELECT 
            *,
            -- PRIMA DE SERVICIOS (Formula: PrimaS)
            CASE 
                WHEN Cargo = 'Lectiva' THEN 0 
                WHEN Banda = 'B01' THEN 0 
                ELSE CEILING((Salario_Calc + Aux_Transporte) * 0.0834)
            END AS PrimaS,

            -- VACACIONES (Formula: SVacaciones)
            CASE 
                WHEN Cargo = 'Lectiva' THEN 0 
                ELSE CEILING(Salario_Calc * 0.0417) 
            END AS SVacaciones,

            -- CESANTIAS (Formula: Cesantias)
            CASE 
                WHEN Cargo = 'Lectiva' THEN 0 
                WHEN Banda = 'B01' THEN 0 
                ELSE CEILING((Salario_Calc + Aux_Transporte) * 0.0834) 
            END AS Cesantias,

            -- INTERESES CESANTIAS (Formula: ICesantias)
            CASE 
                WHEN Cargo = 'Lectiva' THEN 0 
                WHEN Banda = 'B01' THEN 0 
                ELSE CEILING((Salario_Calc + Aux_Transporte) * 0.01) 
            END AS ICesantias,

            -- CAJA DE COMPENSACION (Formula: CCF)
            CASE 
                WHEN Cargo = 'Lectiva' THEN 0
                WHEN Banda = 'B01' THEN CEILING((Salario_Calc * 0.7 * 0.04)/100)*100
                ELSE CEILING((Salario_Calc * 0.04)/100)*100
            END AS CCF,

            -- SENA (Formula: SENA)
            CASE 
                WHEN Familia = 'Aprendiz' THEN 0
                WHEN Banda = 'B01' THEN CEILING((Salario_Calc * 0.7 * 0.02)/100)*100
                ELSE CEILING((Salario_Calc * 0.02)/100)*100
            END AS SENA,

            -- ICBF (Formula: ICBF)
            CASE 
                WHEN Familia = 'Aprendiz' THEN 0
                WHEN Banda = 'B01' THEN CEILING((Salario_Calc * 0.7 * 0.03)/100)*100
                ELSE CEILING((Salario_Calc * 0.03)/100)*100
            END AS ICBF

        FROM CalculosPrestacionales
    )
    -- SELECCION FINAL CON EL TOTAL SUMADO
    SELECT 
        *,
        (Salario_Calc + Aux_Transporte + PrimaS + SVacaciones + Cesantias + ICesantias + CCF + SENA + ICBF) AS salario_t
    FROM CalculosFinales;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"cedula": cedula})
        tramos = [dict(row._mapping) for row in result]
        
    return {"ok": True, "tramos": tramos}


@app.get("/api/consulta/{cedula}")
def obtener_consulta_individual(
    cedula: str,
    _user: dict[str, Any] = Depends(get_current_user),
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
    tramos_query = text("""
        SELECT
            id_financiacion,
            id_contrato,
            posicion,
            cedula,
            fecha_inicio,
            fecha_fin,
            salario_base,
            salario_t,
            rubro,
            id_proyecto,
            id_fuente,
            id_componente,
            id_subcomponente,
            id_categoria,
            id_responsable
        FROM BFinanciacion
        WHERE cedula = :cedula
        ORDER BY fecha_inicio ASC
    """)

    with engine.connect() as conn:
        empleado = conn.execute(empleado_query, {"cedula": cedula}).mappings().first()
        if not empleado:
            raise HTTPException(status_code=404, detail="No se encontró el trabajador.")

        contrato = conn.execute(contrato_query, {"cedula": cedula}).mappings().first()
        tramos = conn.execute(tramos_query, {"cedula": cedula}).mappings().all()

    nombre_parts = [
        empleado.get("p_nombre"),
        empleado.get("s_nombre"),
        empleado.get("p_apellido"),
        empleado.get("s_apellido"),
    ]
    nombre = " ".join(part for part in nombre_parts if part).strip()

    tramos_data = [dict(tramo) for tramo in tramos]
    mensualizado = mensualizar_base_30(tramos_data)

    cabecera = None
    if contrato:
        cabecera = {
            "CEDULA": contrato.get("cedula", cedula),
            "IDCONTRATO": contrato.get("id_contrato"),
            "POSICION": contrato.get("posicion"),
            "NOMBRE": nombre,
            "CARGO": contrato.get("cargo"),
            "ROL": contrato.get("rol"),
            "BANDA": contrato.get("banda"),
            "SALARIO": contrato.get("salario"),
            "NIVEL_RIESGO": contrato.get("nivel_riesgo"),
            "ATEP": contrato.get("atep"),
            "DIRECCION": contrato.get("direccion"),
            "GERENCIA": contrato.get("gerencia"),
            "AREA": contrato.get("area"),
            "SUBAREA": contrato.get("subarea"),
            "TPLANTA": contrato.get("tipo_contrato"),
            "NUM_CONTRATO": contrato.get("num_contrato"),
            "F_CONTRATO": contrato.get("fecha_ingreso"),
            "F_TERMINACION": contrato.get("fecha_terminacion"),
            "PRORROGAS": contrato.get("prorrogas_fecha"),
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
    _user: dict[str, Any] = Depends(get_current_user),
):
    try:
        with engine.connect() as conn:
            if dato.id:
                sql = text(
                    """
                    UPDATE BFinanciacion
                    SET fecha_inicio = :ini,
                        fecha_fin = :fin,
                        salario_base = :sal,
                        id_proyecto = :proy
                    WHERE id_financiacion = :id
                    """
                )
                conn.execute(
                    sql,
                    {
                        "ini": dato.fechaInicio,
                        "fin": dato.fechaFin,
                        "sal": dato.salario,
                        "proy": dato.proyecto,
                        "id": dato.id,
                    },
                )
            else:
                sql = text(
                    """
                    INSERT INTO BFinanciacion (cedula, fecha_inicio, fecha_fin, salario_base, id_proyecto)
                    VALUES (:ced, :ini, :fin, :sal, :proy)
                    """
                )
                conn.execute(
                    sql,
                    {
                        "ced": dato.cedula,
                        "ini": dato.fechaInicio,
                        "fin": dato.fechaFin,
                        "sal": dato.salario,
                        "proy": dato.proyecto,
                    },
                )
            conn.commit()
            return {"ok": True, "mensaje": "Guardado exitoso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
