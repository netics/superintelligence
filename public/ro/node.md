---
title: "Event loop-ul Node.js explicat pas cu pas | Runtime lines"
description: "Cum jonglează un singur thread cu mii de sarcini: stiva de apeluri (call stack), cozile nextTick și de promise-uri, timerele, fazele libuv și thread pool-ul."
url: https://superintelligence.ro/ro/node
alternate_en: https://superintelligence.ro/node.md
alternate_ro: https://superintelligence.ro/ro/node.md
---

# Event loop-ul Node.js, stație cu stație

Alege un scenariu de pe linia de mai jos, apoi apasă Pornește sau avansează pas cu pas cu săgețile. Fiecare callback călătorește din codul tău prin cozile Node până pe stiva de apeluri (call stack), așa că vezi exact de ce output-ul apare în ordinea aceea.

## Regulile din spatele fiecărei rulări

Fiecare scenariu de mai sus respectă aceleași cinci reguli, în această ordine.

- **Rulează scriptul până la capăt:** Codul sincron se termină întotdeauna primul. Nimic nu îl întrerupe: nici timerele, nici I/O-ul.
- **Golește microtask-urile:** Toate callback-urile `process.nextTick`, apoi toate callback-urile de promise-uri. Repetă până când ambele cozi sunt goale.
- **Parcurge bucla:** timers, pending callbacks, idle/prepare, poll, check, close callbacks. Fiecare fază rulează callback-urile care așteaptă în coada ei.
- **Golește microtask-urile după fiecare callback:** Începând cu Node 11, un promise sau un nextTick creat într-un callback rulează înainte de următorul callback din aceeași fază.
- **Așteaptă sau ieși:** Faza poll blochează cât timp mai există I/O în curs. Când nu mai rămân timere, handle-uri sau cereri, procesul se încheie.

**Modulele ES sunt diferite.** Într-un fișier `.mjs` sau cu `"type": "module"`, codul de la nivelul superior rulează deja într-un job de promise, așa că callback-urile de promise-uri rulează înainte de `nextTick`. Acolo, exemplul clasic afișează **A E C D B**.

## Unde își trimite fiecare API callback-ul

Folosește asta ca pe o hartă a traseelor când citești cod async necunoscut: găsești API-ul și știi în ce coadă așteaptă callback-ul lui.

## Întrebări de interviu: event loop-ul Node.js

Răspunsuri scurte pe care le poți spune cu voce tare. Încearcă să răspunzi singur la fiecare întrebare înainte s-o deschizi.

### Node rulează pe un singur thread. Cum gestionează mii de conexiuni?

JavaScript-ul tău rulează pe un singur thread, dar așteptarea nu. Node predă I/O-ul de rețea sistemului de operare (epoll, kqueue, IOCP) și operațiile pe sistemul de fișiere thread pool-ului din libuv, apoi rulează callback-ul tău pe thread-ul principal când rezultatul e gata. Thread-ul principal nu așteaptă niciodată; doar rulează callback-uri.

### Ce este, de fapt, event loop-ul?

O buclă din libuv care trece ciclic prin faze: timers, pending callbacks, poll (I/O), check (`setImmediate`) și close callbacks. Fiecare fază are o coadă, iar fiecare callback rulează până la capăt pe stiva de apeluri înainte să înceapă următorul.

### În ce ordine rulează codul sincron, `process.nextTick`, promise-urile și timerele?

Mai întâi codul sincron. Apoi toată coada `nextTick`, apoi toată coada de microtask-uri a promise-urilor. Abia după aceea bucla trece la callback-urile `setTimeout` din faza timers și la `setImmediate` din faza check. Ambele cozi de microtask-uri sunt golite din nou după fiecare callback în parte.

### De ce rulează promise-urile înaintea lui `process.nextTick` într-un modul ES?

Node pornește un modul ES din interiorul unui job de promise, așa că, atunci când codul de la nivelul superior se termină, V8 încă golește coada de microtask-uri și rulează callback-urile de promise-uri pe care le-ai pus în coadă înainte ca Node să ajungă la coada `nextTick`. În CommonJS, coada `nextTick` vine prima. Exemplele de pe această linie sunt CommonJS: rulează scenariul 1 ca fișier `.mjs` și C și D își schimbă locurile.

### `setTimeout(fn, 0)` sau `setImmediate(fn)`: care rulează primul?

Din modulul principal nu e garantat; depinde de cât de repede pornește bucla. Într-un callback de I/O, `setImmediate` câștigă întotdeauna, pentru că faza check vine imediat după faza poll.

### Ce face thread pool-ul din libuv și cât de mare e?

Rulează munca pentru care sistemul de operare nu are un API neblocant: majoritatea apelurilor `fs`, `dns.lookup` și funcțiile `crypto` și `zlib` care consumă mult CPU. Are implicit 4 thread-uri, număr setat prin `UV_THREADPOOL_SIZE`. Socket-urile de rețea nu îl folosesc.

