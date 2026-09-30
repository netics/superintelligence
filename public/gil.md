---
title: "Python's GIL explained: threads, processes, free-threading | Runtime lines"
description: "Four threads and one lock on a live timeline: CPU-bound versus I/O-bound work, free-threaded Python, processes, and a race condition you can step through."
url: https://superintelligence.ro/gil
alternate_en: https://superintelligence.ro/gil.md
alternate_ro: https://superintelligence.ro/ro/gil.md
---

# Python’s GIL, on a timeline

Four threads, one Global Interpreter Lock. Pick a workload and a Python build, press Run, and watch who holds the lock, what the CPU cores are doing, and how long the whole job takes.

## The GIL doesn’t make your code thread-safe

The GIL guarantees that one bytecode instruction runs at a time, not that your read, modify and write steps stay together. Step through two deposits into one balance, with and without a lock.

## Which tool for which job

### Waiting on I/O

Network calls, disk, databases, subprocesses. The GIL is released while a thread waits, so threads overlap well.
threading, asyncio

### CPU-heavy pure Python

Loops over Python objects. One GIL means one core, so use separate processes, or a free-threaded build (`python3.14t`) with thread-safe code.
multiprocessing, ProcessPoolExecutor

### NumPy and C extensions

Many extensions release the GIL during heavy work (NumPy, hashlib, zlib), so plain threads can use several cores.
threads around C-level work

### Shared mutable state

With or without a GIL, a read followed by a write can interleave. Protect it, or pass messages instead of sharing.
Lock, queue.Queue

**Free-threaded Python.** CPython 3.13 added an experimental build without the GIL, and in 3.14 it became officially supported (PEP 779). Check with `sys._is_gil_enabled()`; setting `PYTHON_GIL=1` turns the lock back on, and importing an extension that isn’t marked safe for it re-enables the GIL automatically.

## Interview questions: the GIL and concurrency

Short answers you can say out loud. Try answering each question yourself before you open it.

### What is the GIL?

The Global Interpreter Lock is a mutex in CPython that lets only one thread run Python bytecode at a time within an interpreter. It keeps the interpreter’s internals, such as reference counts, safe without fine-grained locking.

### Then why use threads in Python at all?

Because a thread releases the GIL while it waits: blocking I/O on sockets and files, and `time.sleep`, let other threads run. Many C extensions, such as NumPy and `hashlib` on large inputs, release it during heavy computation too.

### How do you speed up CPU-bound Python code?

Use processes (`multiprocessing` or `concurrent.futures.ProcessPoolExecutor`) so each worker has its own interpreter and GIL, move the hot loop into native code that releases the GIL, or run on the free-threaded build.

### Does the GIL make my code thread-safe?

No. Threads can switch between any two bytecodes, so `count += 1` (load, add, store) can interleave and lose updates, which is the race you can step through on this line. Protect shared state with `threading.Lock`, or pass data between threads with `queue.Queue`.

### How often do threads switch?

A thread waiting for the GIL asks for it after the switch interval, 5 ms by default (`sys.getswitchinterval()`), and the holder releases it at the next safe point. A thread that starts blocking I/O releases it straight away.

### What is free-threaded Python?

A separate CPython build without the GIL (PEP 703), added experimentally in 3.13 as `python3.13t` and officially supported from 3.14 (PEP 779). Threads can then run Python code on several cores at once, at some cost to single-threaded speed. `sys._is_gil_enabled()` tells you which mode you’re in.

### asyncio, threads or processes: how do you choose?

asyncio for many concurrent I/O tasks with async libraries on a single thread. Threads for I/O with blocking libraries, or a handful of background tasks. Processes for CPU-bound pure Python, paying for start-up time and for pickling data between them.

### What is the convoy effect?

A CPU-bound thread keeps the GIL for a whole switch interval at a time, so I/O threads that only need it for a moment after each read queue up behind it. Their latency grows even though the total work barely changes, as the Mixed workload on this line shows.

### Is the GIL part of the Python language?

No, it’s part of CPython, the reference implementation. Jython and IronPython never had one, PyPy has its own, and since 3.13 CPython has an optional free-threaded build without it. The language only says what your program means, not how threads are scheduled.

### Why does CPython have a GIL at all?

It’s a simple way to keep the interpreter’s internals safe: reference counts, the allocator and built-in objects can be updated without a lock of their own. That keeps single-threaded code fast and makes C extensions easy to write, at the price of only one thread running Python bytecode at a time.

### When is the GIL released?

During blocking I/O (sockets, files, `time.sleep`), and inside C code that chooses to release it, such as many NumPy operations, `hashlib` on large inputs and `zlib`. While executing Python bytecode, the running thread also gives it up when another thread has waited for the switch interval, 5 ms by default.

### Why was the GIL so hard to remove?

