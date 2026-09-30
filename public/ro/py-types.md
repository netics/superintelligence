---
title: "Tipurile din Python explicate: dispatch-ul operatorilor, +=, hashing | Runtime lines"
description: "Tipurile predefinite și unde să-l folosești pe fiecare, cum se face dispatch-ul pentru a + b, când += modifică obiectul pe loc și cum se calculează hash-ul cheilor dintr-un dict."
url: https://superintelligence.ro/ro/py-types
alternate_en: https://superintelligence.ro/py-types.md
alternate_ro: https://superintelligence.ro/ro/py-types.md
---

# Tipurile din Python și cum se înțeleg între ele

Totul în Python este un obiect, iar tipul lui decide ce fac operatorii cu el. Explorează rețeaua de tipuri, trimite doi operanzi prin mecanismul operatorilor, apoi urmărește cum `+=` și cheile de dict se comportă în moduri care îi surprind pe cei mai mulți.

## Ce se întâmplă când scrii a + b

Python îl întreabă mai întâi pe operandul din stânga. Dacă metoda lui returnează `NotImplemented`, vine rândul operandului din dreapta, cu metoda reflectată. Alege două valori și un operator; fiecare pas de mai jos a fost înregistrat pe obiecte CPython reale.

## += modifică obiectul pe loc, sau nu

`x += y` încearcă mai întâi `x.__iadd__(y)`. Tipurile mutabile îl implementează și modifică obiectul pe loc; cele imutabile nu, așa că Python recurge la `x = x + y` și reasociază numele.

## Chei de dict și hashing

Un dict își păstrează intrările în ordinea inserării, plus un mic tabel de indecși. `hash(key)` alege un slot, iar cheile egale trebuie să aibă hash-uri egale, și exact de aceea `1`, `True` și `1.0` ajung să fie o singură cheie.

## Întrebări de interviu: tipurile Python

Răspunsuri scurte pe care le poți spune cu voce tare. Încearcă să răspunzi singur la fiecare întrebare înainte s-o deschizi.

### Ce tipuri predefinite sunt mutabile?

`list`, `dict`, `set` și `bytearray`, plus majoritatea claselor pe care le scrii tu. `int`, `float`, `complex`, `bool`, `str`, `bytes`, `tuple`, `frozenset`, `range` și `None` sunt imutabile: orice „modificare” construiește un obiect nou.

### Ce face un obiect hashable și de ce contează?

Are nevoie de un `__hash__` care nu se schimbă niciodată pe durata vieții obiectului, iar obiectele egale trebuie să aibă același hash. Doar obiectele hashable pot fi chei de dict sau elemente de set, de aceea o listă nu poate fi cheie, dar un tuplu de elemente hashable poate.

### De ce `1`, `True` și `1.0` ajung să fie o singură cheie de dict?

Sunt egale la comparare și au același hash, așa că dict-ul le tratează ca pe o singură cheie. Se păstrează primul obiect-cheie și se înlocuiește doar valoarea, cum arată pas cu pas exemplul de hashing de pe această linie.

### Ce se întâmplă când Python evaluează `a + b`?

Apelează `a.__add__(b)`. Dacă acesta returnează `NotImplemented`, încearcă `b.__radd__(a)` și aruncă `TypeError` dacă amândouă renunță. Dacă tipul lui b este o subclasă a tipului lui a și suprascrie `__radd__`, b are prioritate.

### `x += y` este același lucru cu `x = x + y`?

Nu pentru tipurile mutabile. `+=` apelează mai întâi `__iadd__`, care extinde o listă pe loc, așa că toate numele legate de acea listă văd schimbarea. Tipurile imutabile recurg la `x = x + y` și reasociază doar x. Tot de aceea `pair[0] += [2]` pe un tuplu și modifică lista, și aruncă o excepție.

### Ce problemă are `def f(items=[])`?

Valorile implicite sunt evaluate o singură dată, la definirea funcției, așa că toate apelurile folosesc aceeași listă. Folosește `items=None` și creează o listă nouă în interiorul funcției.

### De ce scrii `x is None` în loc de `x == None`?

`None` este un singleton, așa că identitatea e testul precis. E și mai rapid și nu poate fi păcălit de o clasă al cărei `__eq__` răspunde da la orice.

### list, tuple, set sau dict: cum alegi?

O listă pentru o colecție ordonată pe care o modifici, un tuplu pentru o înregistrare fixă sau o cheie hashable, un set pentru unicitate și teste rapide de apartenență, iar un dict pentru căutare după cheie. Alege un `frozenset` când ai nevoie de un set hashable.

