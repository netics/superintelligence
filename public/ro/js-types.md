---
title: "Tipurile din JavaScript explicate: typeof, ==, copii, float-uri | Runtime lines"
description: "Macazul typeof, cum stochează V8 fiecare tip, copii versus referințe, algoritmul exact al lui ==, valorile truthy și falsy și cei 64 de biți dintr-un număr."
url: https://superintelligence.ro/ro/js-types
alternate_en: https://superintelligence.ro/js-types.md
alternate_ro: https://superintelligence.ro/ro/js-types.md
---

# Tipurile JavaScript, sortate la macaz

Orice valoare JavaScript aparține unuia dintre cele șapte tipuri primitive sau este un obiect. Trimite valori prin macazul `typeof`, întoarce cardurile ca să vezi cum le stochează V8, urmărește exact ce face `==` și descompune un număr bit cu bit.

## Șapte tipuri primitive și un tip obiect

Primitivele sunt imutabile și se compară după valoare; obiectele sunt mutabile și se compară după referință. Întoarce un card ca să vezi cum reprezintă V8 acel tip.

**Stivă sau heap?** Vei citi des că primitivele stau pe stivă, iar obiectele pe heap. În V8 aproape totul stă pe heap, iar o variabilă ține un pointer către valoare; doar întregii mici (Smi) încap direct în slot. Ce deosebește cu adevărat primitivele e că nu pot fi modificate, așa că partajarea uneia nu se observă.

## Copie sau partajare?

Atribuirea unei primitive o copiază. Atribuirea unui obiect copiază o referință. Spread-ul copiază un singur nivel; `structuredClone` copiază toate nivelurile.

## Ce face de fapt ==

`===` nu convertește niciodată. `==` urmează pas cu pas o listă fixă de reguli de conversie din specificație. Alege două valori și urmărește pașii sau dă click pe orice pătrat din grilă.

## Truthy sau falsy?

Un `if` își convertește condiția cu `Boolean()`. Exact opt valori sunt falsy; toate celelalte, inclusiv câteva surprinzătoare, sunt truthy. Alege o valoare, apoi coșul în care crezi că îi e locul.

## În interiorul unui număr

Un `number` JavaScript este un double IEEE 754: 1 bit de semn, 11 biți de exponent și 52 de biți de fracție. Scrie o valoare, alege una predefinită sau inversează orice bit și urmărește cum se schimbă numărul.

## Întrebări de interviu: tipurile JavaScript

Răspunsuri scurte pe care le poți spune cu voce tare. Încearcă să răspunzi singur la fiecare întrebare înainte s-o deschizi.

### Ce tipuri are JavaScript?

Șapte primitive (`undefined`, `null`, `boolean`, `number`, `bigint`, `string` și `symbol`), plus obiecte. Array-urile, funcțiile, datele calendaristice, map-urile și instanțele de clasă sunt toate obiecte.

### Ce poate returna `typeof`?

Opt șiruri: "undefined", "boolean", "number", "bigint", "string", "symbol", "object" și "function". `typeof null` este "object" din cauza unui bug istoric, așa că verifică null cu `=== null`, iar array-urile cu `Array.isArray()`.

### `==` sau `===`?

Folosește implicit `===`, care nu convertește niciodată tipurile. `==` aplică reguli de conversie: `null` și `undefined` sunt egale doar între ele, valorile booleene devin numere, un șir comparat cu un număr devine număr, iar obiectele sunt convertite în primitive. Singura utilizare uzuală a lui `==` este `x == null`, care verifică dacă valoarea e null sau undefined.

### JavaScript transmite argumentele prin referință?

Nu. Totul se transmite prin valoare, dar valoarea unei variabile de tip obiect este o referință. O funcție poate modifica obiectul pe care i-l dai, dar reatribuirea parametrului nu îți schimbă variabila. În Python e la fel.

### Copie superficială sau copie profundă?

Spread-ul, `Object.assign` și `slice()` copiază un singur nivel, așa că obiectele imbricate rămân partajate. `structuredClone` face o copie profundă, inclusiv pentru `Map`, `Set`, `Date` și referințe circulare, dar aruncă o excepție la funcții, iar instanțele de clasă devin obiecte simple.

### De ce `0.1 + 0.2 !== 0.3` dă true?

Numerele sunt double-uri IEEE 754 pe 64 de biți, iar 0.1, 0.2 și 0.3 nu au o reprezentare binară exactă, așa că fiecare e stocat ca cel mai apropiat double, iar erorile de rotunjire nu se anulează reciproc. Compară cu o toleranță sau ține sumele de bani ca întregi, în cenți.

### Ce valori sunt falsy?

