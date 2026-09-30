---
title: "Gestionarea memoriei în Python explicată: referințe, GC, pymalloc | Runtime lines"
description: "Nume, obiecte și numărul de referințe, cum eliberează colectorul de cicluri ce nu poate elibera numărarea referințelor și de ce pymalloc păstrează memoria după ce ștergi lucruri."
url: https://superintelligence.ro/ro/memory
alternate_en: https://superintelligence.ro/memory.md
alternate_ro: https://superintelligence.ro/ro/memory.md
---

# Memoria în Python, desenată ca o hartă

În stânga sunt numele, în dreapta obiectele din heap, iar fiecare săgeată este o referință. Parcurge pas cu pas patru programe scurte ca să vezi când sunt obiectele partajate, numărate și eliberate, apoi joacă-te cu alocatorul care le stochează.

## Unde stau de fapt obiectele mici

CPython nu cere memorie de la sistemul de operare de fiecare dată când creezi un obiect. Obiectele de cel mult 512 octeți vin din **pymalloc**: **arene** mari împărțite în **pool-uri**, iar fiecare pool oferă blocuri de dimensiune fixă pentru o singură clasă de dimensiune (multipli de 16 octeți). Alocă și eliberează câteva obiecte și urmărește ce se întâmplă cu arenele.

Redus la scară pentru ecran: un pool real conține sute de blocuri, iar o arenă reală conține multe pool-uri. Dimensiunile sunt date de `sys.getsizeof()` pe CPython 3.12 pe 64 de biți, rotunjite în sus la următoarea clasă de dimensiune (multiplu de 16 octeți).

## De reținut

**Numele sunt referințe**Atribuirea, transmiterea argumentelor și `return` copiază referințe, niciodată obiecte. Modificările unui obiect se văd prin toate numele lui.
**Numărarea eliberează majoritatea obiectelor**Când numărul de referințe al unui obiect ajunge la 0, obiectul e eliberat pe loc, determinist. `del` doar șterge un nume.
**GC-ul e pentru cicluri**Obiectele care se referă unele la altele își țin numărul de referințe peste 0. Colectorul de cicluri le găsește și le eliberează.
**Eliberat nu înseamnă returnat**Blocurile eliberate se întorc la pymalloc, nu la sistemul de operare. O arenă e eliberată doar când toate pool-urile din ea sunt goale.

## Întrebări de interviu: memoria în Python

Răspunsuri scurte pe care le poți spune cu voce tare. Încearcă să răspunzi singur la fiecare întrebare înainte s-o deschizi.

### Ce se întâmplă în memorie la `a = [1, 2]` urmat de `b = a`?

Se creează un singur obiect listă în heap, iar ambele nume se referă la el. Atribuirea nu copiază niciodată: leagă un nume de un obiect, iar numărul de referințe al listei ajunge la 2.

### Python transmite argumentele prin valoare sau prin referință?

Niciuna. Transmite prin valoare referințe la obiecte, ceea ce se numește adesea call by sharing. O funcție poate modifica un obiect pe care i-l dai și vei vedea schimbarea, dar dacă funcția leagă parametrul de alt obiect, variabila ta nu e afectată.

### Cum eliberează CPython memoria?

În principal prin numărarea referințelor: când numărul de referințe al unui obiect scade la zero, obiectul e eliberat imediat. Un garbage collector generațional pentru cicluri găsește grupuri de obiecte care se referă doar unele la altele, pe care numărarea referințelor singură nu le poate elibera niciodată.

### Care e diferența dintre `is` și `==`?

`is` verifică identitatea: sunt acestea același obiect? `==` verifică egalitatea prin `__eq__`. Folosește `is` pentru singleton-uri precum `None` și `==` pentru tot restul.

### De ce poate fi `x is y` True pentru două numere întregi mici egale, dar nu și pentru cele mari?

CPython păstrează în cache întregii de la -5 la 256, așa că aceștia sunt mereu aceleași obiecte. Dacă alte numere sau șiruri egale împart același obiect depinde de interning și de constant folding, un detaliu de implementare pe care nu trebuie să te bazezi niciodată.

### `del x` eliberează obiectul?

Nu direct. `del` șterge un nume (sau un element dintr-un container) și decrementează numărul de referințe. Obiectul e eliberat doar când numărul ajunge la zero, sau mai târziu de garbage collector, dacă face parte dintr-un ciclu.

### De ce nu scade memoria procesului după ce șterg o listă mare?

Obiectele mici vin din pymalloc, care ia memorie de la sistemul de operare în arene mari și poate returna o arenă doar când fiecare bloc din ea e liber. Câteva obiecte supraviețuitoare țin în viață arene întregi, cum arată demo-ul pymalloc de pe această linie. Python refolosește memoria respectivă; doar că n-o dă înapoi.

