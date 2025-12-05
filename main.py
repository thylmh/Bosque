# main.py
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from routers import empleados as empleados_router
from routers import contratos as contratos_router

app = FastAPI(
    title="ERP Talento Humano - Bosque",
    version="0.1.0",
)

# Crea las tablas en la BD si no existen
Base.metadata.create_all(bind=engine)

# Incluir rutas de contratos y empleados
app.include_router(contratos_router.router)
app.include_router(empleados_router.router)


@app.get("/")
def root():
    return {"mensaje": "ERP Talento Humano API en funcionamiento"}


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    """
    Prueba simple de conexion a la base de datos.
    """
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_ok": True, "result": result}
