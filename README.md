# Build Your Own Lisp Interpreter (Python)

Dua interpreter Lisp/Scheme yang dibangun lapis demi lapis
mengikuti esai **Peter Norvig**:

1. [*(How to Write a (Lisp) Interpreter (in Python))*](http://norvig.com/lispy.html)
2. [*(An ((Even Better) Lisp) Interpreter (in Python))*](http://norvig.com/lispy2.html)

Bagian dari seri belajar [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x)
(kategori Programming Language). Ditulis ulang dari nol sebagai
latihan dengan atribusi; bukan salinan berkas asli Norvig.

## Dua generasi, dua berkas

| Berkas | Isi |
|---|---|
| `lispy.py` | **Lispy v1** — parser 3 fungsi, `eval` 8 kasus, `Env` bersarang dengan `find`, `Procedure` sebagai closure: `quote`, `set!`, `lambda`, rekursi, prosedur tingkat tinggi. ±117 baris inti. |
| `lispy2.py` | **Lispy 2** — `Symbol` ter-intern, `InPort` dengan tokenizer regex (string, komentar, `#t/#f`, kompleks, notasi `' ` , ,@`), `expand()` dengan cek sintaks dini + makro (`let`, `define-macro`, `and` ditulis di Scheme sendiri), `eval` berekor-rekursif, lambda variadik, `call/cc` versi escape, port I/O, REPL dengan pemulihan error. |

## Menjalankan

```bash
python3 lispy.py            # REPL v1 (Ctrl-D keluar)
python3 lispy2.py           # REPL v2
python3 lispy2.py prog.scm  # jalankan berkas Scheme
```

```scheme
lispy> (define (sum2 n acc) (if (= n 0) acc (sum2 (- n 1) (+ n acc))))
lispy> (sum2 1000000 0)
500000500000
lispy> (call/cc (lambda (throw) (+ 5 (* 10 (call/cc (lambda (escape) (* 100 (escape 3))))))))
35
```

## Uji

Setiap irisan punya berkas ujinya; finale menjalankan semuanya
termasuk **dua baterai resmi yang diterbitkan Norvig sendiri**
(`lispytest.py`): 29 uji untuk v1 dan 81 uji untuk v2, lengkap
dengan kasus error yang dibandingkan *pesannya persis*.

```bash
python3 uji_irisan1.py   # 13 uji — parser & eval inti
python3 uji_irisan2.py   # 11 kelompok — baterai 29/29 + transkrip artikel
python3 uji_irisan3.py   # 13 uji — tipe & sintaks v2
python3 uji_irisan4.py   # 6 kelompok — baterai 81/81, ekor sejuta, REPL, port
```

Sorotan bukti: `(fact 100)` utuh 158 digit, riff-shuffle tiga
kali mengembalikan dek ke urutan asal, rekursi ekor sejuta
langkah tanpa tumpukan, `((account bal) amt)` currying lewat
pengembangan `define`, dan makro `unless` yang ditulis pemakai
dengan quasiquote.

## Adaptasi yang dicatat terbuka

- **Modernisasi Python 3** — artikel kedua masih Python 2:
  `io.StringIO`, unescape manual, `op.truediv`, `list(map(...))`.
- `Env.find` melempar `LookupError` untuk variabel tak dikenal
  (aslinya tersandung `AttributeError` dari `None.find`).
- `to_string` untuk kompleks campuran (`(3+4i)`) adalah bentuk
  tampil saja — persis perilaku aslinya.
- `call/cc` hanya escape (pengecualian Python), bukan kontinuasi
  penuh yang bisa disimpan & dipanggil ulang — batas yang
  diakui artikelnya.

Perjalanan irisan demi irisan, konsep inti, dan semua temuan
ada di `CATATAN.md`; peta & pagar selesai di `RENCANA.md`.
