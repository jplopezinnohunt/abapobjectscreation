"""
pmo_id_integrity_check.py — el PMO es la lista de lo pendiente: si su ID no identifica, no
sirve de indice. H135 + H136, s107.

DOS DEFECTOS MEDIDOS EL 2026-08-27, los dos silenciosos:

  H136 — DOBLE CODIFICACION EN DISCO. 788 secuencias mojibake (`â€”` por `—`, `ðŸ”´` por
      `🔴`, `Ã³` por `ó`...). El fichero decodificaba como UTF-8 sin error, asi que ninguna
      herramienta se quejaba: el texto era UTF-8 valido de unos bytes que ya venian mal.
      Nadie lo vio porque nadie lo comprobaba -- se lee a ojo y el ojo perdona.
      Reparadas todas en s107. Esta puerta impide que vuelvan.

  H135 — EL MISMO NUMERO PARA DOS COSAS DISTINTAS. 134 cabeceras, 111 numeros: 19 repetidos.
      Y hay que separar dos casos que se parecen y no son lo mismo:
        VARIAS SECCIONES DEL MISMO ITEM  — H137 sale 4 veces: el enunciado, los hallazgos de
            un agente, y el cierre. Es CORRECTO y util: un item vivo se actualiza.
        DOS ITEMS CON UN NUMERO          — H113 es a la vez 'REUBICACION de reglas' y
            'ALINEAR VARIANTES DE F.05'. Eso SI es un defecto: citar 'H113' ya no dice cual.
      Nacio de dos sesiones repartiendo numeros sin mirar los del otro -- el mismo fallo de
      un-solo-escritor que ADR-008 describe, aplicado al contador del PMO.

COMO SE SEPARAN — y por que NO por parecido de titulo
    El primer intento comparaba las PALABRAS de los titulos: si dos entradas del mismo numero
    no compartian ninguna, colision. Fallo en las DOS direcciones y se vio en la misma corrida:
    marco H137 -- que son cuatro secciones del MISMO item, redactadas distinto -- y dejo pasar
    H108, que si son dos cosas ('bancos casa muertos' y '11 de 13 incidentes no dejaron
    proceso'). Un titulo no es el item.
    Lo que se usa: SE DECLARA. En el propio PMO hay un bloque `PMO-IDS` donde se dice que
    repeticiones son el MISMO item y cuales son COLISIONES ya conocidas. Todo lo demas --
    cualquier repeticion nueva -- FALLA hasta que alguien la clasifique leyendo.
    Es la misma regla que se aplico a las juntas del circuito: JUICIO (alguien lo abrio y lo
    dijo) mas MEDIDA (la puerta comprueba que sigue siendo asi). Ninguno de los dos solo.

POR QUE LAS COLISIONES CONOCIDAS NO PONEN LA PUERTA EN ROJO
    Son 14 y vienen de dos sesiones repartiendo numeros sin mirar las del otro. Renumerarlas
    es una migracion con barrido de citas, no un arreglo de una linea. Un gate en rojo
    permanente por deuda historica es como se consigue que un check se ignore (leccion de
    H131), asi que se reportan como DEUDA VISIBLE y lo que falla es lo NUEVO.

LO QUE NO PUEDE VER
    - Si un item DEBERIA existir. Mide la integridad del indice, no si el trabajo esta bien.
    - Citas fuera del repo (un commit, un correo). Renumerar rompe esas y no se ven desde aqui.

Uso:
    python pmo_id_integrity_check.py
    python pmo_id_integrity_check.py --todos     # lista tambien las repeticiones benignas
"""

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",
    "needs": "files",
    "what": "el PMO no tiene doble codificacion y un ID no nombra dos items distintos",
    "args": "[--todos]",
}

import argparse
import collections
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PMO = os.path.join(REPO, ".agents", "intelligence", "PMO_BRAIN.md")

# Arranque de una secuencia UTF-8 leida como cp1252. Si aparece, el fichero paso dos veces
# por una codificacion y lo que se ve NO es lo que se escribio.
MOJIBAKE = re.compile(
    r"[ÂÃâð]"
    r"[-ÿ€‚ƒ„…†‡ˆ‰Š‹"
    r"ŒŽ‘’“”•–—˜™š›"
    r"œžŸ]{1,4}")

