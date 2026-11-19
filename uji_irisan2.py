"""Uji Irisan 2 — Full Lispy v1: Env.find, Procedure closure,
quote/set!/lambda, REPL.

Bukti utama: baterai 29 uji yang diterbitkan Norvig sendiri
(lispytest.py, dikutip di artikel lispy2) dijalankan berurutan
dalam satu environment — plus jangkar transkrip artikel pertama:
circle-area, fact 100 utuh, count, fib/range/map, make-account.
"""

import math
import subprocess
import sys

sys.path.insert(0, ".")
from lispy import Env, Procedure, eval, parse, schemestr, standard_env

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


# ------------------------------------------------------------------
# Baterai resmi 29 uji (lispytest untuk lis.py) — berurutan,
# satu environment bersama, persis seperti aslinya.
# ------------------------------------------------------------------

BATERAI_29 = [
    ("(quote (testing 1 (2.0) -3.14e159))", ["testing", 1, [2.0], -3.14e159]),
    ("(+ 2 2)", 4),
    ("(+ (* 2 100) (* 1 10))", 210),
    ("(if (> 6 5) (+ 1 1) (+ 2 2))", 2),
    ("(if (< 6 5) (+ 1 1) (+ 2 2))", 4),
    ("(define x 3)", None),
    ("x", 3),
    ("(+ x x)", 6),
    ("(begin (define x 1) (set! x (+ x 1)) (+ x 1))", 3),
    ("((lambda (x) (+ x x)) 5)", 10),
    ("(define twice (lambda (x) (* 2 x)))", None),
    ("(twice 5)", 10),
    ("(define compose (lambda (f g) (lambda (x) (f (g x)))))", None),
    ("((compose list twice) 5)", [10]),
    ("(define repeat (lambda (f) (compose f f)))", None),
    ("((repeat twice) 5)", 20),
    ("((repeat (repeat twice)) 5)", 80),
    ("(define fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))", None),
    ("(fact 3)", 6),
    ("(fact 50)", 30414093201713378043612608166064768844377641568960512000000000000),
    ("(define abs (lambda (n) ((if (> n 0) + -) 0 n)))", None),
    ("(list (abs -3) (abs 0) (abs 3))", [3, 0, 3]),
    ("(define combine (lambda (f) (lambda (x y) (if (null? x) (quote ()) "
     "(f (list (car x) (car y)) ((combine f) (cdr x) (cdr y)))))))", None),
    ("(define zip (combine cons))", None),
    ("(zip (list 1 2 3 4) (list 5 6 7 8))", [[1, 5], [2, 6], [3, 7], [4, 8]]),
    ("(define riff-shuffle (lambda (deck) (begin "
     "(define take (lambda (n seq) (if (<= n 0) (quote ()) (cons (car seq) (take (- n 1) (cdr seq)))))) "
     "(define drop (lambda (n seq) (if (<= n 0) seq (drop (- n 1) (cdr seq))))) "
     "(define mid (lambda (seq) (/ (length seq) 2))) "
     "((combine append) (take (mid deck) deck) (drop (mid deck) deck)))))", None),
    ("(riff-shuffle (list 1 2 3 4 5 6 7 8))", [1, 5, 2, 6, 3, 7, 4, 8]),
    ("((repeat riff-shuffle) (list 1 2 3 4 5 6 7 8))", [1, 3, 5, 7, 2, 4, 6, 8]),
    ("(riff-shuffle (riff-shuffle (riff-shuffle (list 1 2 3 4 5 6 7 8))))",
     [1, 2, 3, 4, 5, 6, 7, 8]),
]


def uji_baterai_29():
    assert len(BATERAI_29) == 29
    env = standard_env()
    for sumber, harap in BATERAI_29:
        got = ev(sumber, env)
        assert schemestr(got) == schemestr(harap), (sumber, got, harap)


# ------------------------------------------------------------------
# Jangkar transkrip artikel pertama
# ------------------------------------------------------------------

def uji_circle_area():
    env = standard_env()
    ev("(define circle-area (lambda (r) (* pi (* r r))))", env)
    got = ev("(circle-area 3)", env)
    assert got == math.pi * 9, got  # artikel mencetak 28.274333877 (repr Py2)


