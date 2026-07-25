"""Inventario: scripts .py que ESCRIBEN directo a los stores core del brain.

Recorre Zagentexecution/** y scratch/**, busca .py que mencionen un store core
Y llamen json.dump / write_text, y determina via AST el TARGET REAL de cada write.
"""
import ast
import json
import os
import re
import sys

ROOT = r"C:\Users\jp_lopez\projects\abapobjectscreation"
SCAN_DIRS = ["Zagentexecution", "scratch"]

CORE_STORES = {
    "claims/claims.json": "claims",
    "claims.json": "claims",
    "agent_rules/feedback_rules.json": "feedback_rules",
    "feedback_rules.json": "feedback_rules",
    "annotations/annotations.json": "annotations",
    "annotations.json": "annotations",
    "incidents/incidents.json": "incidents",
    "incidents.json": "incidents",
    "agi/known_unknowns.json": "known_unknowns",
    "known_unknowns.json": "known_unknowns",
    "agi/data_quality_issues.json": "data_quality_issues",
    "data_quality_issues.json": "data_quality_issues",
}
# Basenames que identifican un store core
STORE_BASENAMES = {
    "claims.json": "claims",
    "feedback_rules.json": "feedback_rules",
    "annotations.json": "annotations",
    "incidents.json": "incidents",
    "known_unknowns.json": "known_unknowns",
    "data_quality_issues.json": "data_quality_issues",
}

MENTION_RE = re.compile(
    r"claims\.json|feedback_rules\.json|annotations\.json|incidents\.json|"
    r"known_unknowns\.json|data_quality_issues\.json"
)
WRITE_RE = re.compile(r"json\.dump|write_text")


