# Pacote de sinais do AutoLibras

Animações de sinais de Libras para o avatar VRM do [AutoLibras Tradutor](https://github.com/lucas-arantes/autolibras-tradutor). Elas são convertidas do dicionário aberto do VLibras ([vlibras-dictionary-sources](https://gitlab.lavid.ufpb.br/vlibras-public/vlibras-dictionary/vlibras-dictionary-sources), do LAViD/UFPB), que é GPL-3.0. Por isso o pacote fica neste repositório separado, com a mesma licença. O app, que é MIT, não inclui nenhum clipe: ele baixa o pacote por URL quando roda.

Este projeto não tem ligação com o VLibras nem com o LAViD/UFPB, e eles não o endossam.

## Como usar

Depois de publicado, o pacote fica em:

```text
https://lucas-arantes.github.io/autolibras-sinais/BR/
```

No AutoLibras Tradutor, há três formas de usar essa URL:

- no build do app web, com `VITE_SIGN_PACK_URL=https://lucas-arantes.github.io/autolibras-sinais/BR/`. Com ela definida, o avatar próprio passa a ser o padrão;
- nas configurações do app, em Avatar → Avatar próprio → Pacote de sinais;
- no player embutível: `player.html?avatar=propio&signs=<URL>`.

## O que tem no pacote

```text
dist/
  index.html          página simples com os links
  LICENSE             GPL-3.0
  .nojekyll
  BR/
    manifest.json     um verbete por sinal: arquivo, duração, trecho principal e posição das mãos
    stats.json        resumo da conversão: quantidade, tamanhos, erros medidos e falhas
    <sinal>.glb       um clipe glTF por sinal
```

Os nomes de arquivo trocam os caracteres fora de `[A-Za-z0-9_-]` pelo código Unicode entre hífens (`ÁGUA` vira `-c1-GUA.glb`). Por isso o player usa o campo `file` do manifest e não monta o nome sozinho.

Cada `.glb` tem:

- um nó por osso humanoide do VRM, com as rotações locais em quaternions int16 (pose de descanso em T, como os ossos normalizados do `@pixiv/three-vrm`);
- nós `contact_<lado>_<âncora>_<ponto>[_<outro>]` com a posição da mão em relação ao rosto, ao peito ou à outra mão (translação) e o peso do contato (escala). O avatar usa esses dados para corrigir os contatos com IK;
- nós `face_<canal>` com as expressões do sinal, de 0 a 1 na escala: `browRaise`, `browOuterUp`, `browLower`, `browFrown`, `browAngry`, `smile`, `frown`, `pucker`, `lipPress`, `upperLip`, `cheekPuff`, `cheekSuck` e `jawOpen`. Eles vêm das shape keys do rosto do avatar do VLibras.

O `manifest.json` também registra a origem: o commit do dicionário (`sourceCommit`) e o do conversor (`converterCommit`).

## Como gerar

Você precisa de:

- um checkout do [autolibras-tradutor](https://github.com/lucas-arantes/autolibras-tradutor), que tem o conversor (`packages/avatar-three/tools/clips`). Por padrão o script procura em `../autolibras-tradutor`; outro caminho vai em `AUTOLIBRAS_TRADUTOR`;
- o Blender 4.5 ou mais recente no `PATH`, ou indicado em `BLENDER`;
- o Python 3;
- uns 60 GB livres para o cache dos `.blend`, em `~/.cache/autolibras/vlibras-sources`.

```bash
scripts/build.sh                 # região BR, branch main do dicionário
scripts/build.sh --ref <commit>  # fixa outra versão do dicionário
```

A conversão leva algumas horas, quase todas gastas no download. Converter cada sinal leva uns 0,2 s. Se for interrompida, rodar de novo só converte o que falta. Os sinais que falham ficam em `build/BR/failures.json` e aparecem no `stats.json`. Para reconverter tudo depois de mudar o conversor, use `scripts/build.sh -- --force`; com os `.blend` já no cache, leva poucos minutos.

O `build/` guarda a saída completa, com as medidas de qualidade de cada sinal, e não é versionado. O `dist/` é o site pronto para publicar.

## Como publicar

```bash
scripts/publish.sh          # cria o commit local no branch gh-pages
scripts/publish.sh --push   # pede confirmação e envia com --force
```

O branch `gh-pages` tem um único commit, sem histórico, para que o repositório não guarde cópias antigas dos clipes. No GitHub, ative o Pages em Settings → Pages → Deploy from a branch → `gh-pages`, pasta `/`.

O GitHub Pages responde com `Access-Control-Allow-Origin: *`, então o app consegue carregar o pacote de qualquer domínio. O limite do Pages é de 1 GB por site, e o pacote da região BR ocupa uns 700 MB. Qualquer servidor estático que libere CORS também serve (`rsync -a dist/ destino/`). No Cloudflare Pages não dá, porque o plano gratuito aceita no máximo 20 mil arquivos por site.

## Licença e código-fonte correspondente

GPL-3.0 ([LICENSE](LICENSE)). O repositório de origem traz o texto da GPLv3 sem dizer "ou qualquer versão posterior", então o pacote usa GPL-3.0-only.

A forma preferida para modificar os clipes são os arquivos `.blend` do dicionário do VLibras, no commit indicado em `sourceCommit`, junto com os scripts de conversão do autolibras-tradutor (MIT), no commit indicado em `converterCommit`. Os dois repositórios são públicos, e `scripts/build.sh` refaz o pacote a partir deles.

Créditos das animações: equipe do VLibras, LAViD/UFPB.
