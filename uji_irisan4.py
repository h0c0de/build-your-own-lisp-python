"""Uji Irisan 4 — finale Lispy 2: expand, makro, ekor-rekursif,
call/cc, REPL, load — dibuktikan oleh BATERAI RESMI 81 uji yang
diterbitkan Norvig (lispytest untuk lispy.py), dijalankan
berurutan dalam environment global bersama, persis aslinya.
Kasus error membandingkan PESAN persisnya, bukan cuma kelasnya.
"""

import io
import os
import subprocess
import sys

sys.path.insert(0, ".")
import lispy2
from lispy2 import eval, parse, to_string

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


class Raises:
    "Penanda: ekspresi harus melempar exception ini dengan pesan ini."

    def __init__(self, tipe, pesan):
        self.tipe, self.pesan = tipe, pesan


BATERAI_81 = [
    ("(quote (testing 1 (2.0) -3.14e159))",
     [lispy2.Sym("testing"), 1, [2.0], -3.14e159]),
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
    ("()", Raises(SyntaxError, "(): wrong length")),
    ("(set! x)", Raises(SyntaxError, "(set! x): wrong length")),
    ("(define 3 4)", Raises(SyntaxError, "(define 3 4): can define only a symbol")),
    ("(quote 1 2)", Raises(SyntaxError, "(quote 1 2): wrong length")),
    ("(if 1 2 3 4)", Raises(SyntaxError, "(if 1 2 3 4): wrong length")),
    ("(lambda 3 3)", Raises(SyntaxError, "(lambda 3 3): illegal lambda argument list")),
    ("(lambda (x))", Raises(SyntaxError, "(lambda (x)): wrong length")),
    ("(if (= 1 2) (define-macro a 'a) (define-macro a 'b))",
     Raises(SyntaxError,
            "(define-macro a (quote a)): define-macro only allowed at top level")),
    ("(define (twice x) (* 2 x))", None),
    ("(twice 2)", 4),
    ("(twice 2 2)", Raises(TypeError, "expected (x), given (2 2), ")),
    ("(define lyst (lambda items items))", None),
    ("(lyst 1 2 3 (+ 2 2))", [1, 2, 3, 4]),
    ("(if 1 2)", 2),
    ("(if (= 3 4) 2)", None),
    ("(define ((account bal) amt) (set! bal (+ bal amt)) bal)", None),
    ("(define a1 (account 100))", None),
    ("(a1 0)", 100),
    ("(a1 10)", 110),
    ("(a1 10)", 120),
    ("(define (newton guess function derivative epsilon) "
     "(define guess2 (- guess (/ (function guess) (derivative guess)))) "
     "(if (< (abs (- guess guess2)) epsilon) guess2 "
     "(newton guess2 function derivative epsilon)))", None),
    ("(define (square-root a) "
     "(newton 1 (lambda (x) (- (* x x) a)) (lambda (x) (* 2 x)) 1e-8))", None),
    ("(> (square-root 200.) 14.14213)", True),
    ("(< (square-root 200.) 14.14215)", True),
    ("(= (square-root 200.) (sqrt 200.))", True),
    ("(define (sum-squares-range start end) "
     "(define (sumsq-acc start end acc) "
     "(if (> start end) acc (sumsq-acc (+ start 1) end (+ (* start start) acc)))) "
     "(sumsq-acc start end 0))", None),
    ("(sum-squares-range 1 3000)", 9004500500),
    ("(call/cc (lambda (throw) (+ 5 (* 10 (throw 1)))))", 1),
    ("(call/cc (lambda (throw) (+ 5 (* 10 1))))", 15),
    ("(call/cc (lambda (throw) (+ 5 (* 10 (call/cc (lambda (escape) "
     "(* 100 (escape 3))))))))", 35),
    ("(call/cc (lambda (throw) (+ 5 (* 10 (call/cc (lambda (escape) "
     "(* 100 (throw 3))))))))", 3),
    ("(call/cc (lambda (throw) (+ 5 (* 10 (call/cc (lambda (escape) "
     "(* 100 1)))))))", 1005),
    ("(* 1i 1i)", -1 + 0j),
    ("(sqrt -1)", 1j),
    ("(let ((a 1) (b 2)) (+ a b))", 3),
    ("(let ((a 1) (b 2 3)) (+ a b))",
     Raises(SyntaxError, "(let ((a 1) (b 2 3)) (+ a b)): illegal binding list")),
    ("(and 1 2 3)", 3),
    ("(and (> 2 1) 2 3)", 3),
    ("(and)", True),
    ("(and (> 2 1) (> 2 3))", False),
    ("(define-macro unless (lambda args `(if (not ,(car args)) "
     "(begin ,@(cdr args)))))", None),
    ("(unless (= 2 (+ 1 1)) (display 2) 3 4)", None),
    ("(unless (= 4 (+ 1 1)) (display 2) (display \"\\n\") 3 4)", 4),
    ("(quote x)", lispy2.Sym("x")),
    ("(quote (1 2 three))", [1, 2, lispy2.Sym("three")]),
    ("'x", lispy2.Sym("x")),
    ("'(one 2 3)", [lispy2.Sym("one"), 2, 3]),
    ("(define L (list 1 2 3))", None),
    ("`(testing ,@L testing)",
     [lispy2.Sym("testing"), 1, 2, 3, lispy2.Sym("testing")]),
    ("`(testing ,L testing)",
     [lispy2.Sym("testing"), [1, 2, 3], lispy2.Sym("testing")]),
    ("`,@L", Raises(SyntaxError, "(unquote-splicing L): can't splice here")),
    ("'(1 ;test comments '\n     ;skip this line\n"
     "     2 ; more ; comments ; ) )\n     3) ; final comment", [1, 2, 3]),
]