### Ce blochează event loop-ul și cum repari asta?

Orice muncă sincronă de durată: un `JSON.parse` uriaș, apeluri sincrone `fs` sau `crypto`, bucle grele, un regex cu backtracking catastrofal. Cât timp rulează, nicio cerere, niciun timer și niciun promise nu pot avansa. Împarte munca în bucăți, procesează datele ca stream sau mut-o în `worker_threads`.

### De ce timerul meu de 10 ms s-a declanșat după 100 ms?

Întârzierea unui timer e un minim, nu o garanție. Callback-ul rulează în prima fază timers de după expirarea întârzierii, așa că un callback lung dinaintea lui îl întârzie, exact ca în scenariul `loop done at 100 ms` de pe această linie.

### Poate `process.nextTick` să blocheze event loop-ul (starvation)?

Da. Coada `nextTick` e golită complet înainte ca bucla să continue, așa că un callback care programează mereu un alt `nextTick` oprește tot I/O-ul. `setImmediate`, în schimb, lasă loc I/O-ului.

### Când ai folosi `worker_threads` și când `cluster`?

`worker_threads` rulează JavaScript în paralel în același proces și pot partaja memorie prin `SharedArrayBuffer`; folosește-le pentru sarcini care consumă mult CPU. `cluster`, sau mai multe procese în spatele unui load balancer, rulează procese Node separate, astfel încât un server să poată folosi toate nucleele.

### Care e diferența dintre microtask-uri și macrotask-uri?

Macrotask-urile sunt callback-urile pe care bucla le preia fază cu fază: timere, callback-uri de I/O, `setImmediate`, evenimente close. Microtask-urile sunt reacțiile promise-urilor și callback-urile `queueMicrotask`, plus coada proprie a Node, `nextTick`. După fiecare callback de macrotask, Node golește complet ambele cozi de microtask-uri înainte să-l ruleze pe următorul.

### Prin ce diferă `queueMicrotask` de `process.nextTick`?

`queueMicrotask` pune un callback în coada de microtask-uri a V8, aceeași coadă pe care o folosesc callback-urile de promise-uri. `process.nextTick` folosește o coadă separată a Node care, în CommonJS, rulează înaintea ei. Preferă `queueMicrotask`: funcționează la fel în browsere și în Node și nu poate trece înaintea promise-urilor pe care le-ai pus deja în coadă.

### Ce se întâmplă în faza poll?

Bucla cere sistemului de operare operațiile de I/O terminate și rulează callback-urile lor. Dacă nu are nimic de rulat, așteaptă acolo I/O nou, dar doar până când vine rândul celui mai apropiat timer. Dacă există un `setImmediate` în coadă, nu așteaptă deloc și trece direct la faza check.

### Cum se mapează `async`/`await` pe event loop?

O funcție `async` rulează sincron până la primul `await`. Acolo îi returnează apelantului un promise în așteptare (pending), iar restul funcției e reluat mai târziu ca microtask, după ce valoarea așteptată e finalizată (settled). Nimic nu rulează în paralel: `await` doar îți împarte funcția în callback-uri.

### Ce se întâmplă cu un promise respins și netratat sau cu o excepție neprinsă?

Începând cu Node 15, o respingere netratată emite `unhandledRejection`, iar dacă nimic nu o tratează, e aruncată ca excepție neprinsă și procesul se încheie cu eroare. Într-un handler `uncaughtException`, loghează și ieși: procesul e într-o stare necunoscută, așa că lasă un supervisor să-l repornească în loc să continui.

### Evită `fs.promises` thread pool-ul?

Nu. Variantele cu promise, cu callback și sincronă ale `fs` fac aceeași muncă; cele asincrone o rulează pe thread pool-ul din libuv și diferă doar prin felul în care primești rezultatul. I/O-ul de rețea, inclusiv `fetch` și `http`, e partea care merge direct la sistemul de operare, fără pool.

### De ce poate un DNS lent să încetinească citirea fișierelor?

`dns.lookup`, pe care `http` și `net` îl folosesc implicit, apelează `getaddrinfo` pe thread pool. Cu doar 4 thread-uri, câteva lookup-uri lente pot ocupa tot pool-ul, iar operațiile `fs`, `crypto` și `zlib` se adună la coadă în spatele lor. Mărește `UV_THREADPOOL_SIZE`, pune lookup-urile în cache sau folosește `dns.resolve`, care interoghează direct rețeaua.

### Ce sunt stream-urile și de ce le folosești?

Stream-urile mută datele în bucăți (chunk-uri) în loc să le încarce pe toate odată, așa că un fișier de 10 GB folosește la fel de multă memorie ca unul de 10 KB, iar procesarea începe de la prima bucată. Există patru tipuri: Readable, Writable, Duplex (ambele, ca un socket) și Transform (un Duplex care modifică datele, ca gzip).

### Ce este backpressure?

