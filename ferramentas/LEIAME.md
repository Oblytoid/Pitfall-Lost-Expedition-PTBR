# Ferramentas - Pitfall: The Lost Expedition

Precisa do Python 3 instalado (https://www.python.org, marcar "Add Python to PATH").

| Arquivo | Para que serve |
|---------|----------------|
| `quickdat.py` | Biblioteca que entende o formato do quickdat.arc (usada pelos outros) |
| `datasets.py` | Biblioteca do datasets.arc, onde ficam as cópias dos textos de menu que o jogo realmente usa |
| `extrair.py` | Extrai os textos para arquivos `.txt` editáveis |
| `inserir.py` | Coloca os textos traduzidos de volta e gera novos `quickdat.arc`, `datasets.arc` e `index.ind` |
| `creditos.py` | Acrescenta "Tradução PT-BR / Oblytoid" no fim dos créditos do jogo (o texto fica no topo do arquivo) |
| `iso_substituir.py` | Coloca os arquivos novos dentro de uma cópia da ISO |
| `gerar_iso.bat` | Faz tudo de uma vez: inserir + montar a ISO de teste |
| `gerar_patch.py` / `gerar_patch.bat` | Cria o patch `.xdelta`, confere se ele reproduz a ISO traduzida, grava os códigos em `.hashes.txt` e monta o pacote `.zip` para distribuir |
| `modelo_aplicar.bat` | Modelo do "ARRASTE A ISO AQUI.bat" que vai no pacote (o jogador arrasta a ISO e pronto) |
| `diagnostico_iso.py` / `diagnostico.bat` | Mostra onde cada arquivo está dentro da ISO (usado para investigar a leitura dos arquivos) |

## Uso rápido
- **Dois cliques em `gerar_iso.bat`:** usa os textos da pasta `Jogos\Pitfall\script`.
- **Arrastar uma pasta para cima do `gerar_iso.bat`:** usa os textos dessa pasta (ex.: `teste_menu`).

O resultado fica em `Jogos\Pitfall\build\Pitfall_PTBR_teste.iso`. A ISO original nunca é alterada.

## Gerar o patch para distribuir
1. Baixe o xdelta3 para Windows em https://github.com/jmacd/xdelta-gpl/releases (arquivo `xdelta3-...-x86_64.exe.zip`), descompacte e coloque o `.exe` nesta pasta.
2. Rode o `gerar_iso.bat` e confira a ISO no PCSX2.
3. Dois cliques em `gerar_patch.bat`. Leva alguns minutos.
4. Em `Jogos\Pitfall\patch` ficam o `.xdelta`, o `.hashes.txt` e o **`.zip` pronto para distribuir**. O zip tem:
   - `ARRASTE A ISO AQUI.bat`: o jogador arrasta a ISO original em cima e recebe a traduzida (confere a ISO antes e o resultado depois);
   - `xdelta3.exe` e o `.xdelta`;
   - `LEIAME.txt`, feito a partir da nota "LEIAME - Patch" do cofre, com os códigos da ISO já preenchidos.

A versão do patch fica na linha `set "VERSAO=..."` do `gerar_patch.bat`.

## Segurança
- `inserir.py` se recusa a continuar se o texto ORIGINAL de algum bloco tiver sido editado sem querer.
- Avisa quando as tags (`<br>`, `<prompt ...>` etc.) da tradução não batem com as do original.
- Só aceita caracteres do Latin-1 (inclui á é í ó ú â ê ô ã õ ç à).

## Testado
- Extrair e reinserir sem mudanças gera arquivos idênticos ao original (byte a byte).
- 792 textos alterados de uma vez, muitos maiores que o original: todos os ponteiros conferidos.
