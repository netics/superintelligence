---
title: "GIL-ul din Python explicat: thread-uri, procese, free-threading | Runtime lines"
description: "Patru thread-uri și un singur lock pe o cronologie live: muncă limitată de CPU versus muncă limitată de I/O, Python free-threaded, procese și un race condition (condiție de cursă) pe care îl poți parcurge pas cu pas."
url: https://superintelligence.ro/ro/gil
alternate_en: https://superintelligence.ro/gil.md
alternate_ro: https://superintelligence.ro/ro/gil.md
---

# GIL-ul din Python, pe o axă a timpului

Patru thread-uri, un singur Global Interpreter Lock. Alege o sarcină și un build Python, pornește simularea și urmărește cine ține lock-ul, ce fac nucleele CPU și cât durează toată treaba.

## GIL-ul nu îți face codul thread-safe

GIL-ul garantează că rulează o singură instrucțiune bytecode odată, nu că pașii tăi de citire, modificare și scriere rămân împreună. Parcurge pas cu pas două depuneri în același sold, cu și fără lock.

## Ce unealtă pentru ce treabă

### Așteptare după I/O

Apeluri de rețea, disc, baze de date, subprocese. GIL-ul e eliberat cât timp un thread așteaptă, așa că thread-urile se suprapun bine.
threading, asyncio

### Python pur, intensiv pe CPU

Bucle peste obiecte Python. Un singur GIL înseamnă un singur nucleu, așa că folosește procese separate sau un build free-threaded (`python3.14t`) cu cod thread-safe.
multiprocessing, ProcessPoolExecutor

### NumPy și extensii C

Multe extensii eliberează GIL-ul în timpul calculelor grele (NumPy, hashlib, zlib), așa că thread-urile obișnuite pot folosi mai multe nuclee.
thread-uri care apelează cod C

### Stare mutabilă partajată

Cu sau fără GIL, o citire urmată de o scriere se pot intercala. Protejează starea sau trimite mesaje în loc s-o partajezi.
Lock, queue.Queue

**Python free-threaded.** CPython 3.13 a adăugat un build experimental fără GIL, iar în 3.14 a devenit suportat oficial (PEP 779). Verifici cu `sys._is_gil_enabled()`; setarea `PYTHON_GIL=1` repornește lock-ul, iar importul unei extensii care nu e marcată ca sigură pentru acest mod reactivează automat GIL-ul.

## Întrebări de interviu: GIL-ul și concurența

Răspunsuri scurte pe care le poți spune cu voce tare. Încearcă să răspunzi singur la fiecare întrebare înainte s-o deschizi.

### Ce este GIL-ul?

Global Interpreter Lock este un mutex din CPython care lasă un singur thread să ruleze bytecode Python la un moment dat, în cadrul unui interpretor. Astfel, componentele interne ale interpretorului, cum ar fi numărul de referințe, rămân sigure fără lock-uri granulare.

### Atunci de ce să mai folosești thread-uri în Python?

Pentru că un thread eliberează GIL-ul cât timp așteaptă: I/O blocant pe socketuri și fișiere, precum și `time.sleep`, lasă alte thread-uri să ruleze. Multe extensii C, cum ar fi NumPy și `hashlib` pe date de intrare mari, îl eliberează și în timpul calculelor grele.

### Cum accelerezi cod Python limitat de CPU (CPU-bound)?

Folosește procese (`multiprocessing` sau `concurrent.futures.ProcessPoolExecutor`), ca fiecare worker să aibă propriul interpretor și propriul GIL, mută bucla critică în cod nativ care eliberează GIL-ul sau rulează pe build-ul free-threaded.

### Face GIL-ul codul meu thread-safe?

Nu. Thread-urile pot comuta între oricare două instrucțiuni bytecode, așa că `count += 1` (citire, adunare, scriere) se poate intercala și pierde actualizări; e exact race condition-ul (condiția de cursă) pe care îl poți parcurge pas cu pas pe această linie. Protejează starea partajată cu `threading.Lock` sau transmite datele între thread-uri prin `queue.Queue`.

### Cât de des comută thread-urile?

Un thread care așteaptă GIL-ul îl cere după intervalul de comutare, implicit 5 ms (`sys.getswitchinterval()`), iar thread-ul care îl deține îl eliberează la următorul punct sigur. Un thread care începe o operație I/O blocantă îl eliberează imediat.

### Ce este Python free-threaded?

Un build CPython separat, fără GIL (PEP 703), adăugat experimental în 3.13 ca `python3.13t` și suportat oficial din 3.14 (PEP 779). Thread-urile pot rula atunci cod Python pe mai multe nuclee simultan, cu un cost la viteza pe un singur thread. `sys._is_gil_enabled()` îți spune în ce mod ești.

