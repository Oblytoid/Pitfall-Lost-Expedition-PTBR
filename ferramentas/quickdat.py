"""Leitura e escrita do quickdat.arc de Pitfall: The Lost Expedition (PS2, SLUS-20408).

Formato (descoberto em 09/10/2026):
  u32 tamanho_dos_registros
  N registros encadeados
  diretório: u32 N, depois N x (u32 hash, u32 ofs, u32 tam, nome\0, 8 bytes FILETIME)

Registro: 1..3 segmentos. Cabeçalho do segmento k em rec+k*0x18:
  [0x18, ofs, tam, fim, tam_trailer, 0x500000]
  dados em rec+ofs (tam bytes), fim = ofs + align4(tam), trailer em rec+fim.
Ponteiros: u32 0x500000 + endereço virtual. O segmento 0 tem os dados comuns
(endereço 0). Os segmentos 1..n são variantes de idioma: todos começam no mesmo
endereço virtual, logo após o segmento 0. O segmento 1 é o inglês; no registro
"savegametext" o segmento 2 é uma pseudo-tradução de teste ({{...XXXX}}) que não é usada.
Textos: UTF-16LE terminados em 00 00, apontados por ponteiros do próprio registro.
"""
import struct

TAG = 0x500000


def align4(n):
    return (n + 3) & ~3


class Segment:
    def __init__(self, ofs, size, end, tr, root):
        self.ofs, self.size, self.end, self.tr, self.root = ofs, size, end, tr, root


class Record:
    def __init__(self, raw, idx):
        self.idx = idx
        self.raw = raw
        h1 = struct.unpack_from('<I', raw, 4)[0]
        nseg = (h1 - 0x18) // 0x18 + 1
        self.segs = []
        for k in range(nseg):
            f = struct.unpack_from('<6I', raw, k * 0x18)
            assert f[0] == 0x18
            self.segs.append(Segment(*f[1:]))
        # sanidade: layout físico contíguo
        exp = self.segs[0].ofs
        for s in self.segs:
            assert s.ofs == exp, 'segmentos fora de ordem'
            assert s.end == s.ofs + align4(s.size)
            exp = s.end + s.tr
        assert exp == len(raw)
        lang = align4(self.segs[0].size)
        self.vbase = [0] + [lang] * (len(self.segs) - 1)
        self.data = [bytearray(raw[s.ofs:s.ofs + s.size]) for s in self.segs]
        self.trailers = [raw[s.end:s.end + s.tr] for s in self.segs]
        self._find_strings()

    def v2seg(self, v, origem):
        """Resolve endereço virtual visto de um ponteiro que está no segmento `origem`."""
        if v < self.segs[0].size:
            return 0, v
        k = origem if origem >= 1 else 1
        if k < len(self.segs) and self.vbase[k] <= v < self.vbase[k] + self.segs[k].size:
            return k, v - self.vbase[k]
        return None

    @staticmethod
    def _read_wide(buf, off):
        if off % 2 or off + 2 > len(buf):
            return None
        chars = []
        p = off
        while p + 2 <= len(buf):
            c = buf[p] | (buf[p + 1] << 8)
            if c == 0:
                break
            if not (c >= 0x20 or c in (9, 10, 13)) or c > 0xFF:
                return None
            chars.append(chr(c))
            p += 2
        else:
            return None
        if len(chars) < 1 or not any(ch.isalnum() or ch in '<>' for ch in chars):
            return None
        # rejeita ASCII comum lido como UTF-16 (ex.: bytes 'ab' viram U+6261, já barrado acima)
        return ''.join(chars), p + 2 - off

    def _find_strings(self):
        cands = []  # (seg, off_no_seg, alvo_seg, alvo_off)
        for k, buf in enumerate(self.data):
            for i in range(0, len(buf) - 3, 4):
                v = struct.unpack_from('<I', buf, i)[0]
                if v >> 20 != 5:
                    continue
                t = self.v2seg(v - TAG, k)
                if t is None:
                    continue
                cands.append((k, i, t[0], t[1]))
        strings = {}
        for k, i, ts, to in cands:
            if (ts, to) in strings:
                continue
            r = self._read_wide(self.data[ts], to)
            if r:
                strings[(ts, to)] = r
        # descarta ponteiros que estão dentro de um texto
        spans = {}
        for (ts, to), (_, ln) in strings.items():
            spans.setdefault(ts, []).append((to, to + ln))

        def inside(k, i):
            return any(a <= i < b for a, b in spans.get(k, []))
        self.ptrs = {}
        for k, i, ts, to in cands:
            if (ts, to) in strings and not inside(k, i):
                self.ptrs.setdefault((ts, to), []).append((k, i))
        # só textos do segmento comum e do idioma 1 (inglês)
        self.strings = [(key, strings[key][0], strings[key][1]) for key in sorted(self.ptrs) if key[0] <= 1]

    def build(self, novos, extra=None):
        """novos: dict {(seg, off): texto}. Retorna bytes do registro reconstruído.
        extra: função opcional extra(registro, data) chamada depois dos textos,
        que pode acrescentar dados no fim do segmento de idioma (ver creditos.py)."""
        data = [bytearray(b) for b in self.data]
        alvo = 1 if len(self.segs) > 1 else 0   # onde textos maiores são acrescentados
        tamanhos = {key: ln for key, _, ln in self.strings}
        for (ts, to), txt in novos.items():
            orig_len = tamanhos[(ts, to)]
            enc = txt.encode('latin-1').decode('latin-1').encode('utf-16-le') + b'\0\0'
            if len(enc) <= orig_len:
                data[ts][to:to + orig_len] = enc + b'\0' * (orig_len - len(enc))
                continue
            refs = self.ptrs[(ts, to)]
            if len(self.segs) > 2 and any(k == 0 for k, _ in refs):
                raise ValueError(f'registro {self.idx}: texto em {ts}:{to:#x} nao pode crescer')
            buf = data[alvo]
            while len(buf) % 4:
                buf += b'\0'
            newv = self.vbase[alvo] + len(buf)
            buf += enc
            for (k, i) in refs:
                struct.pack_into('<I', data[k], i, TAG + newv)
        trailers = list(self.trailers)
        if extra:
            extra(self, data, trailers)
        assert len(data[0]) == self.segs[0].size or len(self.segs) == 1
        hdr = bytearray(self.raw[:self.segs[0].ofs])
        pos = self.segs[0].ofs
        body = bytearray()
        for k, s in enumerate(self.segs):
            size = len(data[k])
            if size == s.size:
                pad = self.raw[s.ofs + s.size:s.end]
            else:
                pad = b'\0' * (align4(size) - size)
            end = pos + align4(size)
            tr = len(trailers[k])
            struct.pack_into('<4I', hdr, k * 0x18 + 4, pos, size, end, tr)
            body += data[k] + pad + trailers[k]
            pos = end + tr
        return bytes(hdr + body)


