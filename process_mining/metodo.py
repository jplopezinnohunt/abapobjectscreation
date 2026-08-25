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

    def avisar(self, salida=None):
        """Imprime lo que aplica ANTES de minar. Un aviso que llega despues no sirve."""
        p = salida or print
        if not self.items:
            p(f"[metodo] sin memorias sobre {', '.join(self.temas)} -- eres el primero")
            return
        p(f"[metodo] {len(self.items)} memoria(s) aplican a {', '.join(self.temas)}:")
        for m in self.items:
            verbo, _por = PESO.get(m.get("kind"), ("NOTA", ""))
            p(f"  [{verbo:10s}] {str(m.get('fact'))[:118]}")
            if m.get("implication"):
                p(f"               -> {str(m['implication'])[:110]}")


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