### asyncio, thread-uri sau procese: cum alegi?

asyncio pentru multe task-uri I/O concurente, cu biblioteci async, pe un singur thread. Thread-uri pentru I/O cu biblioteci blocante sau pentru câteva task-uri în fundal. Procese pentru Python pur limitat de CPU, plătind timpul de pornire și serializarea (pickling) datelor între ele.

### Ce este efectul de convoi?

Un thread limitat de CPU ține GIL-ul câte un interval de comutare întreg, așa că thread-urile de I/O, care au nevoie de el doar o clipă după fiecare citire, stau la coadă în spatele lui. Latența lor crește, deși volumul total de lucru aproape nu se schimbă, cum arată sarcina mixtă de pe această linie.

### GIL-ul face parte din limbajul Python?

Nu, face parte din CPython, implementarea de referință. Jython și IronPython n-au avut niciodată GIL, PyPy are propriul GIL, iar din 3.13 CPython are un build free-threaded opțional, fără el. Limbajul spune doar ce înseamnă programul tău, nu cum sunt planificate thread-urile.

### De ce are CPython un GIL?

E o metodă simplă de a proteja componentele interne ale interpretorului: numărul de referințe, alocatorul și obiectele built-in pot fi actualizate fără un lock propriu. Asta păstrează rapid codul single-threaded și face extensiile C ușor de scris, cu prețul că un singur thread rulează bytecode Python la un moment dat.

### Când este eliberat GIL-ul?

În timpul I/O blocant (socketuri, fișiere, `time.sleep`) și în codul C care alege să-l elibereze, cum ar fi multe operații NumPy, `hashlib` pe date mari și `zlib`. Cât execută bytecode Python, thread-ul curent cedează GIL-ul și atunci când alt thread l-a așteptat un interval de comutare, implicit 5 ms.

### De ce a fost GIL-ul atât de greu de eliminat?

Fără el, fiecare modificare a numărului de referințe ar necesita o operație atomică sau un lock, ceea ce a încetinit codul single-threaded în încercările anterioare, iar multe extensii C se bazau tacit pe GIL pentru siguranță. PEP 703 a rezolvat asta cu biased reference counting, lock-uri per obiect și obiecte nemuritoare (immortal objects), și vine ca build opțional.

### Este `counter += 1` atomic?

Nu. Se compilează în mai mulți pași: citește valoarea, adună unu, o scrie înapoi, iar o comutare de thread între citire și scriere pierde o actualizare. Operațiile simple pe tipurile built-in, cum ar fi `list.append`, se întâmplă să fie atomice în CPython, dar nu te baza pe asta; protejează starea partajată cu un `Lock`.

### `Lock` sau `RLock`?

Un `Lock` intră în deadlock dacă thread-ul care îl deține încearcă să-l obțină din nou. Un `RLock` (lock reentrant) lasă thread-ul proprietar să-l obțină de mai multe ori și se eliberează după tot atâtea eliberări. Folosește `RLock` când o metodă care ține lock-ul apelează altă metodă cu lock a aceluiași obiect.

### Cum eviți deadlock-urile?

Obține lock-urile mereu în aceeași ordine globală, ține-le cât mai puțin, folosește `with` ca să fie eliberate întotdeauna și nu apela niciodată cod necunoscut, cum ar fi callback-uri, cât timp ții un lock. Un timeout la `acquire` transformă un blocaj tăcut într-o eroare vizibilă.

### Cum își transmit thread-urile date în siguranță?

Prin `queue.Queue`. Își gestionează singură lock-urile, blochează consumatorii până sosesc elemente și producătorii când e plină, și transformă starea partajată în mesaje. Pentru semnalizare, folosește `threading.Event`; ca să limitezi câte thread-uri folosesc o resursă, `Semaphore`.

### `ThreadPoolExecutor` sau `ProcessPoolExecutor`?

Au în comun API-ul `concurrent.futures`, deci alegerea ține de tipul de lucru. Thread-uri pentru task-uri limitate de I/O: pornesc ieftin și partajează memoria. Procese pentru task-uri limitate de CPU: ocolesc GIL-ul, dar funcția și argumentele ei trebuie să poată fi serializate cu pickle, iar fiecare apel plătește trimiterea datelor către alt proces.

### Ce costă `multiprocessing`?

