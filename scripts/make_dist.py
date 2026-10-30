#!/usr/bin/env python3
"""Monta o site estático do pacote de sinais a partir da saída da conversão.

    python3 scripts/make_dist.py [--build build] [--dist dist] [--converter-commit SHA] [REGIÃO ...]

Para cada região em `build/<REGIÃO>` (gerada por `build_pack.py`), grava em `dist/<REGIÃO>`:

- os clipes `.glb` (hard links quando possível, para não duplicar espaço);
- `manifest.json` só com o que o player usa (o manifest completo, com as medidas de
  qualidade, fica em `build/`);
- `stats.json`, com o resumo de qualidade, tamanhos e falhas da conversão.

Na raiz de `dist/` ficam `LICENSE`, `.nojekyll` e um `index.html` simples. Confere que
todo arquivo citado no manifest existe. Só usa a biblioteca padrão do Python.
"""

import argparse
import html
import json
import os
import shutil
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_KEYS = ("file", "duration", "strokeStart", "strokeEnd", "hands")


def is_sign_meta(entry):
    return entry.endswith(".json") and entry not in ("manifest.json", "failures.json")


def place(src, dst):
    """Hard link (sem copiar os bytes) ou, se não der, cópia."""
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def stats(values):
    values = sorted(values)
    if not values:
        return None
    return {
        "mean": round(sum(values) / len(values), 3),
        "p50": round(values[len(values) // 2], 3),
        "p95": round(values[int(0.95 * (len(values) - 1))], 3),
        "max": round(values[-1], 3),
    }


def build_region(region, build_dir, dist_dir, converter_commit):
    src = os.path.join(build_dir, region)
    with open(os.path.join(src, "manifest.json"), encoding="utf-8") as fh:
        full = json.load(fh)
    metas = {}
    for entry in os.listdir(src):
        if is_sign_meta(entry):
            with open(os.path.join(src, entry), encoding="utf-8") as fh:
                meta = json.load(fh)
            metas[meta["name"]] = meta
    failures = {}
    failures_path = os.path.join(src, "failures.json")
    if os.path.exists(failures_path):
        with open(failures_path, encoding="utf-8") as fh:
            failures = json.load(fh)

    out = os.path.join(dist_dir, region)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    signs = {}
    total_bytes = 0
    for name, entry in sorted(full["signs"].items()):
        glb = os.path.join(src, entry["file"])
        if not os.path.exists(glb):
            sys.exit(f"{region}: falta {entry['file']} ({name})")
        place(glb, os.path.join(out, entry["file"]))
        total_bytes += os.path.getsize(glb)
        signs[name] = {key: entry[key] for key in RUNTIME_KEYS if key in entry}

    manifest = {
        key: full[key]
        for key in ("format", "version", "skeleton", "region", "license", "source", "sourceCommit")
        if key in full
    }
    manifest["converter"] = "https://github.com/lucas-arantes/autolibras-tradutor"
    if converter_commit:
        manifest["converterCommit"] = converter_commit
    manifest["built"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    manifest["rest"] = full["rest"]
    manifest["signs"] = signs
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, separators=(",", ":"))

    quality = [m["quality"] for m in metas.values() if "quality" in m]
    summary = {
        "region": region,
        "signs": len(signs),
        "failures": len(failures),
        "failed": failures,
        "bytes": total_bytes,
        "manifestBytes": os.path.getsize(os.path.join(out, "manifest.json")),
        "clipBytes": stats([m["bytes"] for m in metas.values() if "bytes" in m]),
        "durationSeconds": stats([m["duration"] for m in metas.values()]),
        # Pior caso de cada sinal: o maior erro do clipe, depois a distribuição entre sinais.
        "fingertipErrorCmMax": stats([q["fingertipErrorCm"]["max"] for q in quality]),
        "fingertipErrorCmMean": stats([q["fingertipErrorCm"]["mean"] for q in quality]),
        "compressionDegMax": stats([q["compressionDeg"]["max"] for q in quality]),
        "withContacts": sum(1 for m in metas.values() if m.get("contacts")),
        "withFace": sum(1 for m in metas.values() if m.get("face")),
        "faceChannels": count_face(metas.values()),
    }
    with open(os.path.join(out, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    return summary


def count_face(metas):
    counts = {}
    for meta in metas:
        for channel in meta.get("face", {}):
            counts[channel] = counts.get(channel, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def write_index(dist_dir, summaries):
    rows = "\n".join(
        f'<li><a href="{r}/manifest.json">{r}/manifest.json</a>: {s["signs"]} sinais, '
        f"{s['bytes'] / 1e6:.0f} MB (<a href=\"{r}/stats.json\">estatísticas</a>)</li>"
        for r, s in summaries.items()
    )
    page = f"""<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pacote de sinais do AutoLibras</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem}}</style>
<h1>Pacote de sinais do AutoLibras</h1>
<p>Animações de sinais de Libras para o avatar VRM do
<a href="https://github.com/lucas-arantes/autolibras-tradutor">AutoLibras Tradutor</a>,
convertidas do dicionário aberto do VLibras
(<a href="https://gitlab.lavid.ufpb.br/vlibras-public/vlibras-dictionary/vlibras-dictionary-sources">vlibras-dictionary-sources</a>,
LAViD/UFPB).</p>
<p>Licença: <a href="LICENSE">GPL-3.0</a>. Use a URL da pasta da região como pacote de sinais.</p>
<ul>
{rows}
</ul>
<p>Gerado em {html.escape(datetime.now(timezone.utc).strftime("%Y-%m-%d"))}.</p>
</html>
"""
    with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("regions", nargs="*")
    ap.add_argument("--build", default=os.path.join(ROOT, "build"))
    ap.add_argument("--dist", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--converter-commit", help="commit do autolibras-tradutor usado na conversão")
    args = ap.parse_args()

    regions = args.regions or sorted(
        d for d in os.listdir(args.build) if os.path.exists(os.path.join(args.build, d, "manifest.json"))
    )
    if not regions:
        sys.exit(f"nada convertido em {args.build}; rode scripts/build.sh antes")
    os.makedirs(args.dist, exist_ok=True)
    summaries = {}
    for region in regions:
        summaries[region] = build_region(region, args.build, args.dist, args.converter_commit)
        s = summaries[region]
        print(
            f"{region}: {s['signs']} sinais, {s['failures']} falhas, {s['bytes'] / 1e6:.0f} MB "
            f"(manifest {s['manifestBytes'] / 1e6:.1f} MB)"
        )
    shutil.copy2(os.path.join(ROOT, "LICENSE"), os.path.join(args.dist, "LICENSE"))
    # Sem Jekyll, o GitHub Pages serve os arquivos como estão (inclusive os que começam com "_").
    open(os.path.join(args.dist, ".nojekyll"), "w").close()
    write_index(args.dist, summaries)


if __name__ == "__main__":
    main()
