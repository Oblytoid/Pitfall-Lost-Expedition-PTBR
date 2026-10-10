"""Acrescenta o crédito da tradução no fim dos créditos do jogo.

O registro "credits" (quickdat 032) tem uma tabela "CreditsLine" no segmento 0:
446 entradas de 0x14 bytes [ordem, tipo, ponteiro_texto, ponteiro_titulo, 0].
  tipo 0 = título do grupo (ponteiro_titulo -> ref -> slot -> texto)
  tipo 1 = linha com nome  (ponteiro_texto -> slot -> texto)
  tipo 2 = espaço entre grupos
  tipo 3 = texto da Dolby
O descritor da tabela fica logo depois do nome "CreditsLine":
  [nome, ponteiro_da_tabela, 0, quantidade, 0x14]
Como o segmento 0 não pode crescer sem deslocar tudo, a tabela é copiada para o
fim do segmento de idioma com as entradas novas, e o descritor passa a apontar
para a cópia.

Trailer = lista de relocação: posições (em ordem decrescente) das palavras do
segmento que são ponteiros e que o jogo corrige ao carregar. Bit 0 ligado = todos
os ponteiros dali até a próxima posição da lista; bit 1 = ponteiro também em +4.
No segmento de idioma a lista original é [0x891, 0]: os ponteiros de 0 a 0x890
(a tabela de slots dos textos). Os ponteiros novos precisam entrar nessa lista,
senão o jogo usa o valor cru e trava (testado em 09/10/2026).
"""
import struct

from quickdat import TAG

TITULO = 'Tradução PT-BR'
NOMES = ['Oblytoid']


def _u32(buf, o):
    return struct.unpack_from('<I', buf, o)[0]


def _ler(registro, data, v):
    k, o = registro.v2seg(v - TAG, 1)
    return data[k], o


def adicionar(registro, data, trailers, titulo=TITULO, nomes=NOMES):
    d0 = data[0]
    nome = b'CreditsLine\0'
    a = d0.find(nome)
    assert a >= 0, 'CreditsLine não encontrado'
    alvo = struct.pack('<I', TAG + a)
    p = d0.find(alvo)
    assert p >= 0 and p % 4 == 0, 'descritor do CreditsLine não encontrado'
    tab, zero, qtd, tam = struct.unpack_from('<4I', d0, p + 4)
    assert zero == 0 and tam == 0x14 and 100 < qtd < 2000, 'descritor inesperado'
    k, o = registro.v2seg(tab - TAG, 0)
    entradas = [list(struct.unpack_from('<5I', data[k], o + i * 0x14)) for i in range(qtd)]
    ultimo_titulo = [e for e in entradas if e[1] == 0][-1]
    ultimo_espaco = [e for e in entradas if e[1] == 2][-1]
    ordem = max(e[0] for e in entradas)

    buf = data[1]
    novos_ptrs = []   # posições (no segmento 1) de ponteiros novos

    def alinhar():
        while len(buf) % 4:
            buf.append(0)

    def acrescentar(b):
        alinhar()
        v = registro.vbase[1] + len(buf)
        buf.extend(b)
        return TAG + v

    def texto(s):
        return acrescentar(s.encode('latin-1').decode('latin-1').encode('utf-16-le') + b'\0\0')

    def ponteiro(v):
        alinhar()
        novos_ptrs.append(len(buf))
        return acrescentar(struct.pack('<I', v))

    slot_t = ponteiro(texto(titulo))
    ref_t = ponteiro(slot_t)
    novas = [[ordem + 10, 0, ultimo_titulo[2], ref_t, 0]]
    for n, nm in enumerate(nomes, 1):
        slot = ponteiro(texto(nm))
        novas.append([ordem + 10 + n, 1, slot, 0, 0])
    novas.append([ordem + 30, 2, ultimo_espaco[2], 0, 0])

    todas = entradas + novas
    alinhar()
    inicio = len(buf)
    nova_tab = acrescentar(b''.join(struct.pack('<5I', *e) for e in todas))
    for i, e in enumerate(todas):
        for campo in (2, 3):
            if e[campo]:
                novos_ptrs.append(inicio + i * 0x14 + campo * 4)

    # lista de relocação do segmento 1: novas posições na frente (ordem decrescente)
    antiga = trailers[1]
    lista = list(struct.unpack(f'<{len(antiga) // 4}I', antiga))
    assert lista and lista[-1] == 0 and all(o > max(lista[:1] + [0]) for o in novos_ptrs)
    trailers[1] = struct.pack(f'<{len(novos_ptrs) + len(lista)}I', *sorted(novos_ptrs, reverse=True), *lista)
    struct.pack_into('<I', d0, p + 4, nova_tab)
    struct.pack_into('<I', d0, p + 12, len(todas))
