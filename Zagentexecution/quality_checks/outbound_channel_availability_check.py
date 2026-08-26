"""
outbound_channel_availability_check.py — ¿QUE CANALES SALIENTES ESTAN VIVOS AHORA MISMO?

LA PREGUNTA QUE NUNCA PUDIMOS CONTESTAR
---------------------------------------
Tenemos 239 destinos RFC configurados en P01. El inventario dice cuantos hay y el analisis de
frontera dice cuantos parecen "usados". Ninguno de los dos contesta la unica pregunta que importa
cuando algo se rompe: **¿responde?**

Nacio de INC-000016471 (2026-08-26). El canal por el que sale TODO PDF de la institucion — el
destino `ADS` — estuvo caido TRES DIAS LABORABLES sin que nadie lo supiera, porque:

  * estaba catalogado `NO_MEDIBLE` en interface_inventory.json. Cierto del TRAFICO ("un destino
    saliente no registra en nuestro log que hace en el sistema destino"), FALSO de la
    DISPONIBILIDAD: "¿responde?" se contesta desde aqui, sin credenciales, en menos de un segundo.
  * y estaba marcado `DEAD` en interface_boundary.json mientras un usuario lo ejercitaba. Ese
    veredicto venia de contar llamadas RFC en el log de auditoria — y una llamada HTTP saliente no
    es una llamada RFC. Medido entonces: **40 de 40 destinos tipo G/H con observed_calls=0**, y
    ninguno de los 11 LIVE es HTTP. Una tasa del 100% en una clase entera es la firma de un
    instrumento ciego, no una medida.

Falsador independiente: las 5 rutas al SLD figuran las cinco DEAD, mientras el job
`SAP_SLD_DATA_COLLECT` (`RSLDAGDS`), cuyo unico trabajo es empujar datos por una de ellas,
termino OK 126 veces en la misma ventana.

QUE HACE
--------
Lee los destinos HTTP (tipo G/H) del Gold DB (`rfcdes`), parsea `RFCOPTIONS` para sacar host,
puerto, path y si lleva SSL, y hace UNA peticion por destino. **NUNCA envia credenciales.**

La FORMA del fallo es el dato — son cuatro diagnosticos distintos, no uno:

    401 / 403          -> ARRIBA, pide autenticacion. El servicio corre; si algo falla es la
                          CREDENCIAL. (Es el resultado que buscamos, no un fallo que reintentar.)
    2xx / 3xx          -> ARRIBA.
    404                -> el puerto responde, la aplicacion NO esta desplegada en esa ruta.
    5xx                -> ARRIBA pero rota.
    CONNECTION_REFUSED -> el host esta vivo y NADA escucha en ese puerto: instancia parada.
    TIMEOUT            -> ruta bloqueada (firewall descarta) o destino saturado.
    DNS_FAIL           -> el nombre no resuelve desde aqui.

Confundir refused con timeout manda el ticket al equipo equivocado. Es la distincion mas rentable
de todo el script.

LO QUE ESTE INSTRUMENTO **NO** PUEDE
------------------------------------
  * No dice si el canal se USA — eso es trafico, y para un saliente se mide en el otro extremo.
    Un destino vivo y sin uso es indistinguible aqui de uno vivo y muy usado.
  * No prueba que la APLICACION del otro lado funcione: un 200 en el endpoint de configuracion no
    garantiza que un render de PDF salga bien.
  * No cubre los destinos tipo 3 (ABAP) ni T (programa externo): esos se prueban desde SM59 o con
    RFC_PING, no con HTTP.
  * Mide desde ESTA maquina, no desde P01. Una ruta puede existir para el servidor y no para el
    portatil, y al reves. Cuando el veredicto importe, contrastalo con SM59.

Uso:
    python Zagentexecution/quality_checks/outbound_channel_availability_check.py
    python ... --only ADS,SLD_DS_HTTP        # solo estos destinos
    python ... --json                        # salida encadenable
    python ... --fail-on-down                # exit 1 si algun canal esta caido (para gate/cron)

Sin --fail-on-down siempre sale 0: es un INFORME. La lista de destinos muertos es informacion,
no necesariamente un incidente — muchos destinos estan configurados y no se usan.
"""
import argparse
import http.client
import json
import os
import socket
import sqlite3
import ssl
import sys
import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GOLD_DB = os.path.join(PROJECT_ROOT, "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
TIMEOUT = 8.0


def parse_rfcoptions(opts):
    """RFCOPTIONS es una cadena `K=valor,` concatenada. Devuelve las claves que nos importan.

    H = host · I = puerto · N = path prefix · D = usuario · s = SSL (Y/N) · T = traza (Y/N)
    Q = tipo de autenticacion (B = basic).
    """
    out = {}
    for chunk in (opts or "").split(","):
        if "=" in chunk:
            k, _, v = chunk.partition("=")
            k = k.strip()
            if k and k not in out:
                out[k] = v.strip()
    return out


def load_http_destinations(only=None):
    if not os.path.exists(GOLD_DB):
        raise SystemExit("Gold DB no encontrado: %s" % GOLD_DB)
    con = sqlite3.connect("file:%s?mode=ro" % GOLD_DB.replace("\\", "/"), uri=True, timeout=60)
    rows = con.execute(
        "select RFCDEST, RFCTYPE, RFCOPTIONS from rfcdes where RFCTYPE in ('G','H') order by RFCDEST"
    ).fetchall()
    con.close()

    dests = []
    for name, rtype, opts in rows:
        if only and name not in only:
            continue
        o = parse_rfcoptions(opts)
        host = o.get("H", "")
        if not host or host.startswith("%"):
            continue                                  # destino sin host resoluble (plantilla)
        try:
            port = int(o.get("I") or (443 if o.get("s") == "Y" else 80))
        except ValueError:
            continue
        dests.append({
            "dest": name, "type": rtype, "host": host, "port": port,
            "path": o.get("N") or "/", "user": o.get("D", ""),
            "ssl": o.get("s") == "Y", "trace": o.get("T") == "Y",
            "auth": o.get("Q", ""),
        })
    return dests


def probe(d, timeout=TIMEOUT):
    r = dict(d)
    r["credentials_sent"] = False
    try:
        r["ip"] = socket.gethostbyname(d["host"])
    except socket.gaierror:
        r.update(verdict="DNS_FAIL", up=None,
                 detail="el nombre no resuelve desde esta maquina")
        return r
    t0 = datetime.datetime.now()
    try:
        cls = http.client.HTTPSConnection if d["ssl"] else http.client.HTTPConnection
        kw = {"timeout": timeout}
        if d["ssl"]:
            kw["context"] = ssl._create_unverified_context()
        c = cls(d["host"], d["port"], **kw)
        c.request("GET", d["path"], headers={"User-Agent": "unesco-outbound-availability/1.0"})
        resp = c.getresponse()
        resp.read(256)
        c.close()
    except socket.timeout:
        r.update(verdict="TIMEOUT", up=False,
                 detail="sin respuesta en %.0fs: ruta bloqueada (firewall descarta) o saturado"
                        % timeout)
        return r
    except ConnectionRefusedError:
        r.update(verdict="CONNECTION_REFUSED", up=False,
                 detail="el host vive y NADA escucha en el puerto: instancia parada")
        return r
    except ssl.SSLError as e:
        r.update(verdict="SSL_ERROR", up=None, detail=str(e)[:120])
        return r
    except OSError as e:
        r.update(verdict="NETWORK_ERROR", up=None, detail="%s: %s" % (type(e).__name__, e))
        return r

    r["elapsed_s"] = round((datetime.datetime.now() - t0).total_seconds(), 3)
    r["status"] = resp.status
    if resp.status in (401, 403):
        r.update(verdict="UP_AUTH_REQUIRED", up=True,
                 detail="ARRIBA y pide autenticacion -- si algo falla es la CREDENCIAL")
    elif resp.status == 404:
        r.update(verdict="PORT_UP_APP_NOT_DEPLOYED", up=False,
                 detail="el puerto responde, la aplicacion no esta en esa ruta")
    elif resp.status >= 500:
        r.update(verdict="UP_BUT_ERRORING", up=True, detail="responde con error de servidor")
    else:
        r.update(verdict="UP", up=True, detail="responde")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="lista de destinos separada por comas")
    ap.add_argument("--timeout", type=float, default=TIMEOUT)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on-down", action="store_true",
                    help="exit 1 si algun canal esta caido (para gate o tarea programada)")
    a = ap.parse_args()

    only = set(x.strip() for x in a.only.split(",")) if a.only else None
    dests = load_http_destinations(only)
    results = [probe(d, a.timeout) for d in dests]

    if a.json:
        print(json.dumps({"timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                          "probed": len(results), "results": results},
                         ensure_ascii=False, indent=2))
    else:
        print("=" * 100)
        print("DISPONIBILIDAD DE CANALES SALIENTES HTTP  --  %s"
              % datetime.datetime.now().isoformat(timespec="seconds"))
        print("fuente: Gold DB rfcdes (tipo G/H) · SIN credenciales · un 401 es ARRIBA, no un fallo")
        print("=" * 100)
        up = [r for r in results if r.get("up") is True]
        down = [r for r in results if r.get("up") is False]
        unk = [r for r in results if r.get("up") is None]
        for group, title in ((down, "CAIDOS"), (up, "ARRIBA"), (unk, "INDETERMINADOS")):
            if not group:
                continue
            print("\n-- %s (%d) %s" % (title, len(group), "-" * 60))
            for r in sorted(group, key=lambda x: x["dest"]):
                flag = "  [HTTP PLANO]" if not r["ssl"] and r.get("user") else ""
                print("  %-28s %-24s %s:%s%s" % (r["dest"], r["verdict"], r["host"], r["port"], flag))
                print("       %s" % r["detail"])
        print("\n" + "=" * 100)
        print("  %d probados · %d arriba · %d caidos · %d indeterminados"
              % (len(results), len(up), len(down), len(unk)))
        print("  RECORDATORIO: 'arriba' NO significa 'se usa', y 'caido' NO significa 'incidente'")
        print("  -- muchos destinos estan configurados y nunca se usaron. Cruza con el dueno.")
        print("=" * 100)

    if a.fail_on_down and any(r.get("up") is False for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