Pornirea proceselor, serializarea cu pickle a fiecărui argument și rezultat ca să treacă dintr-un proces în altul, plus o copie separată a interpretorului și a datelor în fiecare proces. Modul de pornire depinde de platformă: `spawn` pe Windows și macOS, `forkserver` pe Linux din 3.14 (înainte, `fork`).

### De ce e periculos să faci fork unui proces care are thread-uri?

Procesul copil primește o copie a memoriei, dar doar thread-ul care a apelat `fork`. Un lock ținut în acel moment de orice alt thread rămâne blocat pentru totdeauna în copil, așa că acesta se poate bloca la primul apel de logging sau la prima alocare. Python 3.12 și versiunile ulterioare avertizează despre asta; preferă `spawn` sau `forkserver`.

### Cum partajezi date între procese?

Trimite mesaje printr-un `multiprocessing.Queue` sau `Pipe`; datele sunt serializate cu pickle și copiate. Pentru array-uri mari, folosește `multiprocessing.shared_memory`, care dă fiecărui proces aceiași octeți, fără copiere. Un `Manager` partajează obiecte Python printr-un proces server, ceea ce e comod, dar lent.

### Rulează asyncio cod în paralel?

Nu. Rulează un singur thread, iar task-urile își dau rândul la fiecare `await`. Așa gestionează ieftin mii de conexiuni care așteaptă, dar un singur apel blocant, cum ar fi `time.sleep` sau `requests.get`, îngheață toate task-urile. Mută lucrul blocant în afara event loop-ului cu `asyncio.to_thread` sau `run_in_executor`.

### Care e diferența dintre concurență și paralelism?

Concurența înseamnă să te ocupi de mai multe lucruri deodată: task-urile avansează pe rând. Paralelismul înseamnă să faci mai multe lucruri deodată: task-urile rulează în același moment pe nuclee diferite. Thread-urile sub GIL și asyncio îți dau concurență; procesele și Python free-threaded îți dau paralelism.

### Pot thread-urile să accelereze cod NumPy?

Adesea, da. NumPy eliberează GIL-ul în multe operații pe array-uri mari, așa că mai multe thread-uri le pot rula pe nuclee diferite. Liniile Python dintre aceste apeluri tot își așteaptă rândul, așa că câștigul depinde de cât din timp se petrece în NumPy.

### Ce sunt subinterpretoarele?

Mai multe interpretoare Python izolate în același proces. Din 3.12 fiecare poate avea propriul GIL (PEP 684), iar 3.14 adaugă modulul `concurrent.interpreters` și `InterpreterPoolExecutor`. Obții paralelism cu overhead mai mic decât la procese, dar obiectele nu sunt partajate; datele se transmit între interpretoare.

### Cum verifici dacă GIL-ul este activ?

Apelează `sys._is_gil_enabled()` (3.13 sau mai nou). Un build free-threaded, de obicei numit `python3.13t` sau `python3.14t`, rulează fără el, dar reactivează GIL-ul când importă o extensie C care nu e marcată ca sigură, dacă nu îl forțezi să rămână oprit cu `PYTHON_GIL=0` sau `-X gil=0`.

### Python free-threaded îmi face codul thread-safe?

Nu. Obiectele built-in își pun intern lock-uri, deci o listă nu se va corupe, dar `counter += 1` și codul de tip check-then-act (verifici, apoi acționezi) au race condition exact ca înainte, doar mai des, pentru că acum thread-urile rulează cu adevărat simultan. Tot ai nevoie de lock-uri, iar codul single-threaded rulează ceva mai lent în acest build.

### `threading.local` sau `contextvars`?

`threading.local()` dă fiecărui thread propria copie a unor atribute, cum ar fi o conexiune la baza de date. `contextvars` face același lucru pentru task-urile asyncio, care împart un singur thread, și funcționează și cu thread-uri. Pentru date legate de un request în cod async, folosește `contextvars`.

### Cum oprești un thread care rulează?

Nu îl poți omorî din afară. Dă-i un `threading.Event` și pune-l să verifice regulat evenimentul și să iasă. Un thread daemon (`daemon=True`) nu împiedică interpretorul să se închidă, dar e omorât fără curățenie, așa că fișierele deschise și tranzacțiile pot rămâne la jumătate.

Simulatorul este un model simplificat al GIL-ului din CPython: un thread care așteaptă cere o comutare după un interval (implicit 5 ms), thread-ul care îl deține eliberează lock-ul, iar cei care așteaptă sunt serviți în ordinea sosirii. Rulările reale adaugă zgomot de la sistemul de operare, așa că formele sunt corecte, iar cifrele sunt orientative. Rulările free-threaded adaugă un overhead de 7% per thread; pornirea unui proces apare ca 10 ms.
