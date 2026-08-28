# -*- coding: utf-8 -*-
"""_hallazgos.py — el CONTRATO DE SALIDA de un minero: datos NO bastan.

Un minero que solo publica datos deja el trabajo a medias: alguien tiene que leerlos y darse
cuenta. Medido en s108: los seis instrumentos nuevos produjeron cifras correctas, y las seis
oportunidades y los cuatro riesgos los saqué YO leyéndolas a mano. Si nadie las lee, no
existen — y nadie las lee cada semana.

**Un minero debe EMITIR lo que ha encontrado, clasificado, con tamaño y con evidencia.**

Tres clases, y la diferencia importa porque van a destinatarios distintos:

  OPORTUNIDAD  algo que se puede mejorar. Va a quien decide inversión de esfuerzo.
  RIESGO       algo que puede hacer daño si nadie actúa. Va a quien responde del control.
  DESAFÍO      algo que NO CUADRA y el minero no puede resolver solo. Va al foro de mineros
               y al humano que sí puede contestarlo. **Nadie está mejor situado que el minero
               para verlo**: es el único que tiene los datos delante en el momento en que la
               contradicción aparece. Si no lo registra ahí, se pierde -- y en s108 se
               perdieron varias hasta que alguien preguntó.
  DATO         un hecho relevante que no es ninguna de las tres. Va al conocimiento.

Reglas del contrato, y las tres nacen de errores medidos en s108:

1. **Sin TAMAÑO no se emite.** «7 cuentas se teclean a mano» parecía un ahorro; medido eran
   1.712 líneas en dos años frente a 11.669 de UNA sola cuenta electrónica. El tamaño
   desmontó la propuesta, y eso es un resultado, no un fracaso.
2. **Se declara el LÍMITE.** Qué no puede ver el instrumento. Tener el modelo asignado no
   prueba que el fichero pueda llegar: la restricción puede estar aguas arriba, en el banco.
   Sin esa frase, una lista accionable se vuelve una idea bonita.
3. **Se declara el DENOMINADOR.** Contra qué población. Las cuentas cerradas se marcan en el
   TEXTO (237 de 411): sin ese corte, 2 de los 4 primeros hallazgos eran falsos.

Aterriza en `process_mining/mining_findings.json`, el bus que ya usa el foro de mineros — para
que un choque entre dos medidas sea DETECTABLE. En s108 el choque 16-vs-80 el bus no lo pudo
ver porque ninguno de los dos publicaba ahí.
"""

import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
BUS = os.path.join(_REPO, "process_mining", "mining_findings.json")

OPORTUNIDAD = "OPORTUNIDAD"
RIESGO = "RIESGO"
DESAFIO = "DESAFIO"
DATO = "DATO"


