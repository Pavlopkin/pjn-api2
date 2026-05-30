import requests
from bs4 import BeautifulSoup
import re

PORTAL_URL = "https://portalpjn.pjn.gov.ar"
SCW_URL = "https://scw.pjn.gov.ar/scw/home.seam"


class PJNScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-AR,es;q=0.9",
        })

    def cerrar(self):
        self.session.close()

    def login(self, usuario: str, password: str):
        """Hace login en el portal PJN con CUIL y contraseña."""
        # 1. GET para obtener el formulario y cookies iniciales
        r = self.session.get(PORTAL_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Buscar campos ocultos del formulario (CSRF, viewstate, etc.)
        form_data = {}
        form = soup.find("form")
        if form:
            for inp in form.find_all("input"):
                name = inp.get("name")
                value = inp.get("value", "")
                if name:
                    form_data[name] = value

        # Agregar credenciales
        form_data["username"] = usuario
        form_data["password"] = password

        # Detectar action del form
        action = form.get("action", "/login") if form else "/login"
        login_url = action if action.startswith("http") else PORTAL_URL + action

        # 2. POST de login
        r2 = self.session.post(login_url, data=form_data, timeout=15, allow_redirects=True)
        r2.raise_for_status()

        # Verificar login exitoso
        if "login" in r2.url.lower() and "error" in r2.text.lower():
            raise Exception("Login fallido: verificá tu usuario y contraseña")

        return True

    def obtener_mis_causas(self, usuario: str, password: str) -> list:
        """Obtiene las causas vinculadas al usuario autenticado."""
        self.login(usuario, password)

        r = self.session.get(f"{PORTAL_URL}/mis-expedientes", timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        causas = []
        tabla = soup.find("table")
        if tabla:
            filas = tabla.find_all("tr")[1:]  # Saltar header
            for fila in filas:
                celdas = fila.find_all("td")
                if len(celdas) >= 2:
                    causas.append({
                        "expediente": celdas[0].get_text(strip=True),
                        "caratula":   celdas[1].get_text(strip=True) if len(celdas) > 1 else "",
                        "juzgado":    celdas[2].get_text(strip=True) if len(celdas) > 2 else "",
                        "estado":     celdas[3].get_text(strip=True) if len(celdas) > 3 else "",
                    })

        if not causas:
            raise Exception("No se encontraron causas o la sesión expiró")

        return causas

    def buscar_expediente(self, usuario: str, password: str,
                          numero: str, anio: str, jurisdiccion: str = "COM") -> dict:
        """Busca un expediente en el SCW (con sesión autenticada)."""
        self.login(usuario, password)

        # 1. GET del formulario SCW para obtener viewstate JSF
        r = self.session.get(SCW_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        form_data = {}
        for inp in soup.find_all("input", {"type": ["hidden", "text", "submit"]}):
            name = inp.get("name")
            value = inp.get("value", "")
            if name:
                form_data[name] = value

        # Campos de búsqueda (los IDs reales del SCW)
        form_data.update({
            "j_idt93:jurisdiccion": jurisdiccion,
            "j_idt93:numero": numero,
            "j_idt93:anio": anio,
            "j_idt93:j_idt121": "Consultar",  # botón submit
        })

        # 2. POST de búsqueda
        r2 = self.session.post(SCW_URL, data=form_data, timeout=20,
                               headers={"Faces-Request": "partial/ajax"})
        r2.raise_for_status()

        return self._parsear_resultado(r2.text)

    def _parsear_resultado(self, html: str) -> dict:
        """Extrae los datos del expediente del HTML de resultados."""
        soup = BeautifulSoup(html, "html.parser")

        resultado = {
            "expediente": "",
            "caratula": "",
            "jurisdiccion": "",
            "dependencia": "",
            "actuaciones": []
        }

        # Datos generales: buscar etiquetas con texto clave
        texto_completo = soup.get_text(" ", strip=True)

        def extraer_campo(patron):
            m = re.search(patron, texto_completo, re.IGNORECASE)
            return m.group(1).strip() if m else ""

        resultado["expediente"]  = extraer_campo(r"Expediente[:\s]+([A-Z]+\s*\d+/\d+)")
        resultado["caratula"]    = extraer_campo(r"Car[áa]tula[:\s]+(.+?)(?:Jurisdicci|Dependencia|$)")
        resultado["jurisdiccion"]= extraer_campo(r"Jurisdicci[óo]n[:\s]+(.+?)(?:Dependencia|Car|$)")
        resultado["dependencia"] = extraer_campo(r"Dependencia[:\s]+(.+?)(?:Car|Jurisd|$)")

        # Actuaciones de la tabla
        for tabla in soup.find_all("table"):
            filas = tabla.find_all("tr")[1:]
            for fila in filas:
                celdas = fila.find_all("td")
                if len(celdas) >= 3:
                    resultado["actuaciones"].append({
                        "oficina":     celdas[0].get_text(strip=True),
                        "fecha":       celdas[1].get_text(strip=True),
                        "tipo":        celdas[2].get_text(strip=True),
                        "descripcion": celdas[3].get_text(strip=True) if len(celdas) > 3 else "",
                    })

        if not resultado["expediente"] and not resultado["actuaciones"]:
            resultado["nota"] = "No se encontraron datos. Verificá número, año y jurisdicción."

        return resultado
