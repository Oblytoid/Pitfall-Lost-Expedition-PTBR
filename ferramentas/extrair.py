"""Extrai os textos do quickdat.arc para arquivos .txt editáveis.

Uso:
  python extrair.py <quickdat.arc> <pasta_saida>

Cada arquivo tem blocos assim:
  #### 037-0012
  texto original
  #### PT
  tradução (começa igual ao original)
  #### FIM

Só edite o texto entre "#### PT" e "#### FIM".
Códigos especiais: quebra de linha normal = nova linha; {LF} {CR} {TAB} = caracteres
de controle que o jogo usa e devem ser mantidos.
"""
import os
import re
import sys

from quickdat import QuickDat, para_texto

MAX_POR_LOTE = 120


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    arc, saida = sys.argv[1], sys.argv[2]
    os.makedirs(saida, exist_ok=True)
    qd = QuickDat(open(arc, 'rb').read())
    total = 0
    resumo = []
    for r in qd.records:
        # ignora "textos" que são só dados binários (ex.: "<", "6", "C"); a numeração não muda
        reais = [x for x in r.strings if re.search(r'[A-Za-zÀ-ÿ]{2}', x[1])]
        if not reais:
            continue
        nome = re.sub(r'[^A-Za-z0-9_-]+', '_', r.name)
        partes = [reais[i:i + MAX_POR_LOTE] for i in range(0, len(reais), MAX_POR_LOTE)]
        for pi, parte in enumerate(partes, 1):
            suf = f'_parte{pi}' if len(partes) > 1 else ''
            fn = f'{r.idx:03d}_{nome}{suf}.txt'
            linhas = [f'# Pitfall: The Lost Expedition - quickdat.arc - registro {r.idx:03d} ({r.name}){" parte " + str(pi) if suf else ""}',
                      '# Edite somente o texto entre "#### PT" e "#### FIM". Nao altere as linhas que comecam com ####.',
                      '']
            for (seg, off), txt, _ in parte:
                n = r.strings.index(((seg, off), txt, _))
                ident = f'{r.idx:03d}-{n:04d}'
                t = para_texto(txt)
                linhas += [f'#### {ident}', t, '#### PT', t, '#### FIM', '']
            with open(os.path.join(saida, fn), 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(linhas))
            resumo.append((fn, len(parte)))
            total += len(parte)
    for fn, n in resumo:
        print(f'{fn}: {n} textos')
    print(f'Total: {total} textos em {len(resumo)} arquivos')


if __name__ == '__main__':
    main()