### Cum depistezi o scurgere de memorie (memory leak) în Python?

Caută referințe care trăiesc prea mult: cache-uri la nivel de modul, un `functools.lru_cache` nelimitat, closure-uri și callback-uri care captează obiecte mari, și variabile globale. `tracemalloc` arată ce linii au alocat memoria care rămâne ocupată, iar `gc.get_referrers()` arată cine ține referințe la un obiect.

### Când ai folosi `weakref`?

Pentru cache-uri și referințe înapoi (back-references) care n-ar trebui să țină un obiect în viață. O referință slabă nu crește numărul de referințe, așa că obiectul poate fi totuși eliberat, după care referința slabă returnează `None`.

### Ce este numărul de referințe și cum îl vezi?

Fiecare obiect CPython are un contor al referințelor care indică spre el: nume, sloturi de listă, valori din dict, atribute. Legarea unui nume adaugă una, renunțarea la el scade una, iar la zero obiectul e eliberat imediat. `sys.getrefcount(x)` îl arată, cu unu mai mare decât te-ai aștepta, pentru că apelul însuși deține o referință.

### Ce sunt obiectele imortale?

Începând cu Python 3.12 (PEP 683), obiecte precum `None`, `True`, `False`, întregii mici și multe șiruri internate au un număr de referințe fix, care nu se schimbă niciodată, și nu sunt eliberate niciodată. Fără acele scrieri în contor se economisește muncă, paginile de memorie rămân partajate după `fork`, iar partajarea lor între thread-uri și interpretoare devine sigură.

### De ce are nevoie Python de un garbage collector dacă are numărarea referințelor?

Numărarea referințelor nu poate elibera ciclurile. Dacă o listă se conține pe ea însăși sau două obiecte indică unul spre celălalt, numărul lor de referințe nu ajunge niciodată la zero, chiar dacă nimic altceva nu le mai poate accesa. Colectorul de cicluri găsește astfel de grupuri scăzând referințele pe care și le țin unul altuia și le eliberează pe cele care rămân fără referințe din exterior.

### Ce sunt generațiile GC?

Colectorul sortează obiectele container după vârstă. Obiectele noi încep în generația cea mai tânără, scanată des pentru că majoritatea obiectelor mor tinere; supraviețuitorii sunt promovați în generații mai vechi, scanate din ce în ce mai rar. Pragurile din `gc.get_threshold()` decid când rulează fiecare.

### Ar trebui să apelezi `gc.collect()` sau `gc.disable()`?

Rareori. Numărarea referințelor eliberează aproape totul, iar colectorul rulează deja singur. Dezactivarea lui e sigură doar dacă codul tău nu creează niciodată cicluri; altfel, ele rămân în memorie (leak). Singura ajustare frecventă este `gc.freeze()` înainte de fork-ul workerilor, ca colectorul să nu atingă (și astfel să nu copieze) paginile partajate de procesele copil.

### Ce este `__del__` și de ce trebuie folosit cu grijă?

Este un finalizator care rulează când un obiect e pe cale să fie eliberat. Momentul depinde de numărul de referințe, de cicluri și de implementarea Python, așa că nu e un loc bun pentru închiderea fișierelor sau a conexiunilor, iar excepțiile ridicate în el sunt doar afișate. Folosește în schimb un context manager (`with`) sau `weakref.finalize`.

### Ce este pymalloc?

Alocatorul CPython pentru obiecte mici, de cel mult 512 octeți. Ia arene mari de la sistemul de operare, le împarte în pool-uri, iar fiecare pool oferă blocuri dintr-o singură clasă de dimensiune. Astfel, crearea și eliberarea obiectelor mici nu costă aproape nimic, pentru că majoritatea cererilor nu ajung niciodată la alocatorul sistemului.

### De ce dă `sys.getsizeof` dimensiunea greșită pentru o listă?

Măsoară doar obiectul în sine. Pentru o listă, asta înseamnă antetul plus array-ul de pointeri, nu obiectele spre care indică aceștia. O listă de o mie de șiruri raportează câțiva kilobytes, oricât de lungi ar fi șirurile. Ca să măsori toată structura, parcurge-o sau compară snapshot-uri `tracemalloc` înainte și după.

### Ce face `__slots__` pentru memorie?

Înlocuiește dicționarul `__dict__` al fiecărei instanțe cu sloturi fixe chiar în obiect. Fiecare instanță devine mai mică, iar accesul la atribute puțin mai rapid, ceea ce contează când creezi milioane de instanțe. Costul: nu poți adăuga atribute care nu sunt listate și ai nevoie de un slot `__weakref__` pentru referințe slabe.

