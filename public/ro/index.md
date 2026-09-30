---
title: "Runtime lines: cum rulează de fapt Node.js și Python codul tău"
description: "Un material de referință interactiv și vizual pentru ingineri full-stack care se pregătesc de interviuri: event loop-ul Node.js, memoria Python și GIL-ul, sistemele de tipuri din JavaScript și Python, pas cu pas, cu întrebări de interviu pentru fiecare."
url: https://superintelligence.ro/ro
alternate_en: https://superintelligence.ro/index.md
alternate_ro: https://superintelligence.ro/ro/index.md
---

Un material de referință interactiv pentru interviurile full-stack

# Cum rulează de fapt Node.js și Python codul tău

Cinci explicații interactive, desenate ca linii pe o hartă de metrou. Parcurge programe reale linie cu linie și urmărește cum se mișcă stiva de apeluri (call stack), heap-ul, GIL-ul și sistemul de tipuri. Fiecare output a fost verificat pe Node.js și CPython reale, iar fiecare linie se încheie cu întrebările de interviu pentru care te pregătește.
[Începe cu event loop-ul](https://superintelligence.ro/ro/node)

## NEvent loop-ul Node

Cum jonglează un singur thread cu mii de sarcini: stiva de apeluri (call stack), cozile nextTick și de promise-uri, timerele, fazele libuv și thread pool-ul.
Vei ști să răspunzi la
- Rulează callback-ul unui promise înainte de `setTimeout(fn, 0)`?
- `setImmediate` sau `setTimeout`: care se declanșează primul?
- Ce blochează event loop-ul și cum repari asta?
[Deschide linia](https://superintelligence.ro/ro/node) [Întrebări de interviu](https://superintelligence.ro/ro/node#n-ref)

## MMemoria Python

Nume, obiecte și numărul de referințe, cum eliberează colectorul de cicluri ce nu poate elibera numărarea referințelor și de ce pymalloc păstrează memoria după ce ștergi lucruri.
Vei ști să răspunzi la
- Python transmite argumentele prin valoare sau prin referință?
- Care e diferența dintre `is` și `==`?
- De ce nu scade memoria după `del`?
[Deschide linia](https://superintelligence.ro/ro/memory) [Întrebări de interviu](https://superintelligence.ro/ro/memory#m-ref)

## GGIL-ul

Patru thread-uri și un singur lock pe o cronologie live: muncă limitată de CPU versus muncă limitată de I/O, Python free-threaded, procese și un race condition (condiție de cursă) pe care îl poți parcurge pas cu pas.
Vei ști să răspunzi la
- Fac thread-urile codul Python mai rapid?
- Face GIL-ul codul meu thread-safe?
- Thread-uri, procese sau asyncio: cum alegi?
[Deschide linia](https://superintelligence.ro/ro/gil) [Întrebări de interviu](https://superintelligence.ro/ro/gil#g-ref)

## JTipuri JavaScript

Macazul `typeof`, cum stochează V8 fiecare tip, copii versus referințe, algoritmul exact al lui `==`, valorile truthy și falsy și cei 64 de biți dintr-un număr.
Vei ști să răspunzi la
- De ce `[] == false` dă true?
- Copie superficială sau copie profundă?
- De ce `0.1 + 0.2 !== 0.3` dă true?
[Deschide linia](https://superintelligence.ro/ro/js-types) [Întrebări de interviu](https://superintelligence.ro/ro/js-types#j-ref)

## PTipuri Python

Tipurile built-in și unde să-l folosești pe fiecare, cum se face dispatch-ul pentru `a + b`, când `+=` modifică obiectul pe loc și cum se calculează hash-ul cheilor dintr-un dict.
Vei ști să răspunzi la
- Ce face ca un obiect să fie hashable?
- Ce se întâmplă când Python evaluează `a + b`?
- Ce problemă are `def f(items=[])`?
[Deschide linia](https://superintelligence.ro/ro/py-types) [Întrebări de interviu](https://superintelligence.ro/ro/py-types#p-ref)

### Parcurge pas cu pas

**Pornește**, **Înainte** și **Înapoi** te mută câte o linie de cod. Folosește ← și → ca să avansezi pas cu pas, Space ca să pornești redarea și alege viteza care ți se potrivește.

### Rezultate pe care te poți baza

Fiecare output afișat a fost verificat cu Node.js 22 și CPython 3.12. Codul JavaScript trece de ESLint, iar codul Python e formatat cu black.

### Gândit pentru recapitulare

Fiecare linie se încheie cu întrebări de interviu și răspunsuri scurte pe care le poți spune cu voce tare. Poți trimite un link direct către o linie cu `#node`, `#memory`, `#gil`, `#js-types` sau `#py-types`.
