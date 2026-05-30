from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from scraper import PJNScraper
import os

app = FastAPI(
    title="PJN API",
    description="API para consultar expedientes judiciales del Poder Judicial de la Nación",
    version="1.0.0"
)

security = HTTPBearer()

# Token de seguridad para proteger tu API (se configura en Railway como variable de entorno)
API_TOKEN = os.getenv("API_TOKEN", "cambia-este-token-secreto")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")
    return credentials.credentials


class LoginRequest(BaseModel):
    usuario: str
    password: str


class ExpedienteRequest(BaseModel):
    usuario: str
    password: str
    numero: str  # Ej: "7639"
    anio: str    # Ej: "2026"
    jurisdiccion: str = "COM"  # COM, CIV, CNT, etc.


@app.get("/")
def root():
    return {"status": "ok", "message": "PJN API funcionando"}


@app.post("/expedientes/buscar")
def buscar_expediente(req: ExpedienteRequest, token: str = Depends(verify_token)):
    """
    Busca un expediente judicial en el portal PJN autenticado.
    """
    scraper = PJNScraper()
    try:
        resultado = scraper.buscar_expediente(
            usuario=req.usuario,
            password=req.password,
            numero=req.numero,
            anio=req.anio,
            jurisdiccion=req.jurisdiccion
        )
        return {"ok": True, "expediente": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.cerrar()


@app.post("/expedientes/mis-causas")
def mis_causas(req: LoginRequest, token: str = Depends(verify_token)):
    """
    Obtiene todos los expedientes vinculados al usuario autenticado.
    """
    scraper = PJNScraper()
    try:
        causas = scraper.obtener_mis_causas(
            usuario=req.usuario,
            password=req.password
        )
        return {"ok": True, "causas": causas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        scraper.cerrar()