def uji_fact_100_utuh():
    env = standard_env()
    ev("(define fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))", env)
    assert ev("(fact 10)", env) == 3628800
    got = ev("(fact 100)", env)
    assert got == math.factorial(100)
    assert len(str(got)) == 158
    assert str(got).startswith("93326215443944152681")
    ev("(define circle-area (lambda (r) (* pi (* r r))))", env)
    luas = ev("(circle-area (fact 10))", env)
    assert math.isclose(luas, math.pi * 3628800 ** 2, rel_tol=1e-12), luas


def uji_count():
    env = standard_env()
    ev("(define count (lambda (item L) (if L (+ (equal? item (car L)) "
       "(count item (cdr L))) 0)))", env)
    assert ev("(count 0 (list 0 1 2 3 0 0))", env) == 3
    assert ev("(count (quote the) (quote (the more the merrier the bigger the better)))",
              env) == 4


def uji_fib_range_map():
    env = standard_env()
    ev("(define fib (lambda (n) (if (< n 2) 1 (+ (fib (- n 1)) (fib (- n 2))))))", env)
    ev("(define range (lambda (a b) (if (= a b) (quote ()) (cons a (range (+ a 1) b)))))",
       env)
    assert ev("(range 0 10)", env) == list(range(10))
    assert ev("(map fib (range 0 10))", env) == [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    assert ev("(map fib (range 0 20))", env) == [
        1, 1, 2, 3, 5, 8, 13, 21, 34, 55,
        89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765]
    assert ev("(pow 2 16)", env) == 65536.0  # pow dari vars(math)


def uji_make_account_closure():
    env = standard_env()
    ev("(define make-account (lambda (balance) (lambda (amt) "
       "(begin (set! balance (+ balance amt)) balance))))", env)
    ev("(define account1 (make-account 100.00))", env)
    ev("(define account2 (make-account 1000.00))", env)
    assert ev("(account1 -20.00)", env) == 80.0
    # closure kedua merdeka: tidak menyentuh saldo pertama
    assert ev("(account2 -20.00)", env) == 980.0
    assert ev("(account1 0)", env) == 80.0
    assert ev("(account1 20.00)", env) == 100.0


def uji_env_find_dan_scope():
    luar = Env()
    luar["x"] = 1
    dalam = Env(("y",), (2,), luar)
    assert dalam.find("x") is luar
    assert dalam.find("y") is dalam
    # set! menulis di env tempat variabel DITEMUKAN, bukan env lokal
    env = standard_env()
    ev("(define x 10)", env)
    ev("(define ubah (lambda (v) (set! x v)))", env)
    ev("(ubah 99)", env)
    assert ev("x", env) == 99
    # parameter menaungi (shadow) variabel global
    ev("(define bayangan (lambda (x) (+ x 1)))", env)
    assert ev("(bayangan 5)", env) == 6
    assert ev("x", env) == 99


def uji_procedure_adalah_nilai():
    env = standard_env()
    p = ev("(lambda (x) (* x x))", env)
    assert isinstance(p, Procedure)
    assert ev("(procedure? (lambda (x) x))", env) is True
    assert p(7) == 49  # bisa dipanggil langsung dari Python


def uji_schemestr():
    assert schemestr(["+", 1, 2]) == "(+ 1 2)"
    assert schemestr([]) == "()"
    assert schemestr([["a", 1], 2.5]) == "((a 1) 2.5)"


def uji_repl_subprocess():
    hasil = subprocess.run(
        [sys.executable, "-c", "from lispy import repl; repl()"],
        input="(+ 2 2)\n(define x 5)\n(* x x)\n",
        capture_output=True, text=True, timeout=30)
    assert hasil.returncode == 0, hasil.stderr
    assert "4" in hasil.stdout and "25" in hasil.stdout, hasil.stdout


def uji_regresi_irisan1():
    hasil = subprocess.run([sys.executable, "uji_irisan1.py"],
                           capture_output=True, text=True, timeout=60)
    assert hasil.returncode == 0, hasil.stdout + hasil.stderr
    assert "0 gagal" in hasil.stdout


if __name__ == "__main__":
    for nama, fn in sorted(dict(globals()).items()):
        if nama.startswith("uji_"):
            cek(nama, fn)
    print(f"\n{LULUS} lulus, {len(GAGAL)} gagal")
    sys.exit(1 if GAGAL else 0)
