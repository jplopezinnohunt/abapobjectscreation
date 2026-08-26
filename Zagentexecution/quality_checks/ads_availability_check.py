"""
ads_availability_check.py — ¿RESPONDE Adobe Document Services? El monitor que este canal nunca tuvo.

POR QUE EXISTE
--------------
INC-000016471 (2026-08-25): "Create PDF Agreement" devuelve
    500 Internal Server Error / ADS: SOAP Runtime Exception: CSoapExceptionTransport :(100101)
y nadie podia decir si ADS estaba vivo. El canal ADS estaba catalogado `NO_MEDIBLE` en
brain_v2/interface_inventory.json, con esta justificacion (correcta, y a medias):

    "un destino SALIENTE no registra en nuestro log que hace en el sistema destino.
     Se mediria en el otro extremo. Ausencia de dato, no de riesgo."

Eso es cierto del TRAFICO y FALSO de la DISPONIBILIDAD. "¿Que hace ADS?" se mide en el otro
extremo; "¿RESPONDE ADS?" se contesta desde aqui, con una peticion. Por confundir las dos
preguntas, el canal por el que sale TODO PDF de la institucion se quedo sin vigilancia — y el dia
que se rompio hubo que reconstruir a mano donde vivia, quien era su usuario y en que maquina
corria. Medido entonces: 43-50 formularios Adobe propios (convenio de practicas, contratos de
personal, attestations, PAF, cartas de dunning de FI, contratos y facturas de RE-FX).

QUE DEMUESTRA, Y COMO
---------------------
Hace UNA peticion HTTP SIN CREDENCIALES al endpoint del servlet. La respuesta discrimina las dos
causas que quedaron vivas tras refutar la caida de maquina con el latido de SolMan:

    401 / 403          -> el servlet ESTA ARRIBA y pide autenticacion.
                          => la aplicacion ADS corre; el problema es la CREDENCIAL (ADSUSER en el
                             UME de Java). Es el mismo veredicto que da SM59 -> Connection Test.
    200                -> el servlet responde sin autenticacion. ADS arriba.
    404                -> el puerto responde pero la aplicacion NO esta desplegada/arrancada.
    ConnectionRefused  -> nada escucha en ese puerto: instancia Java parada.
    Timeout            -> ruta de red / firewall, o Java sin recursos.
    DNS                -> el host no resuelve desde aqui.

NO ENVIA CREDENCIALES. Nunca. Un 401 es un RESULTADO, no un fallo que haya que reintentar
autenticado: es precisamente la prueba de que el servlet vive. Introducir la contrasena de un
usuario de servicio esta prohibido y ademas no haria falta.

AVISO SOBRE EL CANAL: el destino esta configurado con s=N — HTTP PLANO, sin SSL. Este script no
empeora nada (no manda secretos), pero deja constancia: cada render real de PDF manda la
contrasena de ADSUSER por la red sin cifrar.

FUENTE DE LOS PARAMETROS
------------------------
Gold DB, tabla `rfcdes`, destino `ADS` (tipo G):
    H=hq-sap-sbp.hq.int.unesco.org  I=50300  N=/AdobeDocumentServices/Config?style=rpc
    D=ADSUSER  Q=B (basic)  s=N (sin SSL)  T=N (traza apagada)
`hq-sap-sbp` = Solution Manager de produccion (SBP), IP 172.16.4.107. Misma maquina: instancia
ABAP 01 (SolMan) + instancia Java 03 (puerto 50300, ADS). Es el UNICO AS Java de aplicacion del
paisaje: sin respaldo y sin failover.

USO
---
    python Zagentexecution/quality_checks/ads_availability_check.py
    python Zagentexecution/quality_checks/ads_availability_check.py --host X --port N --path /P
    python Zagentexecution/quality_checks/ads_availability_check.py --json

SALIDA: exit 0 = ADS responde (servlet arriba) · exit 1 = ADS NO responde · exit 2 = indeterminado.
"""
import argparse
import http.client
import json
import socket
import ssl
import sys
import datetime

# Valores por defecto = los del destino RFC `ADS` medido en el Gold DB (tabla rfcdes).
DEFAULT_HOST = "hq-sap-sbp.hq.int.unesco.org"
DEFAULT_PORT = 50300
DEFAULT_PATH = "/AdobeDocumentServices/Config?style=rpc"
DEFAULT_TIMEOUT = 10.0