Without it, every reference count change would need an atomic operation or a lock, which slowed single-threaded code in earlier attempts, and many C extensions quietly relied on the GIL for safety. PEP 703 solved this with biased reference counting, per-object locks and immortal objects, and ships as an opt-in build.

### Is `counter += 1` atomic?

No. It compiles to several steps: load the value, add one, store it back, and a thread switch between the load and the store loses an update. Single operations on built-ins, such as `list.append`, happen to be atomic in CPython, but don’t rely on it; protect shared state with a `Lock`.

### `Lock` or `RLock`?

A `Lock` deadlocks if the thread holding it tries to acquire it again. An `RLock` (reentrant lock) lets the owning thread acquire it several times, and it’s released after the same number of releases. Use `RLock` when a locked method calls another locked method of the same object.

### How do you avoid deadlocks?

Always acquire locks in the same global order, hold them for as short a time as possible, use `with` so they’re always released, and never call unknown code, such as callbacks, while holding one. A timeout on `acquire` turns a silent hang into an error you can see.

### How do threads pass data to each other safely?

Through `queue.Queue`. It does its own locking, blocks consumers until items arrive and producers when it’s full, and turns shared state into messages. For signalling, use `threading.Event`; to limit how many threads use a resource, `Semaphore`.

### `ThreadPoolExecutor` or `ProcessPoolExecutor`?

They share the `concurrent.futures` API, so the choice is about the work. Threads for I/O-bound tasks: cheap to start, share memory. Processes for CPU-bound tasks: they get around the GIL, but the function and its arguments must be picklable, and each call pays to send data to another process.

### What does `multiprocessing` cost?

Starting processes, pickling every argument and result to move it between them, and a separate copy of the interpreter and data in each one. How processes start depends on the platform: `spawn` on Windows and macOS, `forkserver` on Linux since 3.14 (before that, `fork`).

### Why is it dangerous to fork a process that has threads?

The child gets a copy of memory, but only the thread that called `fork`. A lock held by any other thread at that moment stays locked forever in the child, so the child can hang on its first log call or allocation. Python 3.12 and later warn about it; prefer `spawn` or `forkserver`.

### How do you share data between processes?

Send messages through a `multiprocessing.Queue` or `Pipe`; the data is pickled and copied. For large arrays, use `multiprocessing.shared_memory`, which gives every process the same bytes without copying. A `Manager` shares Python objects through a server process, which is convenient but slow.

### Does asyncio run code in parallel?

No. It runs one thread, and tasks take turns at each `await`. That handles thousands of waiting connections cheaply, but a single blocking call such as `time.sleep` or `requests.get` freezes every task. Move blocking work off the loop with `asyncio.to_thread` or `run_in_executor`.

### What is the difference between concurrency and parallelism?

Concurrency is dealing with many things at once: tasks make progress by taking turns. Parallelism is doing many things at once: tasks run at the same moment on different cores. Threads under the GIL and asyncio give you concurrency; processes, and free-threaded Python, give you parallelism.

### Can threads speed up NumPy code?

Often, yes. NumPy releases the GIL inside many operations on large arrays, so several threads can run them on different cores. The Python lines between those calls still take turns, so the win depends on how much of the time is spent inside NumPy.

### What are subinterpreters?

Several isolated Python interpreters in one process. Since 3.12 each can have its own GIL (PEP 684), and 3.14 adds the `concurrent.interpreters` module and `InterpreterPoolExecutor`. You get parallelism with less overhead than processes, but objects aren’t shared; data is passed between interpreters.

### How do you check whether the GIL is enabled?

Call `sys._is_gil_enabled()` (3.13 and later). A free-threaded build, usually named `python3.13t` or `python3.14t`, runs without it, but it turns the GIL back on when it imports a C extension that isn’t marked safe, unless you force it off with `PYTHON_GIL=0` or `-X gil=0`.

### Does free-threaded Python make my code thread-safe?

No. Built-in objects lock themselves internally, so a list won’t be corrupted, but `counter += 1` and check-then-act code race exactly as before, only more often, because threads now really run at the same time. You still need locks, and single-threaded code runs somewhat slower in that build.

### `threading.local` or `contextvars`?

`threading.local()` gives every thread its own copy of some attributes, such as a database connection. `contextvars` does the same for asyncio tasks, which share one thread, and also works with threads. For request-scoped data in async code, use `contextvars`.

### How do you stop a running thread?

You can’t kill one from outside. Give it a `threading.Event` and have it check the event regularly and return. A daemon thread (`daemon=True`) doesn’t stop the interpreter from exiting, but it’s killed without cleanup, so open files and transactions may be left half done.

The simulator is a simplified model of CPython’s GIL: a waiting thread asks for a switch after one interval (5 ms by default), the holder drops the lock, and waiters are served first come, first served. Real runs add operating-system noise, so the shapes are right and the numbers are illustrative. Free-threaded runs add 7% per-thread overhead; process start-up is shown as 10 ms.