### Ce este internarea șirurilor (string interning)?

Păstrarea unei singure copii pentru șirurile egale. CPython internează automat identificatorii și multe literale scurte, iar pe altele le poți interna cu `sys.intern()`, ceea ce economisește memorie și accelerează căutările în dict pe chei repetate. E o optimizare, nu o regulă, așa că compară întotdeauna șirurile cu `==`, niciodată cu `is`.

### De ce folosesc workerii creați cu fork tot mai multă memorie în timp, chiar dacă doar citesc date?

După `fork`, părintele și copilul partajează paginile de memorie până când unul dintre ei scrie într-o pagină. În CPython, simpla citire a unui obiect îi modifică numărul de referințe, ceea ce e o scriere, așa că paginile partajate sunt copiate una câte una. Obiectele imortale și `gc.freeze()` reduc acest efect.

### Cum e stocată o listă și de ce e rapid `append`?

O listă este un array redimensionabil de pointeri către obiecte stocate în altă parte. Când e plină, CPython alocă un array mai mare, cu spațiu de rezervă, așa că majoritatea operațiilor append doar ocupă un slot liber, iar copierea ocazională se amortizează: O(1) amortizat. Inserarea sau ștergerea la început este O(n), pentru că toți pointerii de după se mută.

### De ce ocupă atât de multă memorie o listă de un milion de int-uri?

Fiecare element este un pointer (8 octeți) către un obiect int complet (28 de octeți sau mai mult), cu propriul antet. `array.array('q')` sau un array NumPy stochează în schimb valorile brute de 8 octeți una lângă alta, de câteva ori mai compact și mult mai rapid de parcurs în C.

### Cum economisesc memorie generatoarele?

Un generator produce valorile pe rând și păstrează între ele doar frame-ul său suspendat. `sum(x * x for x in range(10**8))` are nevoie de memorie constantă, în timp ce varianta cu list comprehension construiește mai întâi o listă de o sută de milioane de int-uri. Capcana: un generator poate fi consumat o singură dată.

### Ce este un `memoryview`?

O vedere asupra memoriei altui obiect care suportă buffer protocol, cum ar fi `bytes`, `bytearray` sau `array`. Un slice dintr-un `memoryview` nu copiază datele, așa că parsarea bucată cu bucată a unui buffer binar mare rămâne rapidă și nu folosește memorie suplimentară.

### Cum poate un closure să țină în viață un obiect mare?

O funcție imbricată păstrează într-o celulă (cell) fiecare variabilă pe care o folosește din scope-ul exterior. Cât timp funcția există, de exemplu stocată ca callback, acele obiecte nu pot fi eliberate, chiar dacă aveai nevoie doar de o valoare mică dintr-unul uriaș. Extrage ce-ți trebuie înainte să definești funcția.

### Cum poate o excepție să producă o scurgere de memorie?

Un traceback are referințe la fiecare frame prin care a trecut, iar fiecare frame are referințe la variabilele sale locale. Dacă stochezi o excepție, de exemplu într-o listă de erori, toate acele variabile locale rămân în viață. De aceea Python șterge numele după `except E as e:`; stochează `str(e)` dacă ai nevoie doar de mesaj.

### Ce face `functools.lru_cache` cu memoria?

Păstrează o referință la fiecare argument și rezultat pe care îl stochează. Cu `maxsize=None` sau `@cache`, crește la nesfârșit. Pe o metodă stochează și `self`, ceea ce ține în viață fiecare instanță. Dă-i o dimensiune limitată și pune în cache funcții, nu metode.

### Ce returnează `id()`?

Un întreg unic pentru un obiect cât timp acesta trăiește. În CPython este adresa din memorie. După ce un obiect e eliberat, un obiect nou poate primi aceeași adresă, așa că două obiecte diferite, create unul după altul, pot raporta același `id`.

### Cum funcționează numărarea referințelor în Python free-threaded?

Fără GIL, actualizările contorului din thread-uri diferite ar produce un race condition (condiție de cursă). Build-urile free-threaded folosesc **biased reference counting**: thread-ul care deține un obiect actualizează un contor local fără operații atomice, iar celelalte thread-uri actualizează atomic un contor partajat. Unele obiecte folosesc numărare amânată (deferred), iar memoria vine din mimalloc în loc de pymalloc.

Numărul de referințe de pe hartă include doar referințele create de program. `sys.getrefcount()` raportează cu una în plus (propriul argument), iar obiectele imortale raportează o valoare fixă uriașă.
