"""Insere os textos traduzidos e gera novos quickdat.arc, datasets.arc e index.ind.

Uso:
  python inserir.py <pasta data original> <pasta_textos> <pasta_saida>

<pasta data original> é a pasta "data" extraída da ISO (com quickdat.arc,
datasets.arc e index.ind). Ela nunca é alterada: o resultado vai para <pasta_saida>.

Os textos ficam em dois lugares no jogo:
  - quickdat.arc (todos os registros)
  - datasets.arc (cópias dos registros de menu/interface, nos conjuntos
    "bootstrap", "global" e "legalscreen") ← é daqui que o jogo lê os menus
O script atualiza os dois e as duas tabelas do index.ind.
"""
import glob
import os
import re
import sys

import creditos
from datasets import Datasets
from quickdat import QuickDat, de_texto

BLOCO = re.compile(r'^#### (\d{3})-(\d{4})\n(.*?)\n#### PT\n(.*?)\n#### FIM$', re.S | re.M)
# <EMPTY> é texto visível (slot vazio do memory card), não tag: fica fora da conferência
TAG = re.compile(r'<(?!EMPTY>|VAZIO>)[^>]*>|\{(?:LF|CR|TAB)\}')


def trocar_tabela(ind, antigos, novos, nome):
    import struct
    a = b''.join(struct.pack('<2I', *p) for p in antigos)
    n = b''.join(struct.pack('<2I', *p) for p in novos)
    j = ind.find(a)
    if j < 0 or ind.find(a, j + 1) >= 0:
        sys.exit(f'ERRO: tabela do {nome} não encontrada (ou repetida) no index.ind')
    ind[j:j + len(n)] = n


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    data, pasta, saida = sys.argv[1:]
    qd = QuickDat(open(os.path.join(data, 'quickdat.arc'), 'rb').read())
    novos = {}
    alterados = avisos = 0
    for fn in sorted(glob.glob(os.path.join(pasta, '*.txt'))):
        conteudo = open(fn, encoding='utf-8-sig').read().replace('\r\n', '\n')
        for m in BLOCO.finditer(conteudo):
            ri, n, orig, pt = int(m[1]), int(m[2]), m[3], m[4]
            r = qd.records[ri]
            key, txt, _ = r.strings[n]
            if de_texto(orig) != txt:
                sys.exit(f'ERRO {ri:03d}-{n:04d}: o texto original foi alterado ({os.path.basename(fn)})')
            if TAG.findall(orig) != TAG.findall(pt):
                print(f'AVISO {ri:03d}-{n:04d}: as tags/codigos da traducao nao batem com o original')
                avisos += 1
            novo = de_texto(pt)
            if novo != txt:
                bad = [c for c in novo if ord(c) > 0xFF]
                if bad:
                    sys.exit(f'ERRO {ri:03d}-{n:04d}: caracteres nao suportados: {"".join(set(bad))}')
                novos.setdefault(ri, {})[key] = novo
                alterados += 1

    # quickdat.arc
    pares_q_antigos = [(d[1], d[2]) for d in qd.dir]
    # crédito da tradução no fim dos créditos (registro "credits")
    extras = {}
    for r in qd.records:
        if r.name == 'credits':
            extras[r.idx] = creditos.adicionar
    if not extras:
        sys.exit('ERRO: registro "credits" não encontrado')
    novo_q, pares_q = qd.build(novos, extras)

    # registros alterados, por hash, para o datasets.arc
    por_hash = {}
    for ri in set(novos) | set(extras):
        o, s = pares_q[ri]
        por_hash[qd.dir[ri][0]] = novo_q[o:o + s]

    print('Lendo datasets.arc (255 MB)...')
    ds = Datasets(open(os.path.join(data, 'datasets.arc'), 'rb').read())
    pares_d_antigos = ds.pares()
    novo_d, pares_d, trocados = ds.build(por_hash)

    ind = bytearray(open(os.path.join(data, 'index.ind'), 'rb').read())
    trocar_tabela(ind, pares_q_antigos, pares_q, 'quickdat.arc')
    if novo_d is not ds.raw:
        trocar_tabela(ind, pares_d_antigos, pares_d, 'datasets.arc')

    os.makedirs(saida, exist_ok=True)
    open(os.path.join(saida, 'quickdat.arc'), 'wb').write(novo_q)
    open(os.path.join(saida, 'datasets.arc'), 'wb').write(novo_d)
    open(os.path.join(saida, 'index.ind'), 'wb').write(bytes(ind))
    print(f'{alterados} textos alterados, {avisos} avisos.')
    print(f'quickdat.arc: {len(qd.raw)} -> {len(novo_q)} bytes')
    print(f'datasets.arc: {len(ds.raw)} -> {len(novo_d)} bytes ({trocados} copias de registros atualizadas)')


if __name__ == '__main__':
    main()