E ce se întâmplă când producătorul e mai rapid decât consumatorul. `write()` returnează `false` când bufferul intern depășește `highWaterMark`, iar tu ar trebui să te oprești din scris până la `'drain'`. Dacă ignori semnalul, bufferul crește până când procesul rămâne fără memorie. `pipe()` și `pipeline()` se ocupă de asta în locul tău.

### De ce să folosești `stream.pipeline` în loc de `.pipe()`?

`.pipe()` nu propagă erorile: dacă un stream eșuează, celelalte rămân deschise, iar descriptorii de fișiere sau socket-urile nu mai sunt eliberați (leak). `pipeline()` distruge toate stream-urile când oricare dintre ele eșuează și îți dă un singur callback, sau un singur promise din `stream/promises`, pentru succes sau eroare.

### Este `emitter.emit()` asincron?

Nu. `emit()` apelează sincron fiecare listener, în ordinea în care au fost adăugați, pe stiva de apeluri curentă, și revine doar după ce toți au terminat. Un listener lent blochează emitterul. Iar un eveniment `'error'` fără listener aruncă o excepție.

### Cum îți dai seama că event loop-ul e blocat?

Măsoară întârzierea: `perf_hooks.monitorEventLoopDelay()` îți dă o histogramă a întârzierilor buclei, iar `performance.eventLoopUtilization()` arată cât de ocupată e. Ca să găsești cauza, fă un profil CPU cu `--cpu-prof` sau cu inspectorul și caută frame-uri sincrone lungi în flame graph.

### De ce să preferi un `setTimeout` recursiv în locul lui `setInterval` pentru polling?

`setInterval` se declanșează după program, indiferent dacă rularea asincronă anterioară s-a terminat, așa că cererile lente se suprapun și se adună. Dacă programezi următorul `setTimeout` la finalul fiecărei rulări, garantezi o pauză între rulări, iar back-off-ul devine ușor de implementat.

### Cum își partajează datele worker thread-urile?

Fiecare worker are propriul isolate V8 și propriul event loop, deci implicit nu se partajează nimic. `postMessage` copiază datele cu algoritmul structured clone; dacă treci un `ArrayBuffer` în lista de obiecte transferabile, el este mutat în loc să fie copiat. Doar un `SharedArrayBuffer` este partajat cu adevărat, iar accesul la el îl coordonezi cu `Atomics`.

### `spawn`, `exec`, `execFile` sau `fork`?

`spawn` pornește un program și îi transmite ieșirea ca stream. `exec` rulează o comandă printr-un shell și ține ieșirea într-un buffer, așa că e expus la shell injection și limitat de `maxBuffer`. `execFile` este `exec` fără shell. `fork` pornește un alt proces Node cu un canal IPC pentru `send()` și `'message'`.

### Cum oprești controlat un server Node (graceful shutdown)?

La `SIGTERM`, apelează `server.close()` ca să nu mai accepți conexiuni noi și să lași cererile în curs să se termine; închide conexiunile keep-alive inactive (`closeIdleConnections()`); apoi închide pool-urile de conexiuni la baza de date și cozile, și ieși. Adaugă un timeout strict, ca o cerere blocată să nu poată ține procesul în viață la nesfârșit.

### La ce folosește `AsyncLocalStorage`?

Transportă context, cum ar fi ID-ul cererii sau utilizatorul curent, prin fiecare callback și `await` care decurge dintr-o cerere, fără să-l transmiți ca argument. Este echivalentul async al thread-local storage și așa etichetează loggerele și instrumentele de tracing tot ce se face pentru o cerere.

### Cum anulezi o operație asincronă?

Cu un `AbortController`. Transmiți proprietatea lui `signal` către `fetch`, `fs.readFile`, versiunile cu promise ale timerelor, `events.once` sau propriile tale funcții, apoi apelezi `abort()`. `AbortSignal.timeout(ms)` îți dă un semnal care se declanșează singur.

### De ce nu se termină scriptul meu Node?

Event loop-ul rulează cât timp ceva încă îl ține deschis: un timer, un socket sau un server deschis, un pool de conexiuni la baza de date, un proces copil. Închide ce ai deschis. Pentru un handle care n-ar trebui să țină singur procesul în viață, cum ar fi un interval de fundal, apelează `.unref()`.

### `Promise.all` rulează operațiile în paralel?

Nu rulează nimic: operațiile au pornit când ai creat promise-urile, iar `Promise.all` doar le așteaptă. Așteptarea e concurentă, iar promise-ul returnat e respins imediat ce unul dintre ele e respins, fără să le anuleze pe celelalte. Folosește `allSettled` ca să obții toate rezultatele, `any` pentru primul succes, `race` pentru primul care se finalizează și un limitator precum `p-limit` când ai mii de task-uri.

Ieșirile au fost verificate cu Node.js 22, rulând fișiere CommonJS. Începând cu libuv 1.45 (Node 20 și ulterior), pasul timerelor rulează tehnic la sfârșitul fiecărei iterații, după callback-urile de închidere (close); ordinea fazelor prezentată aici rămâne aceeași.
