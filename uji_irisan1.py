"""Uji Irisan 1 — Lispy Calculator: tokenize/parse/atom,
environment standar, eval inti (variabel, angka, if, define,
panggil).

Jangkar utama dari artikel Norvig (lispy.html):
- contoh tokenize & pohon parse untuk program lingkaran,
- (begin (define r 10) (* pi (* r r))) -> 314.1592653589793,
- (if (> 10 20) (+ 1 1) (+ 3 3)) -> 6 dan (sqrt (* 2 8)) -> 4.0.
"""

import math
import sys

sys.path.insert(0, ".")
from lispy import atom, eval, parse, standard_env, tokenize

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


def ev(sumber, env):
    return eval(parse(sumber), env)


def uji_tokenize_artikel():
    got = tokenize("(begin (define r 10) (* pi (* r r)))")
    want = ["(", "begin", "(", "define", "r", "10", ")",
            "(", "*", "pi", "(", "*", "r", "r", ")", ")", ")"]
    assert got == want, got


def uji_parse_artikel():
    got = parse("(begin (define r 10) (* pi (* r r)))")
    want = ["begin", ["define", "r", 10], ["*", "pi", ["*", "r", "r"]]]
    assert got == want, got


def uji_atom():
    assert atom("10") == 10 and isinstance(atom("10"), int)
    assert atom("-3") == -3
    assert atom("3.14") == 3.14 and isinstance(atom("3.14"), float)
    assert atom("-3.14e159") == -3.14e159
    assert atom("pi") == "pi" and isinstance(atom("pi"), str)
    assert atom("+") == "+"


def uji_program_lingkaran():
    env = standard_env()
    got = ev("(begin (define r 10) (* pi (* r r)))", env)
    assert got == 314.1592653589793, got
    assert got == math.pi * 100


def uji_if_artikel():
    env = standard_env()
    assert ev("(if (> 10 20) (+ 1 1) (+ 3 3))", env) == 6
    assert ev("(if (< 10 20) (+ 1 1) (+ 3 3))", env) == 2
    # cabang yang tidak dipilih TIDAK dievaluasi (nama tak dikenal aman)
    assert ev("(if (> 11 10) 42 oops)", env) == 42


def uji_sqrt_artikel():
    env = standard_env()
    assert ev("(sqrt (* 2 8))", env) == 4.0


def uji_define_dan_variabel():
    env = standard_env()
    assert ev("(define x 3)", env) is None
    assert ev("x", env) == 3
    assert ev("(+ x x)", env) == 6
    assert ev("(begin (define x 1) (define x (+ x 1)) (+ x 1))", env) == 3


def uji_aritmetika_bersarang():
    env = standard_env()
    assert ev("(+ (* 2 100) (* 1 10))", env) == 210
    assert ev("(* (+ 1 2) (- 10 4))", env) == 18
    assert ev("(/ 4 2)", env) == 2.0  # truediv (modernisasi Py3)
    assert ev("(expt 2 10)", env) == 1024
    assert ev("(abs -7)", env) == 7
    assert ev("(max 1 5 3)", env) == 5
    assert ev("(min 1 5 3)", env) == 1
    assert ev("(round 3.6)", env) == 4


def uji_begin_sebagai_prosedur():
    env = standard_env()
    assert ev("(begin 1 2 3)", env) == 3
    assert ev("(begin 42)", env) == 42


def uji_list_primitif():
    env = standard_env()
    assert ev("(car (list 1 2 3))", env) == 1
    assert ev("(cdr (list 1 2 3))", env) == [2, 3]
    assert ev("(cons 0 (list 1 2))", env) == [0, 1, 2]
    assert ev("(length (list 1 2 3))", env) == 3
    assert ev("(append (list 1 2) (list 3))", env) == [1, 2, 3]
    assert ev("(list? (list 1))", env) is True
    assert ev("(null? (list))", env) is True
    assert ev("(null? (list 1))", env) is False


def uji_predikat_dan_apply_map():
    env = standard_env()
    assert ev("(number? 5)", env) is True
    assert ev("(number? (list 1))", env) is False
    assert ev("(procedure? car)", env) is True
    assert ev("(apply + (list 3 4))", env) == 7
    assert ev("(map abs (list -1 2 -3))", env) == [1, 2, 3]
    assert ev("(equal? (list 1 2) (list 1 2))", env) is True


def uji_error_parse():
    # ')' nyasar dan program kosong: SyntaxError dari parser.
    for sumber in (")", ""):
        try:
            parse(sumber)
        except SyntaxError:
            pass
        else:
            raise AssertionError(f"{sumber!r} harus SyntaxError")
    # Kurung tak tertutup: panduan asli membiarkan IndexError
    # (tokens[0] pada daftar kosong) — v1 memang tanpa pemulihan
    # error; lispy2 yang memperbaikinya. Dicatat, bukan ditambal.
    try:
        parse("(define r 10")
    except IndexError:
        pass
    else:
        raise AssertionError("kurung tak tertutup harus IndexError (kuirk panduan)")


def uji_variabel_tak_dikenal():
    env = standard_env()
    try:
        ev("tidak-ada", env)
    except LookupError:
        # v1 Calculator (dict polos) melempar KeyError — subkelas
        # LookupError; Full Lispy melempar LookupError dari Env.find.
        pass
    else:
        raise AssertionError("variabel tak dikenal harus LookupError")


if __name__ == "__main__":
    for nama, fn in sorted(dict(globals()).items()):
        if nama.startswith("uji_"):
            cek(nama, fn)
    print(f"\n{LULUS} lulus, {len(GAGAL)} gagal")
    sys.exit(1 if GAGAL else 0)
