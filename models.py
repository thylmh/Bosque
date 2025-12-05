# models.py
from sqlalchemy import (
    Column,
    String,
    Date,
    TIMESTAMP,
    Numeric,
    Integer,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


# =========================
# EMPLEADO
# =========================
class Empleado(Base):
    __tablename__ = "empleados"

    cedula = Column(String(20), primary_key=True, index=True)
    p_apellido = Column(String(100))
    s_apellido = Column(String(100))
    p_nombre = Column(String(100))
    s_nombre = Column(String(100))
    correo_electronico = Column(String(150))
    telefono = Column(String(50))
    fecha_nacimiento = Column(Date)
    genero = Column(String(50))
    estado_civil = Column(String(50))
    tipo_sangre = Column(String(50))
    gestacion = Column(String(50))
    direccion_residencia = Column(String(200))
    barrio_localidad = Column(String(200))
    departamento_residencia = Column(String(200))
    ciudad_residencia = Column(String(200))
    usuario = Column(String(100))
    modificacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relacion 1:N con contratos
    contratos = relationship("Contrato", back_populates="empleado")


# =========================
# POSICION
# =========================
class Posicion(Base):
    __tablename__ = "posiciones"

    id_posicion = Column(String(50), primary_key=True, index=True)
    salario = Column(Numeric(18, 2))
    familia = Column(String(100))
    cargo = Column(String(150))
    rol = Column(String(150))
    banda = Column(String(100))
    direccion = Column(String(200))
    gerencia = Column(String(200))
    area = Column(String(200))
    subarea = Column(String(200))
    planta = Column(String(150))
    tipo_planta = Column(String(150))
    base_fuente = Column(String(150))
    estado = Column(String(50))
    p_jefe = Column(String(50))
    observacion = Column(String)
    usuario = Column(String(100))
    modificacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relacion 1:N con contratos
    contratos = relationship("Contrato", back_populates="posicion")


# =========================
# CONTRATO
# =========================
class Contrato(Base):
    __tablename__ = "contratos"

    id_contrato = Column(String, primary_key=True, index=True)
    cedula = Column(String, ForeignKey("empleados.cedula"), nullable=False)
    id_posicion = Column(String, ForeignKey("posiciones.id_posicion"), nullable=True)

    familia = Column(String)
    cargo = Column(String)
    rol = Column(String)
    banda = Column(String)
    salario = Column(Numeric(18, 2))
    nivel_riesgo = Column(String)
    atep = Column(String)
    direccion = Column(String)
    gerencia = Column(String)
    area = Column(String)
    subarea = Column(String)
    tipo_contrato = Column(String)
    numero_contrato = Column(String)
    f_contrato = Column(Date)
    numero_otrosi = Column(String)
    prorrogas = Column(String)
    f_ingreso = Column(Date)
    f_terminacion_contrato = Column(Date)
    modalidad_teletrabajo = Column(String)
    total_dias_teletrabajo = Column(Integer)
    sede = Column(String)
    ciudad_contratacion = Column(String)
    estado = Column(String)
    metodo_seleccion = Column(String)
    encargo = Column(String)
    motivo_ingreso = Column(String)
    fecha_termi = Column(Date)
    causal_retiro = Column(String)
    usuario = Column(String(100))
    modificacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones ORM
    empleado = relationship("Empleado", back_populates="contratos")
    posicion = relationship("Posicion", back_populates="contratos")