# keluaran stdout yang diharapkan untuk dua uji unless (display)
KELUARAN = {70: "", 71: "2\n"}


def uji_baterai_81():
    assert len(BATERAI_81) == 81, len(BATERAI_81)
    # display menulis ke port default yang terikat saat definisi,
    # jadi untuk dua uji unless primitifnya ditukar sementara
    # dengan versi penangkap — semantiknya yang diuji, bukan pipanya.
    display_asli = lispy2.global_env[lispy2.Sym("display")]
    for i, (sumber, harap) in enumerate(BATERAI_81):
        tangkap = io.StringIO()
        if i in KELUARAN:
            lispy2.global_env[lispy2.Sym("display")] = (
                lambda x, port=None: tangkap.write(
                    x if isinstance(x, str) else to_string(x)))
        try:
            got = ev(sumber)
        except Exception as e:  # noqa: BLE001
            assert isinstance(harap, Raises), (i, sumber, "tak terduga", repr(e))
            assert isinstance(e, harap.tipe), (i, sumber, repr(e))
            assert str(e) == harap.pesan, (i, sumber, str(e), harap.pesan)
        else:
            assert not isinstance(harap, Raises), (i, sumber, "harus error", got)
            assert to_string(got) == to_string(harap), (i, sumber, got, harap)
        finally:
            if i in KELUARAN:
                lispy2.global_env[lispy2.Sym("display")] = display_asli
        if i in KELUARAN:
            assert tangkap.getvalue() == KELUARAN[i], (i, tangkap.getvalue())


def uji_ekor_rekursif_sejuta():
    ev("(define (sum2 n acc) (if (= n 0) acc (sum2 (- n 1) (+ n acc))))")
    assert ev("(sum2 1000000 0)") == 500000500000
    # versi non-ekor artikel memang harus menyerah (RecursionError)
    ev("(define (sum-to n) (if (= n 0) 0 (+ n (sum-to (- n 1)))))")
    try:
        ev("(sum-to 1000)")
    except RecursionError:
        pass
    else:
        raise AssertionError("sum-to non-ekor harus RecursionError")


def uji_eval_dan_port():
    assert ev("(eval (quote (+ 1 2)))") == 3
    os.makedirs("aset", exist_ok=True)
    jalur = os.path.abspath("aset/uji-port.scm")
    ev('(define p (open-output-file "%s"))' % jalur.replace("\\", "/"))
    ev("(write (quote (1 2 tiga)) p)")
    ev("(close-output-port p)")
    ev('(define q (open-input-file "%s"))' % jalur.replace("\\", "/"))
    assert ev("(port? q)") is True
    assert to_string(ev("(read q)")) == "(1 2 tiga)"
    assert ev("(eof-object? (read q))") is True
    ev("(close-input-port q)")


def uji_load_berkas():
    os.makedirs("aset", exist_ok=True)
    jalur = os.path.abspath("aset/uji-load.scm")
    with open(jalur, "w") as f:
        f.write("(define (faktorial n) (if (<= n 1) 1 (* n (faktorial (- n 1)))))\n")
    lispy2.load(jalur)
    assert ev("(faktorial 5)") == 120


def uji_repl_subprocess():
    hasil = subprocess.run(
        [sys.executable, "-c", "from lispy2 import repl; repl()"],
        input="(define (cube x) (* x (* x x)))\n(cube 10)\n(/ 3 0)\n(cube 3)\n",
        capture_output=True, text=True, timeout=60)
    assert hasil.returncode == 0, hasil.stderr
    assert "Lispy version 2.0" in hasil.stderr
    assert "1000" in hasil.stdout, hasil.stdout
    assert "ZeroDivisionError" in hasil.stdout, hasil.stdout  # pulih dari error
    assert "27" in hasil.stdout, hasil.stdout


def uji_regresi():
    for berkas in ("uji_irisan1.py", "uji_irisan2.py", "uji_irisan3.py"):
        hasil = subprocess.run([sys.executable, berkas],
                               capture_output=True, text=True, timeout=300)
        assert hasil.returncode == 0, (berkas, hasil.stdout, hasil.stderr)


if __name__ == "__main__":
    for nama, fn in sorted(dict(globals()).items()):
        if nama.startswith("uji_"):
            cek(nama, fn)
    print(f"\n{LULUS} lulus, {len(GAGAL)} gagal")
    sys.exit(1 if GAGAL else 0)
