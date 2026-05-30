"""
Servidor MCP (Model Context Protocol) para PJN
Permite a Claude consultar expedientes judiciales directamente
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from scraper import PJNScraper
import os

# Se monta en la misma app de main.py
def register_mcp_routes(app: FastAPI):

    @app.get("/.well-known/mcp.json")
    def mcp_manifest():
        """Manifiesto MCP que Claude lee para descubrir las herramientas."""
        base_url = os.getenv("BASE_URL", "https://pjn-api2.onrender.com")
        return {
            "schema_version": "v1",
            "name": "pjn-expedientes",
            "description": "Consulta expedientes judiciales del Poder Judicial de la Nación Argentina",
            "auth": {
                "type": "bearer",
                "instructions": "Usá el API_TOKEN configurado en el servidor"
            },
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
                    "url": f"{base_url}/mcp/tools/buscar_expediente"
                },
                {
                    "name": "mis_causas",
                    "description": "Obtiene todos los expedientes vinculados al usuario en el portal PJN",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "usuario":  {"type": "string", "description": "CUIL del usuario"},
                            "password": {"type": "string", "description": "Contraseña del portal PJN"}
                        },
                        "required": ["usuario", "password"]
                    },
                    "url": f"{base_url}/mcp/tools/mis_causas"
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
    def mcp_buscar(req: MCPBuscarRequest):
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
    def mcp_causas(req: MCPCausasRequest):
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
