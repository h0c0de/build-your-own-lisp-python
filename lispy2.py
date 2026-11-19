"""Lispy 2 — interpreter Lisp/Scheme yang lebih lengkap, dalam Python.

Mengikuti esai Peter Norvig "(An ((Even Better) Lisp) Interpreter
(in Python))" (norvig.com/lispy2.html), ditulis ulang sebagai
latihan dengan atribusi. Berkas mandiri (tidak mengimpor lispy.py).

- Irisan 3: tipe baru (Symbol ter-intern, string, boolean,
  kompleks), InPort + tokenizer regex, notasi ' ` , ,@, to_string.
- Irisan 4: expand() + makro, eval berekor-rekursif, lambda
  variadik, call/cc, REPL & pemuat berkas.

Modernisasi Python 3 (artikel masih Python 2): io.StringIO,
unescape manual (bukan decode('string_escape')), op.truediv.
"""

import cmath
import io
import math
import operator as op
import re
import sys

isa = isinstance


# ------------------------------------------------------------------
# Symbol: kelas tersendiri (turunan str) + tabel intern.
# Simbol yang sama selalu objek yang sama -> bisa dibandingkan
# dengan `is`, dan tidak tertukar dengan string biasa.
# ------------------------------------------------------------------

class Symbol(str):
    pass


def Sym(s, symbol_table={}):
    "Cari atau buat entri Symbol unik untuk string s."
    if s not in symbol_table:
        symbol_table[s] = Symbol(s)
    return symbol_table[s]


_quote, _if, _set, _define, _lambda, _begin, _definemacro = map(
    Sym, "quote if set! define lambda begin define-macro".split())
_quasiquote, _unquote, _unquotesplicing = map(
    Sym, "quasiquote unquote unquote-splicing".split())

eof_object = Symbol("#<eof-object>")  # catatan: tidak ter-intern


# ------------------------------------------------------------------
# InPort & reader: token diambil per kebutuhan dari aliran teks,
# jadi ekspresi boleh membentang banyak baris.
# ------------------------------------------------------------------

class InPort(object):
    "Port masukan: membuffer satu baris teks pada satu waktu."

    tokenizer = r'''\s*(,@|[('`,)]|"(?:[\\].|[^\\"])*"|;.*|[^\s('"`,;)]*)(.*)'''

    def __init__(self, file):
        self.file = file
        self.line = ""

    def next_token(self):
        "Token berikutnya; lewati komentar; eof_object di akhir."
        while True:
            if self.line == "":
                self.line = self.file.readline()
            if self.line == "":
                return eof_object
            token, self.line = re.match(InPort.tokenizer, self.line).groups()
            if token != "" and not token.startswith(";"):
                return token


quotes = {"'": _quote, "`": _quasiquote, ",": _unquote, ",@": _unquotesplicing}


def readchar(inport):
    "Baca satu karakter dari port masukan."
    if inport.line != "":
        ch, inport.line = inport.line[0], inport.line[1:]
        return ch
    else:
        return inport.file.read(1) or eof_object


def read(inport):
    "Baca satu ekspresi Scheme dari port."

    def read_ahead(token):
        if "(" == token:
            L = []
            while True:
                token = inport.next_token()
                if token == ")":
                    return L
                else:
                    L.append(read_ahead(token))
        elif ")" == token:
            raise SyntaxError("unexpected )")
        elif token in quotes:
            return [quotes[token], read(inport)]
        elif token is eof_object:
            raise SyntaxError("unexpected EOF in list")
        else:
            return atom(token)

    token1 = inport.next_token()
    return eof_object if token1 is eof_object else read_ahead(token1)


_UNESCAPE = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "0": "\0"}


