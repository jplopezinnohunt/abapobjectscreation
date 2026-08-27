"""LA MEMORIA DE METODO, APLICADA — no consultada.

EL PROBLEMA
    `brain_v2/methods/algorithm_memory.json` tiene 145 memorias, cada una con su `implication`:
    un campo que dice literalmente QUE DEBEN HACER DISTINTO LOS DEMAS ALGORITMOS por su culpa.
    Y no lo lee nadie. Se escriben, se acumulan, y el comportamiento no cambia.

    Eso es aprender y no aprender a la vez. El bus (blackboard) hace que los mineros se HABLEN;
    las preguntas abiertas (contract net) hacen que se PIDAN cosas; esto es la tercera pieza:
    que lo aprendido CAMBIE la forma de explorar. Sin ella los otros dos mecanismos reparten
    conocimiento entre agentes que siguen equivocandose igual.

    Ejemplo real y caro: la memoria "APQI.CREATOR no es una identidad, es un parametro de
    BDC_OPEN_GROUP que SAP no valida" estaba escrita desde el 24 de agosto. Al dia siguiente se
    mecanizo un minero de ese mismo canal que contaba creadores como si fueran actores. La
    memoria existia, el minero no la leyo, y el error se repitio mecanizado -- que es peor,
    porque ahora corre solo.

COMO SE USA, AL EMPEZAR CUALQUIER MINERO

    from metodo import lo_que_ya_aprendimos

    m = lo_que_ya_aprendimos("apqi", "creator", "batch input")
    m.avisar()                       # imprime lo que aplica, con su implicacion
    if m.prohibe("contar creadores como actores"):
        ...
    for t in m.trampas():            # las que hay que evitar SI O SI
        ...

    # y al terminar, si aprendiste algo del INSTRUMENTO:
    from metodo import aprender
    aprender("A31_bdc_channel_mining", "TRAP",
             "<que descubriste>", implicacion="<que deben hacer distinto los demas>")

POR QUE `implication` ES OBLIGATORIO
    Una memoria sin implicacion es una nota. La diferencia entre "APQD.VARDATA es LCHR" y "no
    intentes leer APQD por RFC: choca con OPTION_NOT_VALID y no es un fallo tuyo" es que la
    segunda cambia lo que hace el siguiente.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MEMORIA = REPO / "brain_v2" / "methods" / "algorithm_memory.json"

# Los tipos que OBLIGAN, y por que. No todos pesan igual.
PESO = {
    "TRAP": ("EVITA", "un error ya cometido y medido: repetirlo no es mala suerte"),
    "INSTRUMENT": ("LIMITA", "lo que tu herramienta NO puede ver. Ignorarlo produce un cero "
                             "que parece un hallazgo"),
    "SUBSTRATE": ("CONDICIONA", "como se comporta el sistema por debajo: cambia la lectura"),
    "CARRIER": ("CUIDADO", "un campo que no significa lo que su nombre sugiere"),
    "METHOD": ("HAZLO ASI", "la forma que ya se demostro que funciona"),
}


class Memorias:
    def __init__(self, items, temas):
        self.items = items
        self.temas = temas

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, i):
        return self.items[i]

    def trampas(self):
        return [m for m in self.items if m.get("kind") == "TRAP"]

    def limites(self):
        return [m for m in self.items if m.get("kind") == "INSTRUMENT"]

    def prohibe(self, texto):
        """¿Hay una memoria que desaconseje esto? Devuelve la memoria o None."""
        t = (texto or "").lower()
        pal = [p for p in t.split() if len(p) > 3]
        for m in self.items:
            blob = json.dumps(m, ensure_ascii=False).lower()
            if sum(1 for p in pal if p in blob) >= max(2, len(pal) // 2):
                return m
        return None

    def avisar(self, salida=None, minero=None):
        """Imprime lo que aplica ANTES de minar. Un aviso que llega despues no sirve.

        Y desde 2026-08-26 tambien enseña LAS PREGUNTAS ABIERTAS QUE ESTE MINERO PUEDE
        CONTESTAR. Aqui y no al final, a proposito: al arrancar, el minero esta a punto de
        leer justo los datos que las contestan; al terminar ya cerro la conexion y lo que
        queda es buena intencion.

        El operador lo pidio asi: «tienes que crear el mecanismo de colaboracion; si no, no
        colaboraran -- ellos tienen que SABER que deben colaborar». Medido antes de esto: 307
        hallazgos publicados en el foro y UNA sola pregunta contestada de catorce. El
        mecanismo existia (`pendientes()`) y era opcional, o sea que no existia.
        """
        p = salida or print
        if not self.items:
            p(f"[metodo] sin memorias sobre {', '.join(self.temas)} -- eres el primero")
        else:
            p(f"[metodo] {len(self.items)} memoria(s) aplican a {', '.join(self.temas)}:")
            for m in self.items:
                verbo, _por = PESO.get(m.get("kind"), ("NOTA", ""))
                p(f"  [{verbo:10s}] {str(m.get('fact'))[:118]}")
                if m.get("implication"):
                    p(f"               -> {str(m['implication'])[:110]}")
        self._foro(p, minero)

    def _foro(self, p, minero=None):
        """Las preguntas abiertas que este minero puede contestar, PUESTAS DELANTE.

        Si no se le pasa `minero`, se deduce del fichero que llamo: un minero no deberia
        tener que identificarse para que el mecanismo funcione -- si depende de que se
        acuerde, vuelve a ser opcional.
        """
        try:
            import inspect
            import os as _os
            import sys as _sys
            if not minero:
                for fr in inspect.stack()[1:6]:
                    f = _os.path.basename(fr.filename)
                    if f not in ("metodo.py", "<string>") and f.endswith(".py"):
                        minero = f[:-3]
                        break
            _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
            from colaborar import para_mi, marcar_visita
            # se prueba el nombre del fichero y tambien el id Axx que lo declara
            mias = para_mi(minero) or []
            if not mias:
                marcar_visita(minero, [], [])
                return
            p(f"\n[foro] {len(mias)} pregunta(s) abierta(s) que TU puedes contestar:")
            for q in mias[:6]:
                p(f"   {q['sujeto']}  (de {q['de']}) -- {q['_por_que_es_tuya']}")
                p(f"      {str(q.get('pregunta'))[:150]}")
            p("   contesta con: from colaborar import contestar; "
              "contestar('<tu id>', '<sujeto>', '<respuesta>', '<evidencia>')")
            p("   dejarla abierta pudiendo contestarla es la OCASION PERDIDA que mide "
              "mining_collaboration_check")

            # --- Y AHORA SE CONTESTA, no solo se enseña (s107) ------------------------
            # Enseñar la pregunta y marcar `contestadas=[]` era exactamente la ocasion
            # perdida que este mismo aviso denuncia. Un mecanismo que muestra el trabajo y
            # deja la accion en otra funcion que llama UN minero de 72 no es un mecanismo.
            # Aqui se intenta la respuesta automatica: si este minero YA publico algo sobre
            # ese sujeto, ese hallazgo es su respuesta -- no hay criterio nuevo que inventar.
            # Si no publico nada, CALLA: un foro que responde por responder miente.
            contestadas = []
            try:
                from colaborar import _respuesta_desde_lo_publicado, contestar
                for q in mias:
                    r = _respuesta_desde_lo_publicado(minero, q)
                    if not r:
                        continue
                    try:
                        if contestar(minero, q["sujeto"], r[0], r[1], para=q.get("para")):
                            contestadas.append(q["sujeto"])
                    except ValueError:
                        pass          # sujeto ambiguo: se niega, y hace bien
                if contestadas:
                    p(f"   [foro] CONTESTADAS automaticamente desde lo ya publicado: "
                      f"{', '.join(contestadas[:4])}")
            except Exception:
                pass

            marcar_visita(minero, [q["sujeto"] for q in mias], contestadas)
        except Exception:
            pass          # el foro no puede tumbar a un minero: avisa o calla, nunca rompe


def lo_que_ya_aprendimos(*temas):
    """Las memorias que aplican a estos temas. Llamalo ANTES de minar, no despues."""
    try:
        M = json.loads(MEMORIA.read_text(encoding="utf-8")).get("memories", [])
    except Exception:
        return Memorias([], list(temas))
    claves = [str(t).lower() for t in temas if t]
    if not claves:
        return Memorias(M, ["todo"])
    out = []
    for m in M:
        blob = json.dumps(m, ensure_ascii=False).lower()
        if any(k in blob for k in claves):
            out.append(m)
    # las TRAMPAS primero: son las que evitan un error ya cometido
    orden = {"TRAP": 0, "INSTRUMENT": 1, "CARRIER": 2, "SUBSTRATE": 3, "METHOD": 4}
    out.sort(key=lambda m: orden.get(m.get("kind"), 9))
    return Memorias(out, list(temas))


# ---------------------------------------------------------------------------------------------
# IMPLICACIONES EJECUTABLES — que la memoria OBLIGUE, no que se lea.
#
# Medido 2026-08-25: los 34 mineros importan este modulo y la puerta los da por buenos, pero
# solo UNO condiciona su comportamiento. Leer no es obedecer, y una puerta que mide el import
# mide la FORMA. Esto lo cierra: una memoria puede llevar una COMPROBACION sobre la salida del
# minero, y lo que la incumple no se publica -- se marca.
#
# Cada entrada: (patron que identifica la memoria, nombre, funcion(salida) -> None | motivo).
def _falta_ventana(doc):
    t = json.dumps(doc, ensure_ascii=False).lower()
    if any(k in t for k in ("ventana", "desde", "_window", "first_seen", "sal_date")):
        return None
    return ("ninguna cifra declara la VENTANA de la que sale, y este fichero mezcla fuentes con "
            "rangos distintos")


def _corte_no_publicado(doc):
    t = json.dumps(doc, ensure_ascii=False).lower()
    corta = any(k in t for k in ("top", "limit", "[:", "muestra", "primeros"))
    publica = any(k in t for k in ("descartad", "_lo_descartado", "vistos", "conservados",
                                   "cola", "resto"))
    if corta and not publica:
        return "hay senales de un corte y ningun recuento de lo descartado"
    return None


def _tasa_sobre_cola(doc):
    # Se normaliza la puntuacion antes de buscar: el aviso puede venir como texto ("no es una
    # tasa") o como NOMBRE DE CAMPO ("_estados_no_es_una_tasa"), y buscar solo la version con
    # espacios daba un incumplimiento donde el aviso SI estaba. Una comprobacion que depende de
    # como se escribe una clave mide la forma, que es justo lo que esta puerta vino a dejar de
    # medir.
    t = re.sub(r"[_\-\s]+", " ", json.dumps(doc, ensure_ascii=False).lower())
    if "qstate" in t or "error sessions" in t or "estados" in t:
        if "no es una tasa" not in t:
            return ("publica el reparto de QSTATE sin el aviso de que la cola BORRA los exitos "
                    "y por tanto no es una tasa de fallo")
    return None


def _creator_como_actor(doc):
    t = json.dumps(doc, ensure_ascii=False).lower()
    if "creator" in t and "usr02" not in t and "no es una identidad" not in t:
        return ("usa CREATOR sin contrastarlo contra USR02 ni advertir que es un parametro de "
                "BDC_OPEN_GROUP que SAP no valida")
    return None


COMPROBACIONES = [
    ("ventana", "declara la ventana", _falta_ventana),
    ("corte|muestreo|umbral|descart", "publica lo que descarta", _corte_no_publicado),
    ("qstate|cola|borra", "QSTATE no es una tasa", _tasa_sobre_cola),
    ("creator|bdc_open_group", "CREATOR no es un actor", _creator_como_actor),
]


def obedece(doc, temas=()):
    """¿La SALIDA de este minero cumple lo que las memorias que le aplican le exigen?

    Devuelve la lista de incumplimientos. Esto es lo que convierte una memoria en una regla:
    hasta ahora la implicacion era texto que se leia y se ignoraba.
    """
    fallos = []
    blob = " ".join(str(t).lower() for t in temas)
    for patron, nombre, fn in COMPROBACIONES:
        if temas and not re.search(patron, blob):
            continue
        motivo = fn(doc)
        if motivo:
            fallos.append({"regla": nombre, "incumplimiento": motivo})
    return fallos


def aprender(minero, kind, hecho, implicacion, evidencia="", sesion=None):
    """Devuelve al store lo aprendido del INSTRUMENTO.

    `implicacion` es obligatoria y a proposito: una memoria sin implicacion es una nota, y una
    nota no cambia lo que hace el siguiente.
    """
    if not implicacion or not str(implicacion).strip():
        raise ValueError("una memoria SIN implicacion es una nota: di que deben hacer distinto "
                         "los demas algoritmos por su culpa")
    if kind not in PESO:
        raise ValueError(f"kind debe ser uno de {sorted(PESO)}")
    try:
        M = json.loads(MEMORIA.read_text(encoding="utf-8"))
    except Exception:
        return 0
    mem = M.setdefault("memories", [])
    if any(str(x.get("fact", ""))[:60] == str(hecho)[:60] for x in mem):
        return 0
    base = {k: None for k in (mem[0] if mem else {"fact": None})}
    base.update({"fact": hecho, "kind": kind, "learned_by": minero,
                 "implication": implicacion, "session": sesion,
                 "source": evidencia or "medido"})
    mem.append(base)
    MEMORIA.write_text(json.dumps(M, indent=2, ensure_ascii=False), encoding="utf-8")
    return 1


def main():
    temas = [a for a in sys.argv[1:] if not a.startswith("--")]
    m = lo_que_ya_aprendimos(*temas)
    m.avisar()
    if not temas:
        print("\nuso: python process_mining/metodo.py <tema> [tema...]")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