class Hallazgos(object):
    """Acumula lo que un minero encuentra y lo emite al final, por consola y al bus.

    Uso mínimo dentro de un minero:

        h = Hallazgos("bank_statement_channel_census", denominador="167 cuentas vivas de 404 "
                      "(237 excluidas por llevar CLOSED en T012T-TEXT1)")
        h.riesgo("8 cuentas de extracto MANUAL sin responsable declarado",
                 tamano="8 cuentas · 4 personas · una lleva 259 dias muda",
                 evidencia="FEBKO.EUSER 2025-2026",
                 limite="el log dice quien lo hizo, no quien DEBIA hacerlo")
        h.emitir()
    """

    def __init__(self, minero, denominador="", sistema="P01", ventana="2025-2026"):
        self.minero = minero
        self.denominador = denominador
        self.sistema = sistema
        self.ventana = ventana
        self.items = []

    def _add(self, clase, que, tamano, evidencia, limite, accion):
        if not tamano:
            raise ValueError(
                "%s: '%s' se emite SIN TAMAÑO. El contrato lo prohíbe -- en s108 una "
                "oportunidad sin medir resultó ser 1.712 líneas en dos años frente a 11.669 "
                "de una sola cuenta. Mide primero, aunque el tamaño la desmonte." % (self.minero, que[:60]))
        self.items.append({"clase": clase, "que": que, "tamano": tamano,
                           "evidencia": evidencia, "limite": limite, "accion": accion,
                           "minero": self.minero, "denominador": self.denominador,
                           "sistema": self.sistema, "ventana": self.ventana})

    def oportunidad(self, que, tamano="", evidencia="", limite="", accion=""):
        self._add(OPORTUNIDAD, que, tamano, evidencia, limite, accion)

    def riesgo(self, que, tamano="", evidencia="", limite="", accion=""):
        self._add(RIESGO, que, tamano, evidencia, limite, accion)

    def desafio(self, que, tamano="", evidencia="", limite="", accion="",
                quien_puede_contestar=""):
        """Lo que NO cuadra y el minero no puede cerrar solo.

        Es la clase que mas se pierde, porque no es un fallo ni una mejora: es una pregunta.
        Y el minero es quien mejor puede formularla, porque la contradiccion le aparece con
        los datos delante. `quien_puede_contestar` es obligatorio en la practica: un desafio
        sin destinatario no lo recoge nadie."""
        self._add(DESAFIO, que, tamano, evidencia, limite,
                  accion or ("preguntar a: %s" % quien_puede_contestar if quien_puede_contestar
                             else "sin destinatario -- NOMBRA a quien puede contestarlo"))
        self.items[-1]["quien_puede_contestar"] = quien_puede_contestar
        self.items[-1]["abierto"] = True

    def dato(self, que, tamano="", evidencia="", limite="", accion=""):
        self._add(DATO, que, tamano, evidencia, limite, accion)

    # ------------------------------------------------------------------
    def emitir(self, al_bus=True):
        """Imprime y, si procede, publica. Devuelve cuántos hallazgos hay."""
        print("\n" + "=" * 92)
        print("LO QUE ESTE MINERO HA ENCONTRADO — %s" % self.minero)
        print("=" * 92)
        if self.denominador:
            print("  denominador: %s" % self.denominador)
        print("  sistema: %s · ventana: %s" % (self.sistema, self.ventana))
        if not self.items:
            print("\n  NADA. Y eso es una respuesta: los datos salieron y no hay ni oportunidad")
            print("  ni riesgo que emitir. No se rellena por rellenar.")
            return 0
        for cl in (RIESGO, DESAFIO, OPORTUNIDAD, DATO):
            g = [x for x in self.items if x["clase"] == cl]
            if not g:
                continue
            print("\n  --- %s (%d) ---" % (cl, len(g)))
            for x in g:
                print("   * %s" % x["que"])
                print("       tamaño    : %s" % x["tamano"])
                if x["evidencia"]:
                    print("       evidencia : %s" % x["evidencia"])
                if x["limite"]:
                    print("       NO puedo ver: %s" % x["limite"])
                if x["accion"]:
                    print("       acción    : %s" % x["accion"])
        if al_bus:
            self._publicar()
        return len(self.items)

    def _publicar(self):
        """Al bus, para que un choque entre dos mineros sea DETECTABLE por el foro."""
        try:
            d = json.load(io.open(BUS, encoding="utf-8")) if os.path.exists(BUS) else {}
        except Exception:
            d = {}
        if not isinstance(d, dict):
            d = {"hallazgos": d if isinstance(d, list) else []}
        import datetime as _dt
        hoy = _dt.date.today().isoformat()
        lst = d.setdefault("hallazgos", [])
        mx = 0
        # DESDE CUANDO. Ningun registro de pendientes de este proyecto dice desde cuando lleva
        # parado un item: todos dicen QUE falta. Con cientos de items, esa es la diferencia
        # entre una lista viva y un cementerio. Se conserva la PRIMERA fecha en que el
        # hallazgo aparecio -- reconocido por (minero, que) -- y se actualiza la ultima vista.
        antes = {}
        for x in lst:
            if isinstance(x, dict) and x.get("minero") == self.minero and x.get("que"):
                antes[x["que"]] = x.get("visto_primero") or x.get("fecha") or hoy
            if isinstance(x, dict) and isinstance(x.get("id"), int):
                mx = max(mx, x["id"])
        # reemplaza lo que este mismo minero publicó antes: la última corrida manda
        lst[:] = [x for x in lst if not (isinstance(x, dict) and x.get("minero") == self.minero)]
        for i, x in enumerate(self.items, 1):
            lst.append(dict(x, id=mx + i,
                            visto_primero=antes.get(x["que"], hoy),
                            visto_ultima=hoy))
        try:
            os.makedirs(os.path.dirname(BUS), exist_ok=True)
            json.dump(d, io.open(BUS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            print("\n  publicado en el bus: %s (%d hallazgos)" % (
                os.path.relpath(BUS, _REPO), len(self.items)))
        except Exception as e:
            print("\n  NO se pudo publicar en el bus: %s" % str(e)[:90])


# =====================================================================================
# LA BUSQUEDA. Lo anterior es como se PUBLICA; esto es lo que hay que BUSCAR.
# =====================================================================================
# Un minero que solo censa una poblacion deja la oportunidad a que alguien la lea. Medido en
# s108: los seis instrumentos dieron cifras correctas y las seis oportunidades las encontre yo
# a mano, mirandolas. Un minero tiene que HACERSE LAS PREGUNTAS el mismo, sobre sus propios
# datos, cada vez que corre.
#
# Estas seis preguntas son genericas: no saben de bancos. Reciben una poblacion de registros y
# los nombres de los campos donde mirar, y devuelven lo que encuentran.

def buscar_configurado_sin_uso(filas, tiene_config, tiene_uso, id_campo="id"):
    """(1) EXISTE Y NO SE USA. Lo que esta montado y no se ejercita.
    En s108: 11 cuentas con modelo de extracto asignado y sin usar."""
    return [f for f in filas if f.get(tiene_config) and not f.get(tiene_uso)]


def buscar_movimiento_sin_contraparte(filas, hay_movimiento, hay_registro):
    """(2) SE MUEVE SIN SU CONTRAPARTE. Actividad sin el rastro que deberia acompanarla.
    En s108: 3 mandatos mueven saldo sin ni un extracto que lo corrobore. Es la forma que
    produce RIESGOS, no oportunidades: algo pasa y nada lo respalda."""
    return [f for f in filas if f.get(hay_movimiento) and not f.get(hay_registro)]


def buscar_entrada_sin_efecto(filas, hay_entrada, hay_efecto):
    """(3) ENTRA Y NO PRODUCE NADA. Trabajo que se procesa sin consecuencia aguas abajo.
    En s108: 5 cuentas, 2.321 extractos, cero movimiento contable."""
    return [f for f in filas if f.get(hay_entrada) and not f.get(hay_efecto)]


def buscar_unico_donde_otros_comparten(filas, campo_recurso, campo_sujeto, minimo_compartido=3):
    """(4) UNICO DONDE OTROS COMPARTEN. Un recurso mantenido para un solo sujeto, mientras
    otro recurso equivalente sirve a muchos. En s108: 5 formatos de extracto para UNA cuenta
    cada uno -- 73 reglas para 6 cuentas -- frente a XRT940 con 60 bancos."""
    import collections
    por = collections.defaultdict(set)
    for f in filas:
        if f.get(campo_recurso):
            por[f[campo_recurso]].add(f.get(campo_sujeto))
    hay_compartidos = any(len(v) >= minimo_compartido for v in por.values())
    if not hay_compartidos:
        return []          # si NADIE comparte, ser unico no es una anomalia
    return [{"recurso": r, "sujetos": sorted(v)} for r, v in por.items() if len(v) == 1]


def buscar_discrepancia(filas, etiqueta, conducta, equivalencias):
    """(5) DOS FUENTES DISCREPAN. Donde lo que algo DICE ser no coincide con lo que HACE.
    `equivalencias` mapea etiqueta -> conductas aceptables. En s108 esta forma destapo que
    receiving_accounts (16) y OPERATIVA_COBRO (80) median objetos distintos.
    Cuando dos medidas del mismo sujeto no coinciden, UNA ESTA MAL: averiguar cual es el
    hallazgo, no el desacuerdo."""
    fuera = []
    for f in filas:
        e, c = f.get(etiqueta), f.get(conducta)
        if e in equivalencias and c and c not in equivalencias[e]:
            fuera.append(dict(f, _dice=e, _hace=c))
    return fuera


def buscar_misma_persona_en_dos_eslabones(filas, eslabon_a, eslabon_b, sujeto="id"):
    """(6) LA MISMA PERSONA EN DOS ESLABONES QUE DEBEN ESTAR SEPARADOS.
    Quien INTRODUCE un hecho externo no deberia ser quien lo VALIDA ni quien DISPONE del
    dinero que ese hecho justifica. Casi toda tabla SAP lleva el usuario que la toco
    (FEBKO.EUSER, BKPF.USNAM, REGUH, CDHDR.USERNAME) y casi nadie los cruza.
    Nacio de un hallazgo real en pagos: el creador coincidia con el autorizador.

    Control invertido, y hay que declararlo al usar esto: donde el eslabon de entrada es
    JOBBATCH no hay persona, y esa AUSENCIA es lo que hace mas seguro el canal automatico."""
    out = []
    for f in filas:
        a, b = f.get(eslabon_a), f.get(eslabon_b)
        if a and b and a == b and str(a).upper() not in ("JOBBATCH", "BATCH", "WF-BATCH"):
            out.append({"sujeto": f.get(sujeto), "persona": a,
                        "eslabones": [eslabon_a, eslabon_b]})
    return out


FORMAS = [
    ("configurado_sin_uso", buscar_configurado_sin_uso, OPORTUNIDAD),
    ("movimiento_sin_contraparte", buscar_movimiento_sin_contraparte, RIESGO),
    ("entrada_sin_efecto", buscar_entrada_sin_efecto, OPORTUNIDAD),
    ("unico_donde_otros_comparten", buscar_unico_donde_otros_comparten, OPORTUNIDAD),
    ("discrepancia", buscar_discrepancia, RIESGO),
    ("misma_persona_dos_eslabones", buscar_misma_persona_en_dos_eslabones, RIESGO),
]
