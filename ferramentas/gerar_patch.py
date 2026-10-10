"""Gera o patch .xdelta da tradução e calcula os códigos de verificação.

Uso:
  python gerar_patch.py <iso_original> <iso_traduzida> <saida.xdelta> [versao] [leiame.md]

Precisa do xdelta3 para Windows na mesma pasta deste script (xdelta3.exe ou
xdelta3-*.exe). Baixe em https://github.com/jmacd/xdelta-gpl/releases.

O script:
  1. calcula CRC32, MD5 e SHA-1 da ISO original e da traduzida;
  2. gera o .xdelta com janela grande (necessária porque parte dos arquivos
     modificados fica no fim da ISO, longe da posição original);
  3. aplica o patch numa cópia temporária e confere se o resultado é idêntico;
  4. grava tudo em <saida>.hashes.txt;
  5. monta o pacote para distribuir (pasta e .zip com o mesmo nome do patch):
     "ARRASTE A ISO AQUI.bat", xdelta3.exe, o .xdelta e o LEIAME.txt com os
     códigos já preenchidos. O jogador só arrasta a ISO para cima do .bat.
"""
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
import zlib


def hashes(caminho):
    md5, sha1, crc = hashlib.md5(), hashlib.sha1(), 0
    tam = os.path.getsize(caminho)
    lido = 0
    with open(caminho, 'rb') as f:
        while True:
            bloco = f.read(8 * 1024 * 1024)
            if not bloco:
                break
            md5.update(bloco)
            sha1.update(bloco)
            crc = zlib.crc32(bloco, crc)
            lido += len(bloco)
            print(f'\r  {os.path.basename(caminho)}: {lido * 100 // tam}%', end='', flush=True)
    print()
    return {'tamanho': tam, 'crc32': f'{crc & 0xFFFFFFFF:08X}', 'md5': md5.hexdigest(), 'sha1': sha1.hexdigest()}