# `[^\n]`, NO `.` con re.S. Con re.S el `.{0,120}` es GOLOSO y se TRAGA la cabecera siguiente
# cuando dos van seguidas, asi que `finditer` sigue DESPUES de ella y la segunda desaparece.
# Se cazo probando la puerta con dos entradas H999 pegadas: no las vio. Una puerta que no se
# prueba con un caso que DEBE fallar no esta probada -- y esta llevaba 133 cabeceras contadas
# donde un regex simple contaba 134.
CABECERA = re.compile(r"\*\*(H\d+)\b([^\n]{0,120})")

VACIAS = {"the", "de", "la", "el", "y", "que", "un", "una", "los", "las", "en", "con", "por",
          "para", "del", "al", "no", "es", "se", "lo", "su", "sin", "mas", "ya", "hay",
          "and", "of", "to", "a", "medido", "queda", "quedan", "solo", "esta", "este"}


def palabras(t):
    t = re.sub(r"[^\wÀ-ÿ ]", " ", t.lower())
    return {w for w in t.split() if len(w) > 3 and w not in VACIAS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--todos", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(PMO):
        print("no existe .agents/intelligence/PMO_BRAIN.md")
        return 1
    t = io.open(PMO, encoding="utf-8").read()

    fallos = []

    # ---- H136: codificacion ----------------------------------------------------
    moj = MOJIBAKE.findall(t)
    print("CODIFICACION")
    if moj:
        c = collections.Counter(moj)
        print(f"   X {len(moj)} secuencia(s) de DOBLE CODIFICACION:")
        for s, n in c.most_common(8):
            print(f"       {s!r} x{n}")
        print("     El fichero decodifica sin error, asi que nada mas se queja. Se repara")
        print("     re-codificando cada secuencia a cp1252 y decodificandola como UTF-8.")
        fallos.append(f"{len(moj)} secuencias mojibake")
    else:
        print("   OK — sin dobles codificaciones")

    # ---- H135: identidad de los IDs --------------------------------------------
    entradas = collections.defaultdict(list)
    for m in CABECERA.finditer(t):
        titulo = " ".join(m.group(2).replace("\n", " ").split())[:110]
        entradas[m.group(1)].append(titulo)

    declarado = {}
    for m in re.finditer(r"<!--\s*PMO-IDS:\s*(mismo-item|colision-historica)\s*=\s*([^>]*?)-->", t):
        for hid in re.findall(r"H\d+", m.group(2)):
            declarado[hid] = m.group(1)

    reales, benignas, deuda = [], [], []
    for hid, tits in entradas.items():
        if len(tits) < 2:
            continue
        cual = declarado.get(hid)
        if cual == "mismo-item":
            benignas.append((hid, tits))
        elif cual == "colision-historica":
            deuda.append((hid, tits))
        else:
            reales.append((hid, tits))          # sin clasificar = falla

    print(f"\nIDENTIDAD DE LOS IDs  ·  {sum(len(v) for v in entradas.values())} cabeceras · "
          f"{len(entradas)} numeros distintos")
    if reales:
        print(f"   X {len(reales)} numero(s) repetidos SIN CLASIFICAR — hay que leerlos y")
        print(f"     declararlos en el bloque PMO-IDS del propio PMO_BRAIN.md:")
        for hid, tits in sorted(reales):
            print(f"      {hid}:")
            for x in tits:
                print(f"         - {x}")
        fallos.append(f"{len(reales)} IDs repetidos sin clasificar")
    else:
        print("   OK — toda repeticion esta clasificada")

    if deuda:
        print(f"\n   DEUDA DECLARADA: {len(deuda)} numero(s) que SI nombran dos items distintos.")
        print(f"   Visible a proposito, no en rojo: renumerar exige barrer las citas del repo.")
        print(f"      {', '.join(sorted(h for h, _ in deuda))}")

    if benignas:
        print(f"\n   {len(benignas)} numero(s) con VARIAS SECCIONES DEL MISMO ITEM — esto es "
              f"correcto, un item vivo se actualiza:")
        for hid, tits in sorted(benignas):
            print(f"      {hid} x{len(tits)}" + (f"  ({tits[0][:70]})" if a.todos else ""))
            if a.todos:
                for x in tits[1:]:
                    print(f"                 {x[:70]}")

    print("\n" + "=" * 76)
    if fallos:
        print("FALLO — " + " · ".join(fallos))
        print("Renumerar NO es gratis: un ID citado en un retro, un claim o un commit se")
        print("queda apuntando a nada. Antes de mover uno, barrer sus citas en el repo.")
        return 1
    print("OK — el PMO codifica bien y cada numero nombra una sola cosa")
    return 0


if __name__ == "__main__":
    sys.exit(main())