def probe(host, port, path, timeout, use_ssl=False):
    """Una peticion GET SIN CREDENCIALES. Devuelve un veredicto estructurado."""
    started = datetime.datetime.now()
    out = {
        "host": host, "port": port, "path": path,
        "timestamp": started.isoformat(timespec="seconds"),
        "credentials_sent": False,
    }

    # Resolucion de nombre aparte: un fallo de DNS no es un fallo de la aplicacion.
    try:
        out["resolved_ip"] = socket.gethostbyname(host)
    except socket.gaierror as e:
        out.update(verdict="DNS_FAIL", ads_up=None, exit=2,
                   detail="el host no resuelve desde esta maquina: %s" % e)
        return out

    try:
        cls = http.client.HTTPSConnection if use_ssl else http.client.HTTPConnection
        kw = {"timeout": timeout}
        if use_ssl:
            kw["context"] = ssl._create_unverified_context()
        conn = cls(host, port, **kw)
        conn.request("GET", path, headers={"User-Agent": "unesco-ads-availability-check/1.0"})
        resp = conn.getresponse()
        body = resp.read(2048)
        conn.close()
    except socket.timeout:
        out.update(verdict="TIMEOUT", ads_up=False, exit=1,
                   detail="el puerto no contesto en %.0fs: ruta de red/firewall, o Java sin "
                          "recursos" % timeout)
        return out
    except ConnectionRefusedError:
        out.update(verdict="CONNECTION_REFUSED", ads_up=False, exit=1,
                   detail="nada escucha en %s:%d -- la instancia Java esta parada" % (host, port))
        return out
    except OSError as e:
        out.update(verdict="NETWORK_ERROR", ads_up=None, exit=2,
                   detail="%s: %s" % (type(e).__name__, e))
        return out

    out["elapsed_s"] = round((datetime.datetime.now() - started).total_seconds(), 3)
    out["http_status"] = resp.status
    out["http_reason"] = resp.reason
    out["www_authenticate"] = resp.getheader("WWW-Authenticate")
    out["server"] = resp.getheader("Server")
    out["body_head"] = body[:400].decode("utf-8", "replace").strip()

    if resp.status in (401, 403):
        out.update(verdict="UP_AUTH_REQUIRED", ads_up=True, exit=0,
                   detail="el servlet ESTA ARRIBA y pide autenticacion. La aplicacion ADS corre "
                          "=> si el PDF falla, la causa es la CREDENCIAL (ADSUSER en el UME de "
                          "Java), no la disponibilidad.")
    elif resp.status == 404:
        out.update(verdict="PORT_UP_APP_NOT_DEPLOYED", ads_up=False, exit=1,
                   detail="el puerto responde pero la aplicacion no esta desplegada o arrancada "
                          "en esa ruta.")
    elif 200 <= resp.status < 400:
        out.update(verdict="UP", ads_up=True, exit=0,
                   detail="el servlet responde. ADS esta arriba.")
    elif resp.status >= 500:
        out.update(verdict="UP_BUT_ERRORING", ads_up=True, exit=1,
                   detail="el servlet responde pero devuelve error de servidor: la aplicacion "
                          "esta desplegada y rota.")
    else:
        out.update(verdict="UNEXPECTED_%d" % resp.status, ads_up=None, exit=2,
                   detail="codigo no contemplado; leer body_head.")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--path", default=DEFAULT_PATH)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--ssl", action="store_true", help="usar HTTPS (el destino real es s=N: HTTP plano)")
    ap.add_argument("--json", action="store_true", help="salida JSON para encadenar")
    a = ap.parse_args()

    r = probe(a.host, a.port, a.path, a.timeout, a.ssl)

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return r["exit"]

    print("=" * 74)
    print("ADS AVAILABILITY CHECK  --  %s" % r["timestamp"])
    print("=" * 74)
    print("  endpoint : http%s://%s:%d%s" % ("s" if a.ssl else "", r["host"], r["port"], r["path"]))
    print("  ip       : %s" % r.get("resolved_ip", "-"))
    print("  credenciales enviadas: NO (un 401 es el RESULTADO que buscamos, no un fallo)")
    print("-" * 74)
    if "http_status" in r:
        print("  HTTP %s %s   (%.3fs)" % (r["http_status"], r["http_reason"], r.get("elapsed_s", 0)))
        if r.get("server"):
            print("  Server: %s" % r["server"])
        if r.get("www_authenticate"):
            print("  WWW-Authenticate: %s" % r["www_authenticate"])
        if r.get("body_head"):
            print("  body: %s" % r["body_head"][:300].replace("\n", " "))
    print("-" * 74)
    print("  VEREDICTO : %s" % r["verdict"])
    print("  ADS ARRIBA: %s" % {True: "SI", False: "NO", None: "INDETERMINADO"}[r["ads_up"]])
    print("  %s" % r["detail"])
    print("=" * 74)
    return r["exit"]


if __name__ == "__main__":
    sys.exit(main())
