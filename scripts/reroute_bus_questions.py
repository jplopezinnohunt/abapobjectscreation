"""Re-enruta lo que el router VIEJO asigno por palabras y sigue sin contestar. s107.

POR QUE HACE FALTA, y por que no basta con arreglar el router
    `repartir()` solo mira preguntas dirigidas a CUALQUIERA. Las 9 abiertas YA tienen
    destinatario -- se lo puso el router viejo, por solape de palabras -- asi que arreglar el
    router no las toca. Un arreglo que solo vale para las futuras deja intacto justo el caso
    que lo motivo: A68 con cuatro preguntas de ADS que no puede contestar.

    Y mientras esten mal asignadas, el gate las cuenta como OCASION PERDIDA de A68, que es
    culpar a quien no podia.

QUE HACE
    Sobre las preguntas ABIERTAS: si alguien ha publicado un hallazgo sobre ese SUJETO, se la
    reasigna a el -- evidencia, no proximidad. Si nadie ha publicado, se marca SIN
    DESTINATARIO con lo que haria falta. Se conserva el destinatario anterior en la propia
    pregunta: reasignar sin dejar rastro seria borrar informacion.

NO SE HACE SOLO. Es una accion explicita: re-enrutar en silencio, cada corrida, seria un
churn que nadie puede auditar.
"""
import io
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "process_mining")
sys.stdout.reconfigure(encoding="utf-8")
import colaborar as C

d = C._cargar()
publicaron = {}
for h in (d.get("hallazgos") or []):
    s = str(h.get("sujeto") or "").strip().lower()
    m = str(h.get("minero") or "")
    if s and m:
        publicaron.setdefault(s, []).append(m)

movidas, sin_destino = [], []
for q in d.get("preguntas") or []:
    if q.get("respuestas"):
        continue
    suj = str(q.get("sujeto") or "").strip().lower()
    antes = str(q.get("para") or "")
    quien = str(q.get("de") or "")
    cands = [m for m in publicaron.get(suj, []) if m != quien]
    if cands and cands[0] != antes:
        q["para"] = cands[0]
        q["_reenrutada_s107"] = {
            "cuando": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "antes": antes,
            "por_que": ("el router viejo asignaba por SOLAPE DE PALABRAS. Este minero YA "
                        "PUBLICO un hallazgo sobre este mismo sujeto: eso es evidencia de que "
                        "puede contestar, no parecido de vocabulario"),
        }
        movidas.append((suj, antes, cands[0]))
    elif not cands:
        q["_sin_destinatario"] = {
            "cuando": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "asignada_por_palabras_a": antes,
            "por_que": ("NADIE ha publicado sobre este sujeto. El destinatario actual salio "
                        "del solape de palabras del router viejo y probablemente no puede "
                        "contestar -- dejarlo ahi le imputa una ocasion perdida que no es suya"),
            "que_haria_falta": ("que alguien MINE el sujeto, o que quien pregunta nombre la "
                                "tabla o el objeto concreto en vez del tema"),
        }
        sin_destino.append((suj, antes))

C._guardar(d)
print("RE-ENRUTADAS POR EVIDENCIA: %d" % len(movidas))
for s, a, b in movidas:
    print("   %-34s %s -> %s" % (s[:34], a, b))
print("\nMARCADAS SIN DESTINATARIO REAL: %d" % len(sin_destino))
for s, a in sin_destino:
    print("   %-34s estaba en %s (por palabras)" % (s[:34], a))