def achar_xdelta():
    """Procura o xdelta3 na pasta ferramentas ou numa subpasta (o .zip oficial
    descompacta numa pasta com o mesmo nome do .exe)."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    for padrao in ('xdelta3*.exe', os.path.join('*', 'xdelta3*.exe')):
        achados = sorted(c for c in glob.glob(os.path.join(aqui, padrao)) if os.path.isfile(c))
        if achados:
            return achados[0]
    sys.exit('xdelta3 não encontrado. Baixe em https://github.com/jmacd/xdelta-gpl/releases '
             '(arquivo xdelta3-...-x86_64.exe.zip), descompacte e coloque o .exe na pasta ferramentas.')


def main():
    if len(sys.argv) not in (4, 5, 6):
        print(__doc__)
        sys.exit(1)
    orig, trad, saida = sys.argv[1:4]
    versao = sys.argv[4] if len(sys.argv) > 4 else ''
    leiame = sys.argv[5] if len(sys.argv) > 5 else ''
    xd = achar_xdelta()
    print('1/5 Calculando códigos da ISO original...')
    h_o = hashes(orig)
    print('2/5 Calculando códigos da ISO traduzida...')
    h_t = hashes(trad)
    print('3/5 Gerando o patch (pode levar alguns minutos)...')
    janela = str(2 ** 30)  # 1 GB: acha os dados repetidos mesmo longe na ISO
    subprocess.run([xd, '-e', '-f', '-9', '-B', janela, '-s', orig, trad, saida], check=True)
    print('4/5 Conferindo: aplicando o patch numa cópia temporária...')
    tmp = saida + '.teste.iso'
    # mesmo comando do .bat do jogador (sem -B), para conferir o que ele vai rodar
    subprocess.run([xd, '-d', '-f', '-s', orig, saida, tmp], check=True)
    h_c = hashes(tmp)
    os.remove(tmp)
    ok = h_c['sha1'] == h_t['sha1']
    linhas = [
        'ISO ORIGINAL (necessária para aplicar o patch)',
        f"  Tamanho: {h_o['tamanho']:,} bytes".replace(',', '.'),
        f"  CRC32:   {h_o['crc32']}",
        f"  MD5:     {h_o['md5']}",
        f"  SHA-1:   {h_o['sha1']}",
        '',
        'ISO TRADUZIDA (resultado depois de aplicar o patch)',
        f"  Tamanho: {h_t['tamanho']:,} bytes".replace(',', '.'),
        f"  CRC32:   {h_t['crc32']}",
        f"  MD5:     {h_t['md5']}",
        f"  SHA-1:   {h_t['sha1']}",
        '',
        f"PATCH: {os.path.basename(saida)} ({os.path.getsize(saida):,} bytes)".replace(',', '.'),
        f"Conferência (aplicar o patch gera exatamente a ISO traduzida): {'OK' if ok else 'FALHOU'}",
    ]
    open(saida + '.hashes.txt', 'w', encoding='utf-8').write('\n'.join(linhas) + '\n')
    print('\n'.join(linhas))
    if not ok:
        sys.exit('ERRO: o patch não reproduz a ISO traduzida. Não distribua este arquivo.')
    print('5/5 Montando o pacote para distribuir...')
    montar_pacote(xd, saida, versao, leiame, h_o, h_t)


def leiame_txt(md, h_o):
    t = open(md, encoding='utf-8').read()
    t = re.sub(r'\A---\n.*?\n---\n', '', t, flags=re.S)
    t = re.sub(r'<!--.*?-->\n?', '', t, flags=re.S)
    for campo in ('crc32', 'md5', 'sha1'):
        nome = {'crc32': 'CRC32', 'md5': 'MD5', 'sha1': 'SHA-1'}[campo]
        t = re.sub(r'(\*\*' + nome + r':\*\* `)PREENCHER(`)', lambda m: m.group(1) + h_o[campo] + m.group(2), t)
    if 'PREENCHER' in t:
        sys.exit('ERRO: ainda há PREENCHER no LEIAME depois de colocar os códigos.')
    for de, para in (('[!NOTE]', 'Nota:'), ('[!IMPORTANT]', 'Importante:'), ('[!WARNING]', 'Atenção:')):
        t = t.replace(de, para)
    return t.strip() + '\n'


def montar_pacote(xd, saida, versao, leiame, h_o, h_t):
    aqui = os.path.dirname(os.path.abspath(__file__))
    base = os.path.splitext(os.path.basename(saida))[0]
    pasta = os.path.join(os.path.dirname(os.path.abspath(saida)), base)
    if os.path.isdir(pasta):
        shutil.rmtree(pasta)
    os.makedirs(pasta)
    shutil.copy2(saida, pasta)
    shutil.copy2(xd, os.path.join(pasta, 'xdelta3.exe'))
    bat = open(os.path.join(aqui, 'modelo_aplicar.bat'), encoding='utf-8').read()
    for chave, valor in (('__PATCH__', os.path.basename(saida)), ('__SHA_ORIG__', h_o['sha1']),
                         ('__SHA_TRAD__', h_t['sha1']), ('__VERSAO__', versao)):
        bat = bat.replace(chave, valor)
    with open(os.path.join(pasta, 'ARRASTE A ISO AQUI.bat'), 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(bat.replace('\r\n', '\n'))
    if leiame and not os.path.isfile(leiame):
        print(f'  AVISO: LEIAME não encontrado ({leiame}); o pacote vai sem LEIAME.txt')
        leiame = ''
    if leiame:
        with open(os.path.join(pasta, 'LEIAME.txt'), 'w', encoding='utf-8-sig', newline='\r\n') as f:
            f.write(leiame_txt(leiame, h_o))
    else:
        print('  (sem LEIAME: nenhum arquivo informado)')
    arq_zip = pasta + '.zip'
    with zipfile.ZipFile(arq_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for nome in sorted(os.listdir(pasta)):
            z.write(os.path.join(pasta, nome), os.path.join(base, nome))
    print(f'  Pacote: {arq_zip} ({os.path.getsize(arq_zip):,} bytes)'.replace(',', '.'))


if __name__ == '__main__':
    main()
