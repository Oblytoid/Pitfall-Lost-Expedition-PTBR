"""Substitui arquivos dentro de uma ISO de PS2 (ISO 9660) sem reconstruir a imagem toda.

Uso:
  python iso_substituir.py <iso_entrada> <iso_saida> CAMINHO_NA_ISO=arquivo_novo [...]

Exemplo:
  python iso_substituir.py original.iso teste.iso DATA/QUICKDAT.ARC=build/quickdat.arc DATA/INDEX.IND=build/index.ind

- A ISO de entrada nunca é alterada; a saída é uma cópia nova.
- Se o arquivo novo couber no espaço do antigo, ele é gravado no mesmo lugar.
- Se for maior, ele é gravado no fim da ISO e o diretório é atualizado.
"""
import os
import shutil
import struct
import sys

SETOR = 2048


def ler_setor(f, lba, n=1):
    f.seek(lba * SETOR)
    return f.read(n * SETOR)


def achar(f, caminho):
    pvd = ler_setor(f, 16)
    assert pvd[1:6] == b'CD001', 'não parece uma ISO 9660'
    raiz = pvd[156:156 + 34]
    lba, tam = struct.unpack_from('<I', raiz, 2)[0], struct.unpack_from('<I', raiz, 10)[0]
    partes = caminho.upper().replace('\\', '/').strip('/').split('/')
    for idx, nome in enumerate(partes):
        dados = ler_setor(f, lba, (tam + SETOR - 1) // SETOR)
        p = 0
        achou = None
        while p < tam:
            ln = dados[p]
            if ln == 0:
                p = (p // SETOR + 1) * SETOR
                continue
            nl = dados[p + 32]
            n = dados[p + 33:p + 33 + nl].decode('ascii', 'replace').split(';')[0]
            if n.upper() == nome:
                achou = (lba * SETOR + p, struct.unpack_from('<I', dados, p + 2)[0], struct.unpack_from('<I', dados, p + 10)[0])
                break
            p += ln
        if not achou:
            raise FileNotFoundError(caminho)
        pos_registro, lba, tam = achou
    return pos_registro, lba, tam


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    entrada, saida = sys.argv[1], sys.argv[2]
    pares = [a.split('=', 1) for a in sys.argv[3:]]
    if os.path.abspath(entrada) == os.path.abspath(saida):
        sys.exit('A saída precisa ser um arquivo diferente da entrada.')
    print('Copiando a ISO...')
    shutil.copyfile(entrada, saida)
    with open(saida, 'r+b') as f:
        for caminho, arquivo in pares:
            novo = open(arquivo, 'rb').read()
            reg, lba, tam = achar(f, caminho)
            espaco = (tam + SETOR - 1) // SETOR * SETOR
            if len(novo) <= espaco:
                f.seek(lba * SETOR)
                f.write(novo + b'\0' * (espaco - len(novo)))
                novo_lba = lba
                onde = 'no mesmo lugar'
            else:
                f.seek(0, 2)
                fim = f.tell()
                novo_lba = (fim + SETOR - 1) // SETOR
                f.seek(novo_lba * SETOR)
                f.write(novo)
                f.write(b'\0' * (-len(novo) % SETOR))
                onde = f'no fim da ISO (setor {novo_lba})'
                total = f.tell() // SETOR
                f.seek(16 * SETOR + 80)
                f.write(struct.pack('<I', total) + struct.pack('>I', total))
            f.seek(reg + 2)
            f.write(struct.pack('<I', novo_lba) + struct.pack('>I', novo_lba))
            f.write(struct.pack('<I', len(novo)) + struct.pack('>I', len(novo)))
            print(f'{caminho}: {tam} -> {len(novo)} bytes, gravado {onde}')
    print('Pronto:', saida)


if __name__ == '__main__':
    main()