### Cum copiezi o structură imbricată?

`list(x)`, `x.copy()`, `x[:]` și `copy.copy()` fac copii superficiale: noul container conține aceleași obiecte interioare. `copy.deepcopy()` copiază totul recursiv.

### Un tuplu e imutabil. De ce poate `t[0] += [1]` să arunce o eroare și totodată să modifice tuplul?

`+=` apelează întâi `list.__iadd__`, care extinde pe loc lista din tuplu, apoi încearcă să stocheze rezultatul înapoi în `t[0]`, ceea ce aruncă `TypeError`. Sloturile tuplului nu se pot schimba, dar obiectele din ele da. Din același motiv, un tuplu care conține o listă nu e hashable.

### Care e contractul dintre `__eq__` și `__hash__`?

Obiectele egale trebuie să aibă hash-uri egale, iar hash-ul nu are voie să se schimbe cât timp obiectul se află într-un set sau dict. De aceea, când definești `__eq__`, `__hash__` devine `None`: Python face clasa non-hashable până când definești un hash bazat pe aceleași câmpuri. `@dataclass(frozen=True)` le face pe amândouă pentru tine.

### Cum funcționează un dict pe dinăuntru?

E o tabelă hash. Hash-ul cheii alege un slot dintr-un mic array de indecși, coliziunile se rezolvă prin sondarea altor sloturi (probing), iar indexul trimite într-un array compact de intrări păstrate în ordinea inserării. Căutările, inserările și ștergerile sunt O(1) în medie, iar o potrivire se confirmă cu `is` sau `==` pe cheie.

### Dict-urile păstrează ordinea?

Da, ordinea inserării e garantată din Python 3.7. `OrderedDict` rămâne util: are `move_to_end`, comparația de egalitate ține cont de ordine și e la îndemână pentru cache-uri LRU. Set-urile nu au deloc ordine.

### Ce este duck typing?

Pe Python îl interesează ce poate face un obiect, nu ce clasă are: orice are `__iter__` poate fi parcurs într-o buclă, orice are `read()` poate ține loc de fișier. De obicei, codul pur și simplu încearcă operația și tratează excepția (EAFP). Pentru type checkere, `typing.Protocol` descrie o astfel de formă fără moștenire.

### `NotImplemented` sau `NotImplementedError`?

`NotImplemented` este o valoare pe care o returnezi dintr-o metodă binară precum `__add__` sau `__eq__` ca să spui „nu cunosc acest tip”, iar Python încearcă atunci metoda celuilalt operand. `NotImplementedError` este o excepție pe care o arunci într-o metodă pe care subclasele trebuie s-o suprascrie. Dacă o arunci pe prima sau o returnezi pe a doua, ai un bug în ambele cazuri.

### Când apelează Python `__radd__`?

Pentru `a + b`, când `a` nu are `__add__` sau aceasta returnează `NotImplemented`, Python încearcă `b.__radd__(a)`. O excepție: dacă tipul lui `b` e o subclasă a tipului lui `a` și suprascrie `__radd__`, metoda lui e încercată prima, ca subclasele să poată prelua controlul. Așa funcționează `sum()` pe tipuri proprii, pornind de la `0`.

### Sunt verificate type hint-urile la runtime?

Nu. Python le ignoră când rulează codul; unelte precum mypy și pyright le verifică înainte de rulare. Sunt disponibile la runtime prin `typing.get_type_hints()` și `annotationlib`, iar așa validează datele biblioteci ca Pydantic și FastAPI. Din 3.14, adnotările sunt evaluate lazy, doar când le cere ceva.

### Poate un int din Python să facă overflow?

Nu, int-urile au precizie arbitrară și cresc cât e nevoie; `sys.maxsize` e dimensiunea maximă a unui container, nu cel mai mare int. Int-urile mari doar devin mai lente. Din 3.11, conversia unui int cu peste 4300 de cifre în sau din string aruncă implicit `ValueError`, ca să prevină atacurile de tip denial-of-service.

### Ce fac `//` și `%` cu numerele negative?

`//` rotunjește în jos, spre minus infinit, deci `-7 // 2` dă `-4`, iar `%` ia semnul împărțitorului: `-7 % 2` dă `1`. JavaScript, C și Java trunchiază în schimb spre zero. Și `int(-3.5)` trunchiază, dând `-3`.

### De ce `round(2.5)` dă 2?