class QuickDat:
    def __init__(self, raw):
        self.raw = raw
        total = struct.unpack_from('<I', raw, 0)[0]
        pos = 4
        self.records = []
        while pos < total:
            h = struct.unpack_from('<6I', raw, pos)
            nseg = (h[1] - 0x18) // 0x18 + 1
            ln = max(struct.unpack_from('<I', raw, pos + k * 0x18 + 12)[0] +
                     struct.unpack_from('<I', raw, pos + k * 0x18 + 16)[0] for k in range(nseg))
            self.records.append(Record(raw[pos:pos + ln], len(self.records)))
            pos += ln
        assert pos == total
        # diretório
        n = struct.unpack_from('<I', raw, pos)[0]
        assert n == len(self.records)
        p = pos + 4
        self.dir = []
        for _ in range(n):
            hsh, ofs, size = struct.unpack_from('<3I', raw, p)
            e = raw.index(b'\0', p + 12)
            name = raw[p + 12:e]
            ft = raw[e + 1:e + 9]
            self.dir.append([hsh, ofs, size, name, ft])
            p = e + 9
        self.tail = raw[p:]
        for r, de in zip(self.records, self.dir):
            r.name = de[3].decode('ascii', 'replace')

    def build(self, novos_por_registro, extras=None):
        extras = extras or {}
        recs = []
        for r in self.records:
            nv = novos_por_registro.get(r.idx)
            ex = extras.get(r.idx)
            recs.append(r.build(nv or {}, ex) if (nv or ex) else r.raw)
        out = bytearray(struct.pack('<I', 0))
        pares = []
        for rb in recs:
            pares.append((len(out), len(rb)))
            out += rb
        struct.pack_into('<I', out, 0, len(out))
        out += struct.pack('<I', len(self.dir))
        for (hsh, _, _, name, ft), (ofs, size) in zip(self.dir, pares):
            out += struct.pack('<3I', hsh, ofs, size) + name + b'\0' + ft
        out += self.tail
        return bytes(out), pares


def atualizar_index(ind, pares_antigos, pares_novos):
    """Troca a tabela (ofs, tam) da seção QuickDatas do index.ind."""
    ind = bytearray(ind)
    antigo = b''.join(struct.pack('<2I', *p) for p in pares_antigos)
    i = ind.find(b'QuickDatas\0')
    assert i >= 0
    j = ind.find(antigo, i)
    assert j >= 0, 'tabela do QuickDatas não encontrada no index.ind'
    novo = b''.join(struct.pack('<2I', *p) for p in pares_novos)
    ind[j:j + len(novo)] = novo
    return bytes(ind)


# ---------- formato dos arquivos de texto ----------

def para_texto(s):
    s = s.replace('\r\n', '\x00')
    s = s.replace('\n', '{LF}').replace('\r', '{CR}').replace('\t', '{TAB}')
    return s.replace('\x00', '\n')


def de_texto(s):
    s = s.replace('\r\n', '\n')  # se o editor salvou com CRLF
    s = s.replace('\n', '\r\n')
    return s.replace('{LF}', '\n').replace('{CR}', '\r').replace('{TAB}', '\t')
