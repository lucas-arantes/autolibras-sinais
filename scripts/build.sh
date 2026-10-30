#!/usr/bin/env bash
# Converte o dicionário do VLibras e monta o site em dist/.
#
# Uso: scripts/build.sh [--region BR] [--ref main] [--jobs N] [-- outros argumentos do build_pack.py]
#
# O conversor (MIT) fica no repositório do AutoLibras Tradutor. Aponte para um checkout
# dele com AUTOLIBRAS_TRADUTOR (padrão: ../autolibras-tradutor). Precisa do Blender 4.5+
# no PATH (ou em BLENDER=...) e do Python 3. A conversão retoma de onde parou: rodar de
# novo só converte o que falta. O dicionário inteiro baixa ~60 GB de .blend para o cache
# (~/.cache/autolibras/vlibras-sources) e leva algumas horas, quase tudo de download.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRADUTOR="${AUTOLIBRAS_TRADUTOR:-$HERE/../autolibras-tradutor}"
CONVERTER="$TRADUTOR/packages/avatar-three/tools/clips/build_pack.py"
REGION=BR
REF=main
JOBS="$(( ($(nproc) + 1) / 2 ))"
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="$2"; shift 2 ;;
    --ref) REF="$2"; shift 2 ;;
    --jobs) JOBS="$2"; shift 2 ;;
    --) shift; EXTRA=("$@"); break ;;
    *) echo "argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$CONVERTER" ]]; then
  echo "conversor não encontrado em $CONVERTER (defina AUTOLIBRAS_TRADUTOR)" >&2
  exit 1
fi
BLENDER_ARGS=()
[[ -n "${BLENDER:-}" ]] && BLENDER_ARGS=(--blender "$BLENDER")

mkdir -p "$HERE/build"
# build_pack.py sai com 1 se algum sinal falhou; as falhas ficam em build/<região>/failures.json
# e entram no stats.json, então o site é montado mesmo assim.
python3 "$CONVERTER" --out "$HERE/build/$REGION" --region "$REGION" --ref "$REF" --all \
  --jobs "$JOBS" "${BLENDER_ARGS[@]}" "${EXTRA[@]}" || echo "aviso: houve falhas na conversão" >&2

COMMIT="$(git -C "$TRADUTOR" rev-parse HEAD 2>/dev/null || true)"
python3 "$HERE/scripts/make_dist.py" --build "$HERE/build" --dist "$HERE/dist" \
  ${COMMIT:+--converter-commit "$COMMIT"} "$REGION"