def collect_candidates():
    out = []
    for d in SCAN_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, dirnames, filenames in os.walk(base):
            # skip venvs / node_modules / .git
            dirnames[:] = [x for x in dirnames if x not in
                           (".git", "node_modules", "__pycache__", ".venv", "venv", "site-packages")]
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    src = open(p, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                if MENTION_RE.search(src) and WRITE_RE.search(src):
                    out.append((p, src))
    return out


class Analyzer(ast.NodeVisitor):
    """Constante-propaga strings/Path y recolecta write-sites con su path expr."""

    def __init__(self):
        self.consts = {}          # var -> rendered string-ish
        self.writes = []          # (kind, path_expr_rendered, lineno)
        self.filevars = {}        # file var -> (path_expr, mode)

    # --- helpers -------------------------------------------------
    def render(self, node):
        try:
            s = ast.unparse(node)
        except Exception:
            return "<?>"
        # substitute known consts (longest name first)
        for k in sorted(self.consts, key=len, reverse=True):
            rep = self.consts[k]
            s = re.sub(r"\b" + re.escape(k) + r"\b", lambda m, _r=rep: _r, s)
        return s

    # --- visits --------------------------------------------------
    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            val = node.value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                self.consts[name] = val.value
            else:
                r = self.render(val)
                if ("/" in r or "\\" in r or ".json" in r) and len(r) < 400:
                    self.consts[name] = r
        self.generic_visit(node)

    def visit_With(self, node):
        for item in node.items:
            call = item.context_expr
            path_expr, mode = None, None
            if isinstance(call, ast.Call):
                f = call.func
                fname = getattr(f, "id", None) or getattr(f, "attr", None)
                if fname == "open":
                    if call.args:
                        path_expr = self.render(call.args[0])
                    if isinstance(f, ast.Attribute):  # p.open('w')
                        path_expr = self.render(f.value)
                    if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
                        mode = call.args[1].value
                    for kw in call.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                            mode = kw.value.value
            if path_expr is not None and item.optional_vars is not None and \
                    isinstance(item.optional_vars, ast.Name):
                self.filevars[item.optional_vars.id] = (path_expr, mode or "r")
        self.generic_visit(node)

    def visit_Call(self, node):
        f = node.func
        # json.dump(obj, fh)
        if isinstance(f, ast.Attribute) and f.attr == "dump" and \
                isinstance(f.value, ast.Name) and f.value.id == "json":
            if len(node.args) > 1:
                fh = node.args[1]
                if isinstance(fh, ast.Name) and fh.id in self.filevars:
                    p, m = self.filevars[fh.id]
                    self.writes.append(("json.dump", p, node.lineno))
                elif isinstance(fh, ast.Call):
                    # json.dump(obj, open(path,'w'))
                    inner = fh
                    if getattr(inner.func, "id", getattr(inner.func, "attr", None)) == "open" and inner.args:
                        self.writes.append(("json.dump", self.render(inner.args[0]), node.lineno))
                else:
                    self.writes.append(("json.dump", "<fh:%s>" % self.render(fh), node.lineno))
        # X.write_text(...)
        if isinstance(f, ast.Attribute) and f.attr == "write_text":
            self.writes.append(("write_text", self.render(f.value), node.lineno))
        # X.write(json.dumps(...))
        if isinstance(f, ast.Attribute) and f.attr == "write":
            if node.args and isinstance(node.args[0], ast.Call):
                a = node.args[0]
                if isinstance(a.func, ast.Attribute) and a.func.attr == "dumps":
                    tgt = f.value
                    if isinstance(tgt, ast.Name) and tgt.id in self.filevars:
                        p, m = self.filevars[tgt.id]
                        self.writes.append(("f.write(dumps)", p, node.lineno))
                    else:
                        self.writes.append(("f.write(dumps)", self.render(tgt), node.lineno))
        self.generic_visit(node)


def find_writer_helpers(tree):
    """Funciones tipo `def save(path, data): json.dump(data, open(path,'w'))`.

    Devuelve {func_name: [indices de parametros que son el destino]}.
    """
    helpers = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = [a.arg for a in fn.args.args]
        if not params:
            continue
        sub = Analyzer()
        for st in fn.body:
            sub.visit(st)
        idxs = set()
        for kind, pexpr, ln in sub.writes:
            for i, p in enumerate(params):
                if re.search(r"\b" + re.escape(p) + r"\b", pexpr):
                    idxs.add(i)
        if idxs:
            helpers[fn.name] = sorted(idxs)
    return helpers


def classify_target(path_expr):
    """Devuelve el store core al que apunta el path, o None."""
    low = path_expr.lower()
    for base, store in STORE_BASENAMES.items():
        if base in low:
            # descartar companions / backups / reportes con nombre parecido
            return store
    return None


def main():
    rows = []
    for p, src in collect_candidates():
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            rows.append({"script": rel, "writes": [], "verdict": "AMBIGUO",
                         "note": "SyntaxError: %s" % e})
            continue
        a = Analyzer()
        a.visit(tree)
        # 2a pasada: llamadas a funciones-helper de escritura (save(path, data))
        helpers = find_writer_helpers(tree)
        helper_writes = []
        if helpers:
            b = Analyzer()          # re-propaga consts a nivel modulo
            for st in tree.body:
                b.visit(st)
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and \
                        n.func.id in helpers:
                    for i in helpers[n.func.id]:
                        if i < len(n.args):
                            helper_writes.append(
                                ("helper:%s" % n.func.id, b.render(n.args[i]), n.lineno))
        all_writes = a.writes + helper_writes
        real, other = [], []
        for kind, pexpr, ln in all_writes:
            st = classify_target(pexpr)
            if st:
                real.append({"store": st, "expr": pexpr[:160], "kind": kind, "line": ln})
            else:
                other.append({"expr": pexpr[:160], "kind": kind, "line": ln})
        unresolved = [w for w in other if "<fh:" in w["expr"] or "<?>" in w["expr"]]
        if real:
            verdict = "ESCRITOR_REAL"
        elif unresolved:
            verdict = "AMBIGUO"
        elif all_writes:
            verdict = "SOLO_LECTOR"
        else:
            verdict = "AMBIGUO"  # menciona store + write pero AST no vio write
        rows.append({
            "script": rel,
            "stores": sorted({r["store"] for r in real}),
            "real": real,
            "other_targets": sorted({os.path.basename(w["expr"].strip("'\"")) for w in other})[:6],
            "verdict": verdict,
        })
    rows.sort(key=lambda r: (r["verdict"], r["script"]))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("TOTAL candidatos:", len(rows))
    for v in ("ESCRITOR_REAL", "AMBIGUO", "SOLO_LECTOR"):
        sub = [r for r in rows if r["verdict"] == v]
        print("\n=== %s (%d) ===" % (v, len(sub)))
        for r in sub:
            print("  %-95s %s" % (r["script"], ",".join(r.get("stores") or []) or
                                  ("->" + ",".join(r.get("other_targets") or []))))
    print("\nJSON:", out)


if __name__ == "__main__":
    main()
