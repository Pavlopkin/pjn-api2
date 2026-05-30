"""
Servidor MCP (Model Context Protocol) para PJN
Compatible con el flujo OAuth de Claude.ai
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel
from scraper import PJNScraper
import os

def register_mcp_routes(app: FastAPI):

    API_TOKEN = os.getenv("API_TOKEN", "cambia-este-token-secreto")
    BASE_URL = os.getenv("BASE_URL", "https://pjn-api2.onrender.com")

    # ─── OAuth endpoints que Claude.ai requiere ───────────────────────────────

    @app.get("/authorize")
    def authorize(
        response_type: str = "",
        client_id: str = "",
        redirect_uri: str = "",
        code_challenge: str = "",
        code_challenge_method: str = "",
        state: str = ""
    ):
        """
        Claude llama a este endpoint para iniciar el flujo OAuth.
        Como usamos token fijo, mostramos una página simple de confirmación.
        """
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>PJN API - Autorizar acceso</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 80px auto; padding: 20px; }}
                h2 {{ color: #1a1a2e; }}
                .btn {{ background: #4CAF50; color: white; padding: 12px 24px; border: none;
                        border-radius: 6px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; }}
                .info {{ background: #f0f4ff; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h2>🏛️ PJN API — Autorizar acceso a Claude</h2>
            <div class="info">
                <p>Claude quiere acceder a tus expedientes judiciales del PJN.</p>
                <p>Al confirmar, Claude podrá consultar expedientes usando tu token de API.</p>
            </div>
            <a class="btn" href="{redirect_uri}?code={API_TOKEN}&state={state}">
                ✅ Autorizar acceso
            </a>
        </body>
        </html>
        """
        return HTMLResponse(content=html)

    @app.post("/token")
    async def token(request: Request):
        """Intercambia el código por un access token."""
        body = await request.form()
        code = body.get("code", "")
        return {
            "access_token": code,
            "token_type": "bearer",
            "expires_in": 86400
        }

    # ─── Manifiesto MCP ───────────────────────────────────────────────────────

    @app.get("/.well-known/mcp.json")
    def mcp_manifest():
        return {
            "schema_version": "v1",
            "name": "pjn-expedientes",
            "description": "Consulta expedientes judiciales del Poder Judicial de la Nación Argentina",
            "auth": {
                "type": "oauth2",
                "authorization_url": f"{BASE_URL}/authorize",
                "token_url": f"{BASE_URL}/token",
                "client_id": API_TOKEN,
                "scopes": []
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

    # ─── Herramientas MCP ─────────────────────────────────────────────────────

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
