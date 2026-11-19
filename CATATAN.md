# Catatan — Interpreter Lisp (Lispy Norvig)

Satu halaman per irisan: konsep inti dan temuan selama membangun.
Panduan: Peter Norvig, "How to Write a (Lisp) Interpreter (in
Python)" dan "(An ((Even Better) Lisp) Interpreter (in Python))".

## Irisan 1 — Lispy Calculator (selesai 19 Nov 2026)

Konsep inti: interpreter = dua separuh yang terpisah bersih.
Parser (tokenize → read_from_tokens → atom) mengubah teks
menjadi pohon list bersarang; eval berjalan di atas pohon itu
dengan sebuah dict environment. Sintaks tidak tahu makna,
makna tidak tahu sintaks. Lima kasus eval saja — variabel,
literal, if, define, panggil — sudah menjalankan program
sungguhan karena sisanya hidup di environment: bahkan `begin`
bukan bentuk khusus, melainkan prosedur biasa
(lambda *x: x[-1]) yang kebetulan mengembalikan argumen
terakhirnya; trik itu yang membuat program contoh artikel
(define di dalam begin) bekerja.

Bukti: 13/13 uji — contoh tokenize & pohon parse artikel persis,
program lingkaran → 314.1592653589793 (bit-exact vs math.pi*100),
tabel artikel (if → 6, sqrt → 4.0), cabang if yang kalah tidak
dievaluasi.

Temuan:
- Kurung tak tertutup pada panduan asli menghasilkan
  IndexError, bukan SyntaxError — tokens[0] pada daftar kosong.
  Dibiarkan setia pada panduan dan dilabeli; artikelnya sendiri
  mengakui v1 "mengharapkan programmer yang sempurna", dan
  lispy2-lah yang memperbaiki penanganan error.
- Dua modernisasi Python 3 tercatat: `/` memakai truediv
  (artikel era Python 2 memakai op.div) dan `map` dibungkus
  list() karena map Python 3 mengembalikan iterator.
- `+` di env standar adalah op.add biner — (+ 1 2 3) memang
  belum bisa di v1; setia pada panduan, bukan bug kami.

## Irisan 2 — Full Lispy v1 (selesai 19 Nov 2026)

Konsep inti: dua tambahan kecil mengubah kalkulator menjadi
bahasa sungguhan. Env menjadi rantai dict (find menelusuri ke
luar), dan lambda mengembalikan Procedure yang MENGINGAT env
tempat ia dibuat — closure. Dari situ rekursi, prosedur tingkat
tinggi, dan state yang terbungkus (make-account) semuanya
jatuh gratis. set! menulis di env tempat variabel ditemukan,
bukan env lokal — itulah yang membuat saldo account1 berubah
tapi account2 tidak.

Bukti: 11/11 kelompok uji — termasuk BATERAI RESMI 29 uji yang
diterbitkan Norvig (lispytest) lulus 29/29 berurutan dalam satu
env: quote, compose/repeat tingkat tinggi, zip, dan
riff-shuffle tiga kali yang mengembalikan dek ke urutan asal.
Jangkar artikel pertama: fact 100 utuh 158 digit (sama dengan
math.factorial), fib 0..19 lewat map+range, make-account
100 → 80 dengan closure kedua yang merdeka penuh.

Temuan:
- riff-shuffle bekerja di v1 karena begin adalah prosedur
  biasa: define-define internalnya dievaluasi di env pemanggil,
  jadi mereka mendarat di env lokal pemanggilan — perilaku yang
  benar secara kebetulan yang elegan.
- Error variabel tak dikenal berubah kelas: dict polos
  melempar KeyError, Env.find melempar LookupError (induknya) —
  uji irisan 1 dilonggarkan ke LookupError dan dicatat.

## Irisan 3 — Tipe & sintaks Lispy 2 (selesai 19 Nov 2026)

Konsep inti: generasi kedua mulai dari READER, bukan eval.
Karena string bisa memuat spasi dan komentar membuang teks,
tokenisasi potong-string v1 runtuh — diganti InPort yang
menarik token satu-satu dari aliran (regex Norvig) sehingga
ekspresi bisa membentang banyak baris dan dibaca dari berkas.
Symbol menjadi kelas tersendiri yang ter-intern: simbol yang
sama selalu objek yang sama, sehingga eval membandingkan
bentuk khusus dengan `is` dan string biasa tidak pernah
tertukar dengan simbol.

Bukti: 13/13 uji — interning (parse("foo") is Sym("foo")),
string satu token walau ber-spasi, contoh komentar artikel di
tengah daftar → (1 2 3), notasi ' ` , ,@ terurai ke bentuk
panjangnya, (sqrt -1) → 1i dan (* 1i 1i) → (-1+0i) persis
artikel, dua ekspresi dari satu port + eof_object.

Temuan:
- to_string untuk kompleks campuran (3+4j) menghasilkan
  "(3+4i)" — bentuk TAMPIL saja, tidak bisa dibaca balik
  sebagai atom (kurungnya terbaca sebagai daftar). Persis
  perilaku aslinya; baterai artikel memang hanya memakai
  bentuk murni 1i dan (-1+0i) sebagai tampilan.
- Gula (define (f x) ...) sudah TERBACA sebagai pohon, tapi
  belum bisa dievaluasi — memang begitu urutan artikelnya:
  sintaks dulu, expand() belakangan (irisan 4).

## Irisan 4 — Semantik Lispy 2 & baterai akhir (selesai 19 Nov 2026)

Konsep inti: tiga gagasan menutup seri ini. (1) expand()
memisahkan waktu-periksa dari waktu-jalan: sintaks rusak
ditolak sebelum dieksekusi, gula sintaks dan makro
dikembangkan menjadi bentuk inti — eval tidak berubah sama
sekali untuk memperoleh let, and, unless, dan define (f x).
(2) eval berekor: mengganti x/env lalu berputar, bukan
memanggil diri — rekursi ekor menjadi iterasi, sejuta langkah
tanpa tumpukan; versi non-ekor artikel terbukti menyerah
dengan RecursionError seperti yang artikel ramalkan. (3)
call/cc versi escape hanyalah pengecualian Python yang
membawa nilai pulang — jujur diakui bukan kontinuasi penuh.

Bukti: BATERAI RESMI 81 uji artikel lulus 81/81 dalam satu env
global berurutan — termasuk 8 kasus error yang dibandingkan
PESANNYA persis, newton yang membuktikan (= (square-root 200.)
(sqrt 200.)) = #t (Newton mendarat di double yang sama persis),
akun curry (define ((account bal) amt) ...), makro unless
dengan display yang tertangkap, quasiquote bersarang, dan
komentar artikel. Ditambah: sum2 1.000.000 → 500000500000,
port tulis/baca pulang-pergi, load berkas, REPL yang pulih
dari ZeroDivisionError, dan regresi irisan 1–3 hijau.
Total seluruh seri: 13 + 11 + 13 + 6 kelompok uji.

Temuan:
- Menangkap keluaran display di uji tidak bisa memakai
  redirect_stdout: port default primitif terikat pada objek
  sys.stdout saat definisi. Semantiknya yang diuji dengan
  menukar primitifnya sementara — pipanya bukan urusan bahasa.
- Nilai harap baterai harus membedakan str dan Symbol:
  di lispy2 keduanya tipe berbeda, dan to_string menelanjangi
  kekeliruan itu seketika ("testing" vs testing).
