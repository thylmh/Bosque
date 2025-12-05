# schemas_contratos.py
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ContratoBase(BaseModel):
    id_contrato: str
    cedula: str
    id_posicion: Optional[str] = None
    familia: Optional[str] = None
    cargo: Optional[str] = None
    rol: Optional[str] = None
    banda: Optional[str] = None
    salario: Optional[float] = None
    nivel_riesgo: Optional[str] = None
    atep: Optional[str] = None
    direccion: Optional[str] = None
    gerencia: Optional[str] = None
    area: Optional[str] = None
    subarea: Optional[str] = None
    tipo_contrato: Optional[str] = None
    numero_contrato: Optional[str] = None
    f_contrato: Optional[date] = None
    numero_otrosi: Optional[str] = None
    prorrogas: Optional[str] = None
    f_ingreso: Optional[date] = None
    f_terminacion_contrato: Optional[date] = None
    modalidad_teletrabajo: Optional[str] = None
    total_dias_teletrabajo: Optional[int] = None
    sede: Optional[str] = None
    ciudad_contratacion: Optional[str] = None
    estado: Optional[str] = None
    metodo_seleccion: Optional[str] = None
    encargo: Optional[str] = None
    motivo_ingreso: Optional[str] = None
    fecha_termi: Optional[date] = None
    causal_retiro: Optional[str] = None
    usuario: Optional[str] = None


class ContratoCreate(ContratoBase):
    pass


class ContratoUpdate(BaseModel):
    salario: Optional[float] = None
    estado: Optional[str] = None
    causal_retiro: Optional[str] = None
    usuario: Optional[str] = None


class ContratoOut(ContratoBase):
    model_config = ConfigDict(from_attributes=True)
