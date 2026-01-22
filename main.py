import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from google.cloud.sql.connector import Connector

app = FastAPI()

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
    id: str = None
    cedula: str
    fechaInicio: str
    fechaFin: str
    salario: float
    proyecto: str

# --- 3. API Y CÁLCULOS DE NÓMINA ---

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/api/financiacion/{cedula}")
def obtener_financiacion(cedula: str):
    # Esta consulta traduce tus fórmulas de AppSheet a SQL
    query = text("""
    WITH CalculosBase AS (
        SELECT 
            f.IDFinanciacion, f.Start_Date, f.End_Date, f.IdProyectos,
            c.Cargo, c.Banda, c.Familia,
            i.YEAR, i.SMLV, i.TRANSPORTE, 
            
            -- BASE 1: Salario Mensual Calculado (Redondeado a 1000 como en AppSheet)
            -- Asumimos que AUMENTO viene como 105.00 (porcentaje), por eso dividimos por 100.
            CEILING((f.Salario * (i.AUMENTO / 100)) / 1000) * 1000 AS Salario_Calc
            
        FROM BFinanciacion f
        LEFT JOIN BContrato c ON f.Cédula = c.Cédula
        LEFT JOIN BIncremento i ON YEAR(f.Start_Date) = i.YEAR
        WHERE f.Cédula = :cedula
    ),
    CalculosPrestacionales AS (
        SELECT 
            *,
            -- AUXILIO DE TRANSPORTE (Regla general: Si salario <= 2 SMLV)
            CASE 
                WHEN Salario_Calc <= (2 * SMLV) THEN TRANSPORTE 
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
        (Salario_Calc + Aux_Transporte + PrimaS + SVacaciones + Cesantias + ICesantias + CCF + SENA + ICBF) AS SalarioT
    FROM CalculosFinales;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"cedula": cedula})
        tramos = [dict(row._mapping) for row in result]
        
    return {"ok": True, "tramos": tramos}

@app.post("/api/guardar")
def guardar_tramo(dato: TramoFinanciacion):
    try:
        with engine.connect() as conn:
            if dato.id:
                sql = text("UPDATE BFinanciacion SET Start_Date=:ini, End_Date=:fin, Salario=:sal, IdProyectos=:proy WHERE IDFinanciacion=:id")
                conn.execute(sql, {"ini": dato.fechaInicio, "fin": dato.fechaFin, "sal": dato.salario, "proy": dato.proyecto, "id": dato.id})
            else:
                sql = text("INSERT INTO BFinanciacion (Cédula, Start_Date, End_Date, Salario, IdProyectos) VALUES (:ced, :ini, :fin, :sal, :proy)")
                conn.execute(sql, {"ced": dato.cedula, "ini": dato.fechaInicio, "fin": dato.fechaFin, "sal": dato.salario, "proy": dato.proyecto})
            conn.commit()
            return {"ok": True, "mensaje": "Guardado exitoso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/static", StaticFiles(directory="static"), name="static")