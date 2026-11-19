"""Uji Irisan 3 — Lispy 2: tipe & sintaks.

Symbol ter-intern, InPort regex (string, komentar, #t/#f,
kompleks, notasi ' ` , ,@), to_string, eval lugas di atasnya.
Jangkar dari artikel lispy2: contoh komentar di tengah daftar,
(sqrt -1) -> 1i, (* 1i 1i) -> (-1+0i), REPL multi-baris.
"""

import io
import subprocess
import sys

sys.path.insert(0, ".")
from lispy2 import (InPort, Sym, Symbol, atom, eof_object, eval,
                    parse, read, to_string)

LULUS = 0
GAGAL = []


def cek(nama, fn):
    global LULUS
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        GAGAL.append((nama, repr(e)))
        print(f"GAGAL  {nama}: {e!r}")
    else:
        LULUS += 1
        print(f"ok     {nama}")


def ev(sumber):
    return eval(parse(sumber))


def uji_symbol_intern():
    assert Sym("foo") is Sym("foo")
    assert isinstance(Sym("foo"), str)
    assert isinstance(Sym("foo"), Symbol)
    # simbol dari parser adalah objek yang sama dengan intern manual
    assert parse("foo") is Sym("foo")
    # kepala bentuk khusus dikenali lewat identitas
    assert parse("(quote x)")[0] is Sym("quote")
    # string biasa BUKAN simbol
    assert not isinstance("foo", Symbol)


def uji_atom_tipe_baru():
    assert atom("#t") is True
    assert atom("#f") is False
    assert atom('"halo dunia"') == "halo dunia"
    assert atom(r'"a\nb\"c"') == 'a\nb"c'
    assert atom("3+4i") == 3 + 4j
    assert atom("1i") == 1j
    assert atom("42") == 42
    assert atom("-3.14e159") == -3.14e159
    assert atom("xyz") is Sym("xyz")


def uji_string_satu_token():
    # spasi di dalam string tidak memecah token (regex tokenizer)
    assert parse('"satu dua tiga"') == "satu dua tiga"
    assert ev('(define s "halo dunia")') is None
    assert ev("s") == "halo dunia"


def uji_komentar_artikel():
    # contoh persis artikel: komentar di tengah daftar yang dikutip
    sumber = ("'(1 ;test comments '\n"
              "     ;skip this line\n"
              "     2 ; more ; comments ; ) )\n"
              "     3) ; final comment")
    assert to_string(ev(sumber)) == "(1 2 3)"
    # komentar satu baris penuh sebelum ekspresi dilewati reader
    assert ev("; hanya komentar\n(+ 2 2)") == 4


def uji_port_ganda_dan_eof():
    port = InPort(io.StringIO("(+ 1 1) ; komentar\n(+ 2 2)"))
    assert eval(read(port)) == 2
    assert eval(read(port)) == 4
    assert read(port) is eof_object
    kosong = InPort(io.StringIO(""))
    assert read(kosong) is eof_object


def uji_ekspresi_multi_baris():
    # contoh REPL artikel: define membentang dua baris, terbaca utuh.
    # Sejak Irisan 4 parse() juga meng-expand: gula (define (f x) ...)
    # kini langsung menjadi (define f (lambda (x) ...)).
    port = InPort(io.StringIO("(define (cube-sementara x)\n  (* x x))"))
    pohon = read(port)
    assert to_string(pohon) == "(define (cube-sementara x) (* x x))"
    from lispy2 import expand
    assert to_string(expand(pohon, toplevel=True)) == \
        "(define cube-sementara (lambda (x) (* x x)))"


def uji_notasi_kutip():
    assert to_string(parse("'x")) == "(quote x)"
    assert to_string(parse("'(one 2 3)")) == "(quote (one 2 3))"
    # struktur quasiquote diperiksa di tingkat READER (read);
    # sejak Irisan 4, parse() meneruskannya ke expand() yang
    # mengembangkannya menjadi rangkaian cons/append.
    port = InPort(io.StringIO("`(a ,b ,@c)"))
    assert to_string(read(port)) == \
        "(quasiquote (a (unquote b) (unquote-splicing c)))"
    assert to_string(parse("`(a ,b ,@c)")) == \
        "(cons (quote a) (cons b (append c (quote ()))))"
    assert ev("'x") is Sym("x")
    assert to_string(ev("'(one 2 3)")) == "(one 2 3)"


def uji_to_string_semua_tipe():
    assert to_string(True) == "#t"
    assert to_string(False) == "#f"
    assert to_string(Sym("abc")) == "abc"
    assert to_string("abc") == '"abc"'
    assert to_string('a"b\n') == '"a\\"b\\n"'
    assert to_string([1, "dua", True, Sym("tiga")]) == '(1 "dua" #t tiga)'
    assert to_string(1j) == "1i"
    assert to_string(-1 + 0j) == "(-1+0i)"
    assert to_string(2.5) == "2.5"
    # Bentuk tampil kompleks campuran (3+4i) memang hanya untuk
    # dibaca manusia — sama seperti aslinya, ia tidak bisa dibaca
    # balik sebagai satu atom (tanda kurungnya jadi daftar).
    assert to_string(3 + 4j) == "(3+4i)"
    # round-trip: to_string lalu parse menghasilkan nilai yang sama
    for nilai in (True, False, "halo dunia", [1, [2, 3], "x"], 1j):
        assert ev("(quote %s)" % to_string(nilai)) == nilai or \
            to_string(ev("(quote %s)" % to_string(nilai))) == to_string(nilai)


def uji_boolean_dan_if():
    assert ev("(if #t 1 2)") == 1
    assert ev("(if #f 1 2)") == 2
    assert ev("(not #f)") is True
    assert ev("(boolean? #t)") is True
    assert ev("(boolean? 1)") is False
    assert ev("(boolean? (quote x))") is False


def uji_kompleks_artikel():
    assert to_string(ev("(* 1i 1i)")) == "(-1+0i)"
    assert to_string(ev("(sqrt -1)")) == "1i"
    assert ev("(number? 3+4i)") is True


def uji_error_reader():
    for sumber, pesan in ((")", "unexpected )"), ("(1 2", "unexpected EOF")):
        try:
            parse(sumber)
        except SyntaxError as e:
            assert pesan in str(e), (sumber, e)
        else:
            raise AssertionError(f"{sumber!r} harus SyntaxError")


def uji_program_v1_tetap_jalan():
    # regresi semantik dasar di atas reader baru
    assert ev("(+ (* 2 100) (* 1 10))") == 210
    ev("(define fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))")
    assert ev("(fact 10)") == 3628800
    assert ev("(begin (define r 10) (* pi (* r r)))") == 314.1592653589793


def uji_regresi_v1():
    for berkas in ("uji_irisan1.py", "uji_irisan2.py"):
        hasil = subprocess.run([sys.executable, berkas],
                               capture_output=True, text=True, timeout=120)
        assert hasil.returncode == 0, (berkas, hasil.stdout, hasil.stderr)


if __name__ == "__main__":
    for nama, fn in sorted(dict(globals()).items()):
        if nama.startswith("uji_"):
            cek(nama, fn)
    print(f"\n{LULUS} lulus, {len(GAGAL)} gagal")
    sys.exit(1 if GAGAL else 0)
