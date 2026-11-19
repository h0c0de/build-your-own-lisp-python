# Rencana — Build Kedua Belas: Interpreter Lisp (Lispy Norvig)

Mengikuti dua esai **Peter Norvig**: *"How to Write a (Lisp)
Interpreter (in Python)"* (Lispy, lis.py) dan *"(An ((Even
Better) Lisp) Interpreter (in Python))"* (Lispy 2, lispy.py) —
entri Python kategori Programming Language ("How to Write a
Lisp Interpreter in Python") di repo
codecrafters-io/build-your-own-x.

Panduan:
- http://norvig.com/lispy.html
- http://norvig.com/lispy2.html

## Isi panduan (terverifikasi 19 Nov 2026, keduanya dibaca utuh)

**Lispy v1** dua tahap: (a) *Lispy Calculator* — parse
(tokenize + read_from_tokens + atom), environment standar dari
modul math + operator, eval untuk referensi variabel, angka,
`if`, `define`, dan pemanggilan prosedur; (b) *Full Lispy* —
`Env` sebagai dict bersarang dengan `find`, `Procedure` sebagai
closure, tambah `quote`, `set!`, `lambda`. Artikelnya mencetak
transkrip REPL persis: luas lingkaran 314.1592653589793,
(fact 100) sebagai integer raksasa yang utuh, rantai
repeat/twice 40 → 160 → 2560 → 655360, (map fib (range 0 20)).

**Lispy 2** menambal kekurangan v1 yang diakui artikelnya
sendiri: tipe string/boolean (#t/#f)/bilangan kompleks/port;
kelas Symbol ter-intern; InPort dengan tokenizer regex (komentar
`;`, notasi ' ` , ,@); makro (let bawaan + define-macro, `and`
didefinisikan di dalam Scheme sendiri); eval berekor-rekursif
(sum2 sejuta langkah tanpa tumpukan); call/cc versi escape;
lambda variadik; expand() yang memeriksa sintaks lebih dini dan
mengembangkan gula sintaks (define (f x), badan lambda banyak
ekspresi, if tanpa alternatif); ±75 prosedur primitif. Artikel
kedua bahkan menerbitkan baterai ujinya sendiri: 29 uji untuk
v1 dan 81 uji untuk v2, lengkap dengan kasus error
`=raises=>`.

## Adaptasi yang dicatat terbuka

- **Dua modul seperti aslinya**: `lispy.py` (v1, irisan 1–2)
  dan `lispy2.py` (v2, irisan 3–4, mandiri) — regresi v1 tetap
  murni, dan perbedaan kedua generasi terlihat jelas.
- **Modernisasi Python 3**: kode lispy2 di artikel masih
  beraroma Python 2 (print>>, StringIO, decode string_escape,
  op.div). Kami memakai padanan Python 3 (io.StringIO,
  unescape manual, op.truediv) — dicatat, bukan disembunyikan.
- Tidak ada interpreter Scheme di VM ini (guile/racket tidak
  terpasang, terverifikasi 19 Nov 2026); wasitnya adalah
  transkrip tercetak kedua artikel + baterai uji 29/81 yang
  diterbitkan Norvig sendiri + nilai klasik yang diketahui
  pasti (faktorial, Fibonacci, riff-shuffle).
- Tampilan angka REPL artikel v1 memakai repr Python 2 yang
  terpotong (314.159265359); uji kami membandingkan nilai
  numeriknya, bukan string tampilannya.

## Irisan

- [x] Irisan 1 — Lispy Calculator: tokenize/parse/atom,
      environment standar, eval (variabel, angka, if, define,
      panggil). Bukti: contoh tokenize & pohon parse artikel
      persis; (begin (define r 10) (* pi (* r r))) →
      314.1592653589793; contoh tabel artikel ((if (> 10 20)
      (+ 1 1) (+ 3 3)) → 6; (sqrt (* 2 8)) → 4.0).
- [x] Irisan 2 — Full Lispy v1: Env.find, Procedure closure,
      quote/set!/lambda. Bukti: transkrip artikel — circle-area,
      fact 10 & fact 100 utuh, count 3 & 4, rantai repeat,
      (map fib (range 0 20)), make-account (closure + set!:
      100 → 80 → 100), dan baterai 29 uji v1 dari artikel kedua
      lulus semua.
- [x] Irisan 3 — Tipe & sintaks Lispy 2: Symbol ter-intern,
      InPort regex (string dengan escape, komentar, #t/#f,
      kompleks, notasi ' ` , ,@), to_string. Bukti: string &
      boolean & kompleks artikel ((* 1i 1i) → -1, (sqrt -1) →
      1i), komentar di tengah daftar → (1 2 3), round-trip
      to_string untuk semua tipe.
- [x] Irisan 4 — Semantik Lispy 2 + terbit: expand() (cek
      sintaks dini + gula sintaks), eval berekor (sum2
      1.000.000 → 500000500000), lambda variadik, makro
      (let, and, unless), call/cc escape (35 & 3 artikel),
      REPL + pemuat berkas. Bukti akhir: baterai 81 uji artikel
      lulus semua termasuk kasus =raises=>; regresi 1–3;
      terbit ke `build-your-own-lisp-python`.

## Pagar selesai

- [x] Kedua baterai uji yang diterbitkan panduan (29 + 81)
      lulus terhadap implementasi kami.
- [x] Closure, makro, dan rekursi ekor terbukti oleh program
      sungguhan, bukan potongan mainan.
- [x] `CATATAN.md` satu halaman per irisan: konsep inti + temuan.
- [x] Repo GitHub publik `build-your-own-lisp-python` terbit &
      terverifikasi.
