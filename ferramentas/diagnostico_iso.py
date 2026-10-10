"""Diagnóstico: mostra onde cada arquivo está na ISO (setor/LBA) e procura esses
números dentro do executável e do index.ind, para descobrir se o jogo acha os
arquivos por posição fixa no disco.

Uso (dois cliques no diagnostico.bat, ou):
  python diagnostico_iso.py <iso_original> <iso_teste> <pasta_extraida>
Gera diagnostico.txt ao lado deste script.
"""
import os
import struct
import sys

SETOR = 2048


def listar(iso):
    out = {}
    with open(iso, 'rb') as f:
        def ler(lba, n):
            f.seek(lba * SETOR)
            return f.read(n)
        pvd = ler(16, SETOR)
        raiz = pvd[156:190]

        def walk(lba, tam, prefixo):
            dados = ler(lba, tam)
            p = 0
            while p < tam:
                ln = dados[p]
                if ln == 0:
                    p = (p // SETOR + 1) * SETOR
                    continue
                elba = struct.unpack_from('<I', dados, p + 2)[0]
                etam = struct.unpack_from('<I', dados, p + 10)[0]
                flags = dados[p + 25]
                nl = dados[p + 32]
                nome = dados[p + 33:p + 33 + nl]
                if nome not in (b'\0', b'\1'):
                    n = prefixo + nome.decode('ascii', 'replace').split(';')[0]
                    if flags & 2:
                        walk(elba, etam, n + '/')
                    else:
                        out[n] = (elba, etam)
                p += ln
        walk(struct.unpack_from('<I', raiz, 2)[0], struct.unpack_from('<I', raiz, 10)[0], '')
    return out


def main():
    aqui = os.path.dirname(os.path.abspath(__file__))
    iso_o, iso_t, pasta = sys.argv[1:4]
    o, t = listar(iso_o), listar(iso_t)
    linhas = ['ARQUIVO | ISO ORIGINAL (LBA, tamanho) | ISO TESTE (LBA, tamanho)']
    for n in sorted(o):
        linhas.append(f'{n} | {o[n]} | {t.get(n)}')
    linhas.append('')
    alvos = {}
    for n, (lba, tam) in o.items():
        alvos[lba] = f'LBA de {n}'
    for nome in ['SLUS_204.08', 'EoRps2io.irx', 'data/index.ind', 'SYSTEM.CNF']:
        cam = os.path.join(pasta, *nome.split('/'))
        if not os.path.exists(cam):
            linhas.append(f'(não encontrado: {cam})')
            continue
        d = open(cam, 'rb').read()
        achou = 0
        for i in range(0, len(d) - 3):
            v = struct.unpack_from('<I', d, i)[0]
            if v in alvos and v > 100:
                linhas.append(f'{nome} @ {i:#x}: {v} = {alvos[v]}')
                achou += 1
                if achou > 60:
                    linhas.append('... (muitos resultados, cortado)')
                    break
        if not achou:
            linhas.append(f'{nome}: nenhum LBA encontrado')
    saida = os.path.join(aqui, 'diagnostico.txt')
    open(saida, 'w', encoding='utf-8').write('\n'.join(linhas))
    print('\n'.join(linhas))
    print('\nSalvo em', saida)


if __name__ == '__main__':
    main()