`false`, `0`, `-0`, `0n`, `""`, `null`, `undefined` și `NaN` (plus vechiul `document.all` din browsere). Orice altceva e truthy, inclusiv `"0"`, `"false"`, `[]` și `{}`.

### Ce este `Number.MAX_SAFE_INTEGER` și de ce contează?

253 − 1. Peste această valoare, nu orice întreg poate fi reprezentat, așa că un ID pe 64 de biți dintr-o bază de date se poate schimba pe tăcute când e parsat ca număr. Păstrează astfel de ID-uri ca șiruri sau ca `BigInt`.

### `null` sau `undefined`?

`undefined` înseamnă că o valoare n-a fost setată niciodată: o proprietate lipsă, o variabilă neatribuită, o funcție fără return. `null` este un „fără valoare” explicit, pe care îl atribui tu. JSON are `null`, dar nu are `undefined`, iar `JSON.stringify` omite proprietățile a căror valoare este `undefined`.

### De ce `typeof null` este `"object"`?

Un bug din primul motor JavaScript: valorile aveau o etichetă de tip, obiectele aveau eticheta 0, iar `null` era pointerul null, care se citea tot ca 0. Dacă s-ar schimba acum, s-ar strica web-ul, așa că rămâne așa. Verifică null cu `x === null`.

### Cum verifici sigur că o valoare este un array?

`Array.isArray(x)`. `typeof` returnează `"object"`, iar `instanceof Array` eșuează pentru array-uri din alt realm, cum ar fi un iframe sau un context `vm`, pentru că fiecare realm are propriul constructor `Array`.

### Ce este `NaN` și cum îl testezi?

Valoarea IEEE 754 pentru un rezultat nedefinit, cum ar fi `0 / 0` sau `Number("abc")`. Tipul lui este `number` și nu este egal cu nimic, nici măcar cu el însuși, așa că `x === NaN` e mereu false. Folosește `Number.isNaN(x)`; funcția globală `isNaN` convertește mai întâi, așa că `isNaN("abc")` este true.

### Prin ce diferă `Object.is` de `===`?

Exact în două cazuri: `Object.is(NaN, NaN)` este true, iar `Object.is(0, -0)` este false. În rest se comportă ca `===`. React îl folosește ca să decidă dacă state-ul s-a schimbat, iar `Map`, `Set` și `includes` folosesc o variantă care consideră `0` și `-0` egale.

### Cum poate o primitivă precum `"abc"` să aibă metode?

Când scrii `"abc".toUpperCase()`, motorul folosește un wrapper `String` temporar ca să găsească metoda în `String.prototype`; primitiva în sine nu se schimbă. Nu crea niciodată wrappere de mână cu `new String` sau `new Boolean`: `new Boolean(false)` este un obiect, deci e truthy.

### Cum transformă JavaScript un obiect într-o primitivă?

Apelează `obj[Symbol.toPrimitive](hint)`, dacă există. Altfel, încearcă `valueOf()` și apoi `toString()` pentru un hint numeric, și invers pentru un hint de tip șir. De aceea `[] + {}` dă `"[object Object]"`: `[]` devine `""`, `{}` devine `"[object Object]"`, iar `+` concatenează șirurile.

### Ce este `BigInt` și când îl folosești?

Un tip întreg de orice mărime, scris `123n`, pentru care `typeof` dă `"bigint"`. Folosește-l pentru ID-uri, sume de bani în subunități sau orice depășește 253. Nu îl poți amesteca cu numere în operații aritmetice (`1n + 1` aruncă un `TypeError`), nu are zecimale, iar `JSON.stringify` aruncă o excepție când îl întâlnește.

### La ce folosește un `Symbol`?

E o valoare unică, folosită mai ales ca cheie de proprietate care nu se poate ciocni cu nicio altă cheie, nici măcar cu una cu aceeași descriere. `for...in`, `Object.keys` și `JSON.stringify` ignoră cheile de tip symbol. Cele predefinite, ca `Symbol.iterator`, îți permit să conectezi obiectele la facilități ale limbajului, cum ar fi `for...of`.

### `const` face un obiect imutabil?

Nu. `const` te împiedică doar să reasociezi numele; obiectul spre care arată se poate schimba în continuare. `Object.freeze` blochează modificările proprietăților proprii ale obiectului, dar e superficial: obiectele imbricate rămân mutabile dacă nu le îngheți și pe ele.

### `structuredClone` sau `JSON.parse(JSON.stringify(x))`?