def _unescape(s: str) -> str:
    "Padanan Python 3 untuk decode('string_escape') ala Python 2."
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append(_UNESCAPE.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _escape(s: str) -> str:
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r"))


def atom(token):
    "Angka -> angka; #t/#f -> boolean; \"...\" -> string; lain -> Symbol."
    if token == "#t":
        return True
    elif token == "#f":
        return False
    elif token[0] == '"':
        return _unescape(token[1:-1])
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            try:
                return complex(token.replace("i", "j", 1))
            except ValueError:
                return Sym(token)


def to_string(x) -> str:
    "Ubah objek Python kembali menjadi string yang bisa dibaca Lisp."
    if x is True:
        return "#t"
    elif x is False:
        return "#f"
    elif isa(x, Symbol):
        return x
    elif isa(x, str):
        return '"%s"' % _escape(x)
    elif isa(x, list):
        return "(" + " ".join(map(to_string, x)) + ")"
    elif isa(x, complex):
        return str(x).replace("j", "i")
    else:
        return str(x)


def parse(inport):
    "Parse program: baca, lalu expand (cek sintaks + makro)."
    if isa(inport, str):
        inport = InPort(io.StringIO(inport))
    return expand(read(inport), toplevel=True)


# ------------------------------------------------------------------
# expand(): pemeriksaan sintaks dini + pengembangan gula sintaks
# dan makro, sebelum eval melihat ekspresinya (Irisan 4).
# ------------------------------------------------------------------

def require(x, predicate, msg="wrong length"):
    "Lempar SyntaxError berpesan jelas bila predicate salah."
    if not predicate:
        raise SyntaxError(to_string(x) + ": " + msg)


def expand_quasiquote(x):
    "Kembangkan `x menjadi rangkaian cons/append atas (quote ...)."
    if not is_pair(x):
        return [_quote, x]
    require(x, x[0] is not _unquotesplicing, "can't splice here")
    if x[0] is _unquote:
        require(x, len(x) == 2)
        return x[1]
    elif is_pair(x[0]) and x[0][0] is _unquotesplicing:
        require(x[0], len(x[0]) == 2)
        return [_append, x[0][1], expand_quasiquote(x[1:])]
    else:
        return [_cons, expand_quasiquote(x[0]), expand_quasiquote(x[1:])]


def expand(x, toplevel=False):
    "Telusuri pohon x: perbaiki bentuk, kembangkan makro, tolak yang rusak."
    require(x, x != [])                    # () => Error
    if not isa(x, list):                   # konstanta => utuh
        return x
    elif x[0] is _quote:                   # (quote exp)
        require(x, len(x) == 2)
        return x
    elif x[0] is _if:                      # (if test conseq [alt])
        if len(x) == 3:
            x = x + [None]                 # => (if test conseq None)
        require(x, len(x) == 4)
        return [expand(e) for e in x]
    elif x[0] is _set:                     # (set! var exp)
        require(x, len(x) == 3)
        var = x[1]
        require(x, isa(var, Symbol), "can set! only a symbol")
        return [_set, var, expand(x[2])]
    elif x[0] is _define or x[0] is _definemacro:
        require(x, len(x) >= 3)
        _def, v, body = x[0], x[1], x[2:]
        if isa(v, list) and v:             # (define (f arg...) badan...)
            f, args = v[0], v[1:]          # => (define f (lambda (arg...) badan...))
            return expand([_def, f, [_lambda, args] + body], toplevel)
        else:
            require(x, len(x) == 3)
            require(x, isa(v, Symbol), "can define only a symbol")
            exp = expand(x[2])
            if _def is _definemacro:
                require(x, toplevel, "define-macro only allowed at top level")
                proc = eval(exp)
                require(x, callable(proc), "macro must be a procedure")
                macro_table[v] = proc      # daftarkan; bentuknya lenyap
                return None
            return [_define, v, exp]
    elif x[0] is _begin:                   # (begin exp...)
        if len(x) == 1:
            return None                    # (begin) => None
        else:
            return [expand(xi, toplevel) for xi in x]
    elif x[0] is _lambda:                  # (lambda (var...) e1 e2...)
        require(x, len(x) >= 3)
        vars, body = x[1], x[2:]
        require(x, (isa(vars, list) and all(isa(v, Symbol) for v in vars))
                or isa(vars, Symbol), "illegal lambda argument list")
        exp = body[0] if len(body) == 1 else [_begin] + body
        return [_lambda, vars, expand(exp)]
    elif x[0] is _quasiquote:              # `x => expand_quasiquote(x)
        require(x, len(x) == 2)
        return expand_quasiquote(x[1])
    elif isa(x[0], Symbol) and x[0] in macro_table:
        return expand(macro_table[x[0]](*x[1:]), toplevel)  # (makro arg...)
    else:                                  # (f arg...)
        return [expand(e) for e in x]


# ------------------------------------------------------------------
# Makro: `let` ditulis di Python; `and` ditulis di Scheme sendiri
# (lihat bootstrap di bawah) — keduanya lewat macro_table yang sama.
# ------------------------------------------------------------------

_append, _cons, _let = map(Sym, "append cons let".split())


def _let_macro(*args):
    args = list(args)
    x = [_let] + args
    require(x, len(args) > 1)
    bindings, body = args[0], args[1:]
    require(x, all(isa(b, list) and len(b) == 2 and isa(b[0], Symbol)
                   for b in bindings), "illegal binding list")
    vars, vals = zip(*bindings)
    return [[_lambda, list(vars)] + [expand(e) for e in body]] + \
           [expand(v) for v in vals]


macro_table = {_let: _let_macro}


# ------------------------------------------------------------------
# Environment & prosedur (pola yang sama seperti lispy.py)
# ------------------------------------------------------------------

class Env(dict):
    """Environment: dict {var: val} dengan rantai `outer`.

    Parameter boleh satu Symbol (lambda variadik): ia diikat ke
    daftar seluruh argumen. Jumlah argumen yang salah = TypeError
    sejak pemanggilan, bukan kegagalan misterius di tengah jalan.
    """

    def __init__(self, parms=(), args=(), outer=None):
        self.outer = outer
        args = list(args)
        if isa(parms, Symbol):
            self.update({parms: args})
        else:
            if len(args) != len(parms):
                raise TypeError("expected %s, given %s, "
                                % (to_string(parms), to_string(args)))
            self.update(zip(parms, args))

    def find(self, var):
        "Kembalikan Env terdalam yang memuat var."
        if var in self:
            return self
        elif self.outer is None:
            raise LookupError(var)
        else:
            return self.outer.find(var)


class Procedure(object):
    """Prosedur buatan pengguna: closure atas env pembuatnya."""

    def __init__(self, parms, exp, env):
        self.parms, self.exp, self.env = parms, exp, env

    def __call__(self, *args):
        return eval(self.exp, Env(self.parms, args, self.env))


def is_pair(x):
    return x != [] and isa(x, list)


def callcc(proc):
    """Panggil proc dengan kontinuasi semasa; hanya untuk escape.

    Kontinuasi diwujudkan sebagai pengecualian Python yang
    membawa nilai pulang. Ia tidak bisa disimpan lalu dipanggil
    ulang berkali-kali seperti call/cc Scheme sejati — batas
    yang diakui artikelnya sendiri.
    """
    ball = RuntimeWarning("Sorry, can't continue this continuation any longer.")

    def throw(retval):
        ball.retval = retval
        raise ball

    try:
        return proc(throw)
    except RuntimeWarning as w:
        if w is ball:
            return ball.retval
        else:
            raise w


def add_globals(env):
    "Isi env dengan primitif Scheme inti (diperluas di Irisan 4)."
    env.update(vars(math))
    env.update(vars(cmath))  # menimpa versi math: sqrt(-1) -> 1j
    env.update({
        "+": op.add, "-": op.sub, "*": op.mul, "/": op.truediv,
        ">": op.gt, "<": op.lt, ">=": op.ge, "<=": op.le, "=": op.eq,
        "not": op.not_,
        "equal?": op.eq, "eq?": op.is_,
        "length": len,
        "cons": lambda x, y: [x] + list(y),
        "car": lambda x: x[0], "cdr": lambda x: x[1:],
        "append": op.add,
        "list": lambda *x: list(x),
        "list?": lambda x: isa(x, list),
        "null?": lambda x: x == [],
        "symbol?": lambda x: isa(x, Symbol),
        "boolean?": lambda x: isa(x, bool),
        "pair?": is_pair,
        "number?": lambda x: isa(x, (int, float, complex)),
        "apply": lambda proc, l: proc(*l),
        "map": lambda *args: list(map(*args)),
        "max": max, "min": min, "abs": abs,
        "call/cc": callcc,
        "eval": lambda x: eval(expand(x)),
        "load": lambda fn: load(fn),
        "port?": lambda x: isa(x, (io.IOBase, InPort)),
        "open-input-file": lambda fn: InPort(open(fn)),
        "close-input-port": lambda p: p.file.close(),
        "open-output-file": lambda f: open(f, "w"),
        "close-output-port": lambda p: p.close(),
        "eof-object?": lambda x: x is eof_object,
        "read-char": readchar,
        "read": read,
        "write": lambda x, port=sys.stdout: port.write(to_string(x)),
        "display": lambda x, port=sys.stdout: port.write(
            x if isa(x, str) else to_string(x)),
    })
    return env


global_env = add_globals(Env())


# ------------------------------------------------------------------
# Eval — lingkaran berekor-rekursif (Irisan 4).
# Untuk if/begin/pemanggilan prosedur buatan, eval TIDAK memanggil
# dirinya: ia mengganti x (dan env) lalu berputar — tumpukan
# Python tidak tumbuh, jadi rekursi ekor sejuta langkah aman.
# ------------------------------------------------------------------

def eval(x, env=global_env):
    "Evaluasi ekspresi x di dalam environment env."
    while True:
        if isa(x, Symbol):               # referensi variabel
            return env.find(x)[x]
        elif not isa(x, list):           # literal konstan
            return x
        elif x[0] is _quote:             # (quote exp)
            (_, exp) = x
            return exp
        elif x[0] is _if:                # (if test conseq alt)
            (_, test, conseq, alt) = x
            x = (conseq if eval(test, env) else alt)
        elif x[0] is _set:               # (set! var exp)
            (_, var, exp) = x
            env.find(var)[var] = eval(exp, env)
            return None
        elif x[0] is _define:            # (define var exp)
            (_, var, exp) = x
            env[var] = eval(exp, env)
            return None
        elif x[0] is _lambda:            # (lambda (var...) body)
            (_, parms, exp) = x
            return Procedure(parms, exp, env)
        elif x[0] is _begin:             # (begin exp...)
            for exp in x[1:-1]:
                eval(exp, env)
            x = x[-1]
        else:                            # (proc arg...)
            exps = [eval(exp, env) for exp in x]
            proc = exps.pop(0)
            if isa(proc, Procedure):
                x = proc.exp
                env = Env(proc.parms, exps, proc.env)
            else:
                return proc(*exps)


# ------------------------------------------------------------------
# REPL & pemuat berkas
# ------------------------------------------------------------------

def load(filename):
    "Evaluasi setiap ekspresi dari berkas."
    repl(None, InPort(open(filename)), None)


def repl(prompt="lispy> ", inport=None, out=sys.stdout):
    "Lingkaran baca-eval-cetak dengan pemulihan error."
    if inport is None:
        inport = InPort(sys.stdin)
    sys.stderr.write("Lispy version 2.0\n")
    while True:
        try:
            if prompt:
                sys.stderr.write(prompt)
            x = parse(inport)
            if x is eof_object:
                return
            val = eval(x)
            if val is not None and out:
                print(to_string(val), file=out)
        except Exception as e:
            print("%s: %s" % (type(e).__name__, e))


# Bootstrap: makro `and` didefinisikan di dalam Scheme sendiri,
# memakai define-macro + quasiquote — bukti makro bekerja bahkan
# sebelum berkas ini selesai dimuat.
eval(parse("""(begin
(define-macro and (lambda args
   (if (null? args) #t
       (if (= (length args) 1) (car args)
           `(if ,(car args) (and ,@(cdr args)) #f)))))
)"""))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for nama_berkas in sys.argv[1:]:
            load(nama_berkas)
    else:
        repl()
