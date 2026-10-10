# Pitfall: The Lost Expedition (PS2) — Tradução PT-BR

Tradução de fãs de **Pitfall: The Lost Expedition** (PlayStation 2, versão americana **SLUS-20408**) para o português do Brasil, por **Oblytoid**.

**Status:** v0.9 beta. Todo o texto está traduzido e revisado. A segunda metade do jogo ainda não foi conferida tela a tela.

## Para jogar
1. Baixe o `.zip` mais recente em [Releases](../../releases).
2. Descompacte e arraste a ISO original do jogo para cima de `ARRASTE A ISO AQUI.bat`.
3. A ISO traduzida aparece na mesma pasta da original. A original não é alterada.

O `LEIAME.txt` do pacote tem os códigos (CRC32/MD5/SHA-1) da ISO compatível e outras formas de aplicar o patch (Delta Patcher, xdelta3 no Linux/macOS).

Este repositório **não contém o jogo** nem arquivos extraídos dele. Você precisa da sua própria cópia original.

## Encontrou um problema?
Abra uma [Issue](../../issues) com um print da tela e a parte do jogo em que estava.

## Ferramentas (para quem quer estudar ou contribuir)
Scripts em Python 3.8 ou mais novo (testado no 3.12), só com a biblioteca padrão. Não precisa instalar nada além do Python. Detalhes de cada script em [`ferramentas/LEIAME.md`](ferramentas/LEIAME.md).

### Estrutura de pastas esperada
```
Pitfall/
├─ ferramentas/   scripts (neste repositório)
├─ script/        textos traduzidos (.txt), fora do repositório público
├─ ISOs/          Pitfall - The Lost Expedition (PT-BR).iso  ← cópia da sua ISO original
├─ extraido/      Pitfall - The Lost Expedition (PT-BR)/data/...  ← conteúdo da ISO
├─ build/         gerado: arquivos novos e a ISO de teste
└─ patch/         gerado: .xdelta e o pacote .zip
```
As pastas `ISOs/`, `extraido/`, `build/` e `patch/` ficam fora do Git (ver `.gitignore`).

### Como gerar
1. Copie a ISO original para `ISOs/` com o nome acima e extraia o conteúdo dela (por exemplo, com o 7-Zip) para `extraido/Pitfall - The Lost Expedition (PT-BR)/`.
2. `ferramentas/extrair.py` gera os textos editáveis.
3. `ferramentas/gerar_iso.bat` insere os textos e monta `build/Pitfall_PTBR_teste.iso`.
4. `ferramentas/gerar_patch.bat` cria o `.xdelta` e o pacote `.zip`. Precisa do [xdelta3](https://github.com/jmacd/xdelta-gpl/releases) na pasta `ferramentas`.

### Formato dos arquivos do jogo
A documentação técnica está nos comentários de `quickdat.py`, `datasets.py` e `creditos.py`: estrutura do `quickdat.arc`, as cópias (algumas compactadas) dentro do `datasets.arc`, o índice `index.ind` e a lista de relocação de ponteiros.

## Créditos
- Tradução, coordenação e testes: **Oblytoid**
- Ferramentas e apoio na tradução: Claude (Anthropic)
- Revisão e pesquisa: Gemini (Google)

## Licença
As ferramentas usam a licença MIT (arquivo [`LICENSE`](LICENSE)). Ela vale só para o código deste repositório, não para o jogo.

*Pitfall* é marca da Activision Publishing, Inc. Projeto de fãs, sem fins lucrativos e sem ligação com a Activision ou a Edge of Reality.