Preferă `structuredClone`: copiază `Date`, `Map`, `Set`, typed arrays și referințe circulare. Drumul dus-întors prin JSON pierde `undefined` și funcțiile, transformă datele calendaristice în șiruri și `NaN` în `null`, și aruncă o excepție la cicluri și la `BigInt`. Niciuna dintre variante nu copiază funcții și nu păstrează prototipurile claselor.

### Ce este un Smi?

Un întreg mic pe care V8 îl stochează chiar în pointer, marcat prin bitul cel mai puțin semnificativ, așa că nu necesită alocare. Numerele care nu încap, cum ar fi fracțiile, `-0` sau întregii mari, devin HeapNumber: un float pe 64 de biți într-un obiect separat pe heap. De aceea codul care lucrează mult cu întregi e adesea mai rapid.

### Ce sunt clasele ascunse (hidden classes) și de ce contează ordinea proprietăților?

V8 dă fiecărui obiect o clasă ascunsă, sau shape, care reține proprietățile lui și locul în care sunt stocate. Obiectele construite cu aceleași proprietăți, în aceeași ordine, au același shape, așa că accesul la proprietăți poate fi pus în cache și devine foarte rapid. Adăugarea proprietăților în ordini diferite sau folosirea lui `delete` creează shape-uri noi și încetinește acel cod.

### Ce sunt array-urile packed și holey?

V8 ține evidența a ce conține un array: doar întregi mici, doar double-uri sau orice, și dacă are goluri. Array-urile packed de întregi mici sunt cele mai rapide. Tranzițiile merg într-un singur sens: după `arr.push(1.5)` sau un gol ca `arr[100] = 1`, acel array nu mai redevine niciodată rapid. `new Array(n)` pornește ca holey.

### De ce are JavaScript `-0`?

Float-urile IEEE 754 păstrează un bit de semn chiar și pentru zero. `0 === -0` este true, dar `1 / -0` este `-Infinity`, iar `Object.is(0, -0)` este false. Apare când o valoare negativă mică e rotunjită la zero și îți poate spune din ce direcție s-a apropiat o valoare de zero.

### Cum lucrezi cu bani fără erori de float?

Stochează întregi în subunități, cum ar fi cenții, cu `BigInt` dacă pot deveni mari, sau folosește o bibliotecă de numere zecimale, și formatează cu `Intl.NumberFormat`. `toFixed` nu rezolvă problema: rotunjește valoarea binară, așa că `(1.005).toFixed(2)` dă `"1.00"`, pentru că 1.005 este de fapt 1.00499999...

### `parseInt` sau `Number`?

`parseInt` citește cifre până dă de altceva, așa că `parseInt("12px")` dă 12. `Number` convertește tot șirul sau returnează `NaN`, așa că `Number("12px")` dă `NaN`, dar `Number("")` dă 0. Dă-i mereu lui `parseInt` baza (radix) și nu-i da niciodată numere: `parseInt(0.0000005)` dă 5.

### Când este acceptabil `==`?

Pentru `x == null`, care e true doar pentru `null` și `undefined`, așa că le prinde pe amândouă dintr-o singură verificare. Multe ghiduri de stil permit exact acest caz și folosesc `===` în rest.

### Care e diferența dintre `??` și `||`?

`a || b` recurge la `b` pentru orice valoare falsy, inclusiv `0`, `""` și `false`. `a ?? b` face asta doar pentru `null` și `undefined`. Pentru valori implicite ca `count ?? 10` ai nevoie de `??`, ca să păstrezi un 0 real.

### `Map` sau un obiect simplu?

Folosește un `Map` pentru dicționare cu chei dinamice: cheile pot fi orice valoare, inclusiv obiecte, are `size`, se iterează în ordinea inserării și nu are chei moștenite, ca `__proto__`, de care să-ți faci griji. Cheile unui obiect sunt mereu șiruri sau simboluri, iar cheile care arată ca întregi sunt listate primele, în ordine numerică. Folosește obiecte pentru înregistrări cu câmpuri fixe.

### La ce folosește un `WeakMap`?

Ca să atașezi date la obiecte care nu sunt ale tale, fără să le ții în viață. Cheile trebuie să fie obiecte, iar odată ce o cheie nu mai e accesibilă din altă parte, intrarea poate fi colectată de garbage collector. Pentru că intrările pot dispărea oricând, un `WeakMap` nu poate fi iterat și nu are `size`. Utilizări tipice: cache-uri și date private pentru fiecare nod DOM.

Rezultatele typeof, conversiile și regulile truthy/falsy respectă specificația ECMAScript și coincid cu V8 din Node.js și Chrome. Exemplul de copiere afișează `10 20 Bob [ 'dev', 'ops' ] [ 'dev', 'ops', 'qa' ]` în Node.js 22.
