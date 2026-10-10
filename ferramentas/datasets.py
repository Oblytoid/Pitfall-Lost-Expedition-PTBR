"""Leitura e reconstrução do datasets.arc de Pitfall: The Lost Expedition (PS2).

Formato (mapeado em 09/10/2026):
  u32 fim_dos_dados, zeros até 0x1000
  266 conjuntos ("datasets"), cada um começando num múltiplo de 0x1000
  diretório: u32 N, depois N x (u32 hash, u32 posição, u32 tamanho, nome\\0, 8 bytes de data)

Cada conjunto é uma sequência de seções (Textures, Shaders, Fonts, QuickDatas...).
A seção QuickDatas (geralmente a última):
  "QuickDatas\\0", u32 N, N x (u32 hash, u32 tamanho, u32 0, dados)
10 conjuntos são compactados em blocos ZIP de 64 KB (ex.: "credits", ver _descompactar).
Os registros dentro dela são cópias idênticas dos registros do quickdat.arc
(mesmo hash do diretório do quickdat.arc). O jogo lê os textos de menu daqui.
"""
import struct
import zlib

ALINHAMENTO = 0x1000


class Datasets:
    def __init__(self, raw):
        self.raw = raw
        total = struct.unpack_from('<I', raw, 0)[0]
        n = struct.unpack_from('<I', raw, total)[0]
        p = total + 4
        self.dir = []
        for _ in range(n):
            h, o, s = struct.unpack_from('<3I', raw, p)
            e = raw.index(b'\0', p + 12)
            self.dir.append([h, o, s, raw[p + 12:e], raw[e + 1:e + 9]])
            p = e + 9
        self.tail = raw[p:]

    def pares(self):
        return [(d[1], d[2]) for d in self.dir]

    @staticmethod
    def _trocar_quickdatas(ds, novos_por_hash):
        i = ds.rfind(b'QuickDatas\0')
        if i < 0:
            return ds, 0
        q = i + 11
        n = struct.unpack_from('<I', ds, q)[0]
        out = bytearray(ds[:q + 4])
        q += 4
        trocados = 0
        for _ in range(n):
            h, sz, z = struct.unpack_from('<3I', ds, q)
            dado = ds[q + 12:q + 12 + sz]
            if h in novos_por_hash:
                dado = novos_por_hash[h]
                trocados += 1
            out += struct.pack('<3I', h, len(dado), z) + dado
            q += 12 + sz
        out += ds[q:]   # em alguns conjuntos (ex.: "0-kreitler") há seções depois
        return bytes(out), trocados

    # ---- conjuntos compactados (10 de 266, ex.: "credits") ----
    # formato: cabeçalho [u32 tam_cab, 5 bytes, u32, nome\0], depois blocos
    # [u32 tam][cabeçalho local ZIP de 30 bytes (crc 0)][deflate cru], 64 KB descompactados cada.
    @staticmethod
    def _compactado(ds):
        if len(ds) < 8:
            return False
        tam_cab = struct.unpack_from('<I', ds, 0)[0]
        return tam_cab < 64 and ds[tam_cab + 4:tam_cab + 8] == b'PK\x03\x04'

    @staticmethod
    def _descompactar(ds):
        tam_cab = struct.unpack_from('<I', ds, 0)[0]
        p = tam_cab
        out = bytearray()
        while p < len(ds):
            ln = struct.unpack_from('<I', ds, p)[0]
            ent = ds[p + 4:p + 4 + ln]
            sig, _, _, meth, _, _, _, cs, us, nl, xl = struct.unpack_from('<IHHHHHIIIHH', ent, 0)
            assert sig == 0x04034b50 and meth == 8
            dados = zlib.decompress(ent[30 + nl + xl:30 + nl + xl + cs], -15)
            assert len(dados) == us
            out += dados
            p += 4 + ln
        return ds[:tam_cab], bytes(out)

    @staticmethod
    def _compactar(cab, dados, bloco=0x10000):
        out = bytearray(cab)
        for i in range(0, len(dados), bloco):
            parte = dados[i:i + bloco]
            c = zlib.compressobj(9, zlib.DEFLATED, -15)
            comp = c.compress(parte) + c.flush()
            local = struct.pack('<IHHHHHIIIHH', 0x04034b50, 0, 0, 8, 0, 0, 0, len(comp), len(parte), 0, 0)
            out += struct.pack('<I', len(local) + len(comp)) + local + comp
        return bytes(out)

    def build(self, novos_por_hash):
        """novos_por_hash: {hash_do_registro: bytes_novos}. Retorna (bytes, pares_novos, trocados)."""
        if not novos_por_hash:
            return self.raw, self.pares(), 0
        out = bytearray(ALINHAMENTO)
        pares = []
        trocados = 0
        for h, o, s, nome, ft in self.dir:
            ds = self.raw[o:o + s]
            if self._compactado(ds):
                cab, dados = self._descompactar(ds)
                novo, t = self._trocar_quickdatas(dados, novos_por_hash)
                if t:
                    ds = self._compactar(cab, novo)
            else:
                ds, t = self._trocar_quickdatas(ds, novos_por_hash)
            trocados += t
            if len(out) % ALINHAMENTO:
                out += b'\0' * (ALINHAMENTO - len(out) % ALINHAMENTO)
            pares.append((len(out), len(ds)))
            out += ds
        struct.pack_into('<I', out, 0, len(out))
        out += struct.pack('<I', len(self.dir))
        for (h, _, _, nome, ft), (o, s) in zip(self.dir, pares):
            out += struct.pack('<3I', h, o, s) + nome + b'\0' + ft
        out += self.tail
        return bytes(out), pares, trocados