Python rotunjește jumătățile la cel mai apropiat număr par (rotunjirea bancherului), deci `round(2.5)` dă 2, iar `round(3.5)` dă 4; asta evită o eroare sistematică atunci când aduni multe valori rotunjite. `round(2.675, 2)` dă `2.67`, pentru că 2.675 nu poate fi stocat exact. Pentru bani, folosește `decimal.Decimal`.

### `str` sau `bytes`?

`str` e text, o secvență de code point-uri Unicode. `bytes` sunt date brute pe 8 biți, din fișiere, socketuri sau hash-uri. Python 3 nu convertește niciodată implicit între ele: faci `encode()` din text în bytes și `decode()` din bytes în text la granițele programului, specificând encoding-ul, de obicei UTF-8.

### De ce poate `len("é")` să fie 2?

`len` numără code point-uri, nu ce vezi. „é” poate fi un singur code point (U+00E9) sau două: „e” plus un accent combinant. Normalizează cu `unicodedata.normalize("NFC", s)` înainte să compari sau să numeri. Intern, CPython stochează fiecare string cu 1, 2 sau 4 octeți pe caracter, în funcție de cel mai lat caracter din el.

### De ce e lentă construirea unui string cu `+=` într-o buclă?

String-urile sunt imutabile, așa că fiecare `+=` poate crea un string nou și copia tot ce s-a adunat până atunci, adică O(n²) în total. CPython extinde uneori pe loc, dar alte implementări nu, și nu te poți baza pe asta. Adună bucățile într-o listă și apelează o singură dată `"".join(parts)`, sau folosește `io.StringIO`.

### `isinstance(x, T)` sau `type(x) is T`?

`isinstance` acceptă subclase și clase de bază abstracte precum `collections.abc.Mapping`, ceea ce e aproape mereu ce vrei. Are o surpriză clasică: `bool` e subclasă a lui `int`, deci `isinstance(True, int)` e adevărat, iar `True + True` dă 2. Folosește `type(x) is T` doar când subclasele trebuie respinse.

### Cât de rapid e `x in` pe o listă, un set și un dict?

O listă verifică pe rând fiecare element: O(n). Set-urile și dict-urile calculează hash-ul lui `x` și se uită într-un singur slot: O(1) în medie. Să transformi o listă în set înainte să verifici mii de valori într-o buclă e una dintre cele mai simple optimizări cu câștig mare. Și `x in range(...)` e O(1): e doar aritmetică.

### namedtuple, dataclass, TypedDict sau dict?

`namedtuple`: un tuplu imutabil și ușor, cu nume de câmpuri. `dataclass`: o clasă obișnuită cu `__init__`, `__repr__` și `__eq__` generate, mutabilă sau frozen, cu valori implicite și metode. `TypedDict`: type hints pentru dict-uri care rămân dict-uri simple, cum ar fi payload-urile JSON. Un `dict` simplu: chei cu adevărat dinamice.

### Este `sorted` stabil și de ce are nevoie?

Da. Sortarea din Python e stabilă, deci elementele cu chei egale își păstrează ordinea și poți sorta după mai multe chei în mai multe treceri, începând cu cea mai puțin importantă. E O(n log n) și foarte rapidă pe date deja parțial sortate. Are nevoie doar de `<`; dacă amesteci tipuri care nu pot fi comparate, cum ar fi `None` și `int`, primești `TypeError`.

### Cum decide Python dacă un obiect e truthy?

Apelează `__bool__` dacă clasa îl definește, altfel `__len__`, iar orice altceva e considerat adevărat. Așadar `None`, `False`, zero din orice tip numeric și containerele goale sunt falsy. Atenție la `if not x:` când 0 sau o listă goală sunt valori valide; scrie în schimb `if x is None:`.

### Care e diferența dintre un iterabil și un iterator?

Un iterabil, cum e o listă, îți poate da un iterator nou cu `iter()`, de câte ori vrei. Un iterator își ține minte poziția, returnează următorul element din `__next__` și se consumă după o singură trecere. Generatoarele și obiectele fișier sunt iteratori, de aceea a doua parcurgere a unuia nu produce nimic.

Secvențele de dispatch au fost înregistrate apelând fiecare metodă dunder pe obiecte reale în CPython 3.12. Hash-urile string-urilor se schimbă la fiecare rulare dacă nu e setat `PYTHONHASHSEED`, deci hash-ul afișat pentru `'1'` e doar o valoare posibilă.
