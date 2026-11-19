"""Lispy — interpreter Lisp/Scheme mungil dalam Python.

Mengikuti esai Peter Norvig "How to Write a (Lisp) Interpreter
(in Python)" (norvig.com/lispy.html), ditulis ulang sebagai
latihan dengan atribusi. Dua tahap dalam satu berkas:

- Irisan 1: Lispy Calculator — parse + eval inti.
- Irisan 2: Full Lispy — Env bersarang, closure, quote/set!/lambda.

Lispy 2 (esai kedua) tinggal di lispy2.py, mandiri.
"""

import math
import operator as op

# ------------------------------------------------------------------
# Tipe-tipe Lispy (v1): Symbol adalah str, Number int/float,
# List adalah list Python.
# ------------------------------------------------------------------

Symbol = str
Number = (int, float)
List = list


# ------------------------------------------------------------------
# Parser: program (str) -> pohon ekspresi (list bersarang / atom)
# ------------------------------------------------------------------

def tokenize(chars: str) -> list:
    "Ubah string program menjadi daftar token."
    return chars.replace("(", " ( ").replace(")", " ) ").split()


def parse(program: str):
    "Baca satu ekspresi Scheme dari string program."
    return read_from_tokens(tokenize(program))


def read_from_tokens(tokens: list):
    "Bangun pohon ekspresi dari daftar token (dikonsumsi)."
    if len(tokens) == 0:
        raise SyntaxError("unexpected EOF")
    token = tokens.pop(0)
    if token == "(":
        L = []
        while tokens[0] != ")":
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # buang ')'
        return L
    elif token == ")":
        raise SyntaxError("unexpected )")
    else:
        return atom(token)


def atom(token: str):
    "Angka menjadi int/float; selain itu Symbol."
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


# ------------------------------------------------------------------
# Environment bersarang & prosedur buatan pengguna (Irisan 2)
# ------------------------------------------------------------------

class Env(dict):
    """Environment: dict {var: val} dengan rantai `outer`.

    find() menelusuri rantai ke luar sampai variabel ditemukan —
    inilah yang membuat cakupan leksikal (lexical scope) bekerja.
    """

    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def find(self, var):
        "Kembalikan Env terdalam yang memuat var."
        if var in self:
            return self
        elif self.outer is None:
            raise LookupError(var)
        else:
            return self.outer.find(var)


class Procedure(object):
    """Prosedur buatan pengguna: parameter + badan + env penutup.

    Menyimpan env tempat lambda DIBUAT (bukan dipanggil) = closure.
    """

    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

    def __call__(self, *args):
        return eval(self.body, Env(self.parms, args, self.env))


# ------------------------------------------------------------------
# Environment standar: seluruh fungsi math + primitif pilihan
# ------------------------------------------------------------------

def standard_env() -> Env:
    "Environment global Lispy: Env berisi math + primitif."
    env = Env()
    env.update(vars(math))  # sin, cos, sqrt, pi, ...
    env.update({
        "+": op.add, "-": op.sub, "*": op.mul, "/": op.truediv,
        ">": op.gt, "<": op.lt, ">=": op.ge, "<=": op.le, "=": op.eq,
        "abs": abs,
        "append": op.add,
        "apply": lambda proc, args: proc(*args),
        "begin": lambda *x: x[-1],
        "car": lambda x: x[0],
        "cdr": lambda x: x[1:],
        "cons": lambda x, y: [x] + y,
        "eq?": op.is_,
        "expt": pow,
        "equal?": op.eq,
        "length": len,
        "list": lambda *x: list(x),
        "list?": lambda x: isinstance(x, List),
        # Adaptasi Python 3: map() bawaan mengembalikan iterator;
        # Scheme mengharapkan list, jadi dibungkus list().
        "map": lambda *args: list(map(*args)),
        "max": max,
        "min": min,
        "not": op.not_,
        "null?": lambda x: x == [],
        "number?": lambda x: isinstance(x, Number),
        "print": print,
        "procedure?": callable,
        "round": round,
        "symbol?": lambda x: isinstance(x, Symbol),
    })
    return env


global_env = standard_env()


# ------------------------------------------------------------------
# Eval — Full Lispy (Irisan 2)
# Delapan kasus: variabel, literal, quote, if, set!, define,
# lambda, pemanggilan prosedur.
# ------------------------------------------------------------------

def eval(x, env=global_env):
    "Evaluasi ekspresi x di dalam environment env."
    if isinstance(x, Symbol):            # referensi variabel
        return env.find(x)[x]
    elif not isinstance(x, List):        # literal konstan
        return x
    elif x[0] == "quote":                # (quote exp)
        (_, exp) = x
        return exp
    elif x[0] == "if":                   # (if test conseq alt)
        (_, test, conseq, alt) = x
        exp = (conseq if eval(test, env) else alt)
        return eval(exp, env)
    elif x[0] == "set!":                 # (set! var exp)
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
    elif x[0] == "define":               # (define var exp)
        (_, var, exp) = x
        env[var] = eval(exp, env)
    elif x[0] == "lambda":               # (lambda (var...) body)
        (_, parms, body) = x
        return Procedure(parms, body, env)
    else:                                # (proc arg...)
        proc = eval(x[0], env)
        args = [eval(arg, env) for arg in x[1:]]
        return proc(*args)


# ------------------------------------------------------------------
# REPL & pencetakan
# ------------------------------------------------------------------

def schemestr(exp) -> str:
    "Ubah objek Python kembali menjadi string yang bisa dibaca Lisp."
    if isinstance(exp, List):
        return "(" + " ".join(map(schemestr, exp)) + ")"
    else:
        return str(exp)


def repl(prompt="lis.py> "):
    "Lingkaran baca-eval-cetak sederhana (Ctrl-D untuk keluar)."
    while True:
        try:
            val = eval(parse(input(prompt)))
        except EOFError:
            print()
            break
        if val is not None:
            print(schemestr(val))


if __name__ == "__main__":
    repl()
