#!/usr/bin/env bash
# Publica dist/ no branch gh-pages (GitHub Pages, "Deploy from a branch").
#
# Uso: scripts/publish.sh [--push] [--remote origin] [--branch gh-pages]
#
# Sem --push, só cria o commit local em gh-pages e mostra o comando para enviar. O branch
# tem um commit só (sem histórico), para o repositório não acumular cópias antigas dos
# ~700 MB de clipes; por isso o envio usa --force.
#
# O GitHub Pages serve os arquivos com "Access-Control-Allow-Origin: *", então o app
# pode carregar o pacote de qualquer domínio. Limites: site de até 1 GB. Outro servidor
# estático serve do mesmo jeito (rsync -a dist/ destino/), desde que libere o CORS.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUSH=0
REMOTE=origin
BRANCH=gh-pages
while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --remote) REMOTE="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    *) echo "argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done

cd "$HERE"
[[ -f dist/index.html ]] || { echo "dist/ vazio: rode scripts/build.sh antes" >&2; exit 1; }

# Índice temporário: monta a árvore de dist/ sem mexer no branch atual nem no índice.
INDEX="$(mktemp)"
trap 'rm -f "$INDEX"' EXIT
rm -f "$INDEX"
GIT_DIR="$(git rev-parse --absolute-git-dir)"
(cd dist && GIT_INDEX_FILE="$INDEX" git --git-dir="$GIT_DIR" --work-tree=. add -A -f .)
TREE="$(GIT_INDEX_FILE="$INDEX" git write-tree)"
REGIONS="$(cd dist && ls -d */ 2>/dev/null | tr -d / | tr '\n' ' ')"
COMMIT="$(git commit-tree "$TREE" -m "Publica o pacote de sinais (${REGIONS% }, $(date -u +%F))")"
git update-ref "refs/heads/$BRANCH" "$COMMIT"
echo "commit $COMMIT em $BRANCH ($(du -sh --apparent-size dist | cut -f1) em dist/)"

if [[ "$PUSH" -eq 1 ]]; then
  read -r -p "Enviar $BRANCH para $REMOTE com --force? [s/N] " answer
  [[ "$answer" == [sS] ]] || { echo "cancelado"; exit 1; }
  git push --force "$REMOTE" "$BRANCH"
else
  echo "para publicar: git push --force $REMOTE $BRANCH"
fi
