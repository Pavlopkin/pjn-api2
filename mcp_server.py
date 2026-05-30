"""
Servidor MCP para PJN - Autenticación Bearer simple
"""
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from scraper import PJNScraper
import os

def register_mcp_routes(app: FastAPI):

    API_TOKEN = os.getenv("API_TOKEN", "cambia-este-token-secreto")
    BASE_URL = os.getenv("BASE_URL", "https://pjn-api2.onrender.com")

    @app.get("/.well-known/mcp.json")
    def mcp_manifest():
        return {
            "schema_version": "v1",
            "name": "pjn-expedientes",
            "description": "Consulta expedientes judiciales del Poder Judicial de la Nación Argentina",
            "auth": {"type": "bearer"},
            "tools": [
                {
                    "name": "buscar_expediente",
                    "description": "Busca un expediente judicial por número, año y fuero en el PJN",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "usuario":      {"type": "string", "description": "CUIL del usuario (ej: 20-12345678-9)"},
                            "password":     {"type": "string", "description": "Contraseña del portal PJN"},
                            "numero":       {"type": "string", "description": "Número de expediente (ej: 7639)"},
                            "anio":         {"type": "string", "description": "Año del expediente (ej: 2026)"},
                            "jurisdiccion": {"type": "string", "description": "Fuero: COM, CIV, CNT, CAF, CFP, CSJ", "default": "COM"}
                        },
                        "required": ["usuario", "password", "numero", "anio"]
                    },
                    "url": f"{BASE_URL}/mcp/tools/buscar_expediente"
                },
                {
                    "name": "mis_causas",
                    "description": "Lista todos los expedientes vinculados al usuario en el portal PJN",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "usuario":  {"type": "string", "description": "CUIL del usuario"},
                            "password": {"type": "string", "description": "Contraseña del portal PJN"}
                        },
                        "required": ["usuario", "password"]
                    },
                    "url": f"{BASE_URL}/mcp/tools/mis_causas"
                }
            ]
        }

    class MCPBuscarRequest(BaseModel):
        usuario: str
        password: str
        numero: str
        anio: str
        jurisdiccion: str = "COM"

    class MCPCausasRequest(BaseModel):
        usuario: str
        password: str

    @app.post("/mcp/tools/buscar_expediente")
    def mcp_buscar(req: MCPBuscarRequest, authorization: str = Header(default="")):
        token = authorization.replace("Bearer ", "")
        if token != API_TOKEN:
            return JSONResponse(status_code=401, content={"error": "Token inválido"})
        scraper = PJNScraper()
        try:
            resultado = scraper.buscar_expediente(
                usuario=req.usuario,
                password=req.password,
                numero=req.numero,
                anio=req.anio,
                jurisdiccion=req.jurisdiccion
            )
            return {"content": [{"type": "text", "text": str(resultado)}]}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})
        finally:
            scraper.cerrar()

    @app.post("/mcp/tools/mis_causas")
    def mcp_causas(req: MCPCausasRequest, authorization: str = Header(default="")):
        token = authorization.replace("Bearer ", "")
        if token != API_TOKEN:
            return JSONResponse(status_code=401, content={"error": "Token inválido"})
        scraper = PJNScraper()
        try:
            causas = scraper.obtener_mis_causas(
                usuario=req.usuario,
                password=req.password
            )
            return {"content": [{"type": "text", "text": str(causas)}]}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})
        finally:
            scraper.cerrar()
