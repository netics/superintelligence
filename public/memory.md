---
title: "Python memory management explained: references, GC, pymalloc | Runtime lines"
description: "Names, objects and reference counts, how the cycle collector frees what refcounting can’t, and why pymalloc keeps memory after you delete things."
url: https://superintelligence.ro/memory
alternate_en: https://superintelligence.ro/memory.md
alternate_ro: https://superintelligence.ro/ro/memory.md
---

# Python memory, drawn as a map

Names on the left, objects on the heap to the right, and every arrow is a reference. Step through four short programs to see when objects are shared, counted, and freed, then play with the allocator that stores them.

## Where small objects actually live

CPython doesn’t ask the operating system for memory every time you create an object. Objects of 512 bytes or less come from **pymalloc**: big **arenas** split into **pools**, and each pool hands out fixed-size blocks for one size class (multiples of 16 bytes). Allocate and free some objects and watch what happens to the arenas.

Scaled down for the screen: a real pool holds hundreds of blocks and a real arena holds many pools. Sizes are `sys.getsizeof()` on 64-bit CPython 3.12, rounded up to the next 16-byte size class.

## What to remember

**Names are references**Assignment, argument passing and `return` copy references, never objects. Mutations are visible through every name.
**Counting frees most objects**When an object’s count reaches 0 it is freed on the spot, deterministically. `del` only removes a name.
**The GC is for cycles**Objects that refer to each other keep their counts above 0. The cyclic collector finds and frees them.
**Freed isn’t returned**Freed blocks go back to pymalloc, not the OS. An arena is only released when every pool in it is empty.

## Interview questions: Python memory

Short answers you can say out loud. Try answering each question yourself before you open it.

### What happens in memory for `a = [1, 2]` followed by `b = a`?

One list object is created on the heap and both names refer to it. Assignment never copies: it binds a name to an object, and the list’s reference count goes to 2.

### Is Python pass-by-value or pass-by-reference?

Neither. It passes references to objects by value, often called call by sharing. A function can mutate an object you pass in and you’ll see the change, but rebinding the parameter inside the function doesn’t touch your variable.

### How does CPython free memory?

Mainly by reference counting: when an object’s count drops to zero it’s freed immediately. A generational cyclic garbage collector finds groups of objects that only reference each other, which refcounting alone can never free.

### What’s the difference between `is` and `==`?

`is` checks identity: are these the same object? `==` checks equality through `__eq__`. Use `is` for singletons like `None`, and `==` for everything else.

### Why can `x is y` be True for two equal small ints but not for big ones?

CPython caches the integers from -5 to 256, so those are always the same objects. Whether other equal numbers or strings share an object depends on interning and constant folding, an implementation detail you should never rely on.

### Does `del x` free the object?

Not directly. `del` removes a name (or a container item) and decrements the reference count. The object is freed only when its count reaches zero, or later by the garbage collector if it’s part of a cycle.

### Why doesn’t my process shrink after I delete a big list?

Small objects come from pymalloc, which takes memory from the OS in large arenas and can only give an arena back when every block in it is free. A few surviving objects keep whole arenas alive, as the pymalloc demo on this line shows. Python reuses that memory; it just doesn’t hand it back.

### How do you track down a memory leak in Python?

Look for references that live too long: module-level caches, an unbounded `functools.lru_cache`, closures and callbacks that capture big objects, and globals. `tracemalloc` shows which lines allocated the memory that stays, and `gc.get_referrers()` shows who is holding an object.

### When would you use `weakref`?

For caches and back-references that shouldn’t keep an object alive. A weak reference doesn’t increase the reference count, so the object can still be freed, after which the weak reference returns `None`.

### What is a reference count, and how do you see it?

Every CPython object has a counter of how many references point at it: names, list slots, dict values, attributes. Binding a name adds one, dropping it subtracts one, and at zero the object is freed immediately. `sys.getrefcount(x)` shows it, one higher than you expect because the call itself holds a reference.

### What are immortal objects?

Since Python 3.12 (PEP 683), objects such as `None`, `True`, `False`, small ints and many interned strings have a fixed reference count that never changes and are never freed. Skipping those counter writes saves work, keeps memory pages shared after `fork`, and makes sharing them between threads and interpreters safe.

### Why does Python need a garbage collector if it has reference counting?

Reference counting can’t free cycles. If a list contains itself, or two objects point at each other, their counts never reach zero even when nothing else can reach them. The cycle collector finds such groups by subtracting the references they hold to each other and frees the ones left with no outside references.

### What are GC generations?

The collector sorts container objects by age. New objects start in the youngest generation, which is scanned often because most objects die young; survivors are promoted to older generations that are scanned less and less often. Thresholds from `gc.get_threshold()` decide when each one runs.

### Should you call `gc.collect()` or `gc.disable()`?

Rarely. Reference counting frees almost everything, and the collector already runs on its own. Disabling it is safe only if your code never creates cycles, otherwise those leak. The one common tuning is `gc.freeze()` before forking workers, so the collector doesn’t touch, and copy, pages the children share.

### What is `__del__`, and why be careful with it?

It’s a finalizer that runs when an object is about to be freed. When that happens depends on reference counts, cycles and the Python implementation, so it’s a bad place for closing files or connections, and exceptions raised in it are only printed. Use a context manager (`with`) or `weakref.finalize` instead.

### What is pymalloc?

CPython’s allocator for small objects, 512 bytes or less. It takes big arenas from the OS, splits them into pools, and each pool hands out blocks of one size class. Creating and freeing small objects then costs almost nothing, because most requests never reach the system allocator.

### Why does `sys.getsizeof` give the wrong size for a list?

It only measures the object itself. For a list that is the header plus the array of pointers, not the objects they point at. A list of a thousand strings reports a few kilobytes however long the strings are. To measure the whole structure, walk it, or compare `tracemalloc` snapshots before and after.

### What does `__slots__` do for memory?

It replaces the per-instance `__dict__` with fixed slots in the object itself. Each instance gets smaller and attribute access slightly faster, which matters when you create millions of them. The cost: you can’t add attributes that aren’t listed, and you need a `__weakref__` slot for weak references.

### What is string interning?

Keeping a single copy of equal strings. CPython interns identifiers and many short literals automatically, and you can intern others with `sys.intern()`, which saves memory and makes dict lookups on repeated keys faster. It’s an optimisation, not a rule, so always compare strings with `==`, never `is`.

### Why do forked workers use more memory over time, even if they only read data?

After `fork`, parent and child share memory pages until one of them writes to a page. In CPython, simply reading an object changes its reference count, which is a write, so shared pages are copied one by one. Immortal objects and `gc.freeze()` reduce this.

### How is a list stored, and why is `append` fast?

A list is a resizable array of pointers to objects stored elsewhere. When it’s full, CPython allocates a bigger array with spare room, so most appends just fill a free slot and the occasional copy averages out: amortised O(1). Inserting or deleting at the front is O(n), because every pointer after it moves.

### Why does a list of a million ints use so much memory?

Each element is a pointer (8 bytes) to a full int object (28 bytes or more) with its own header. `array.array('q')` or a NumPy array stores the raw 8-byte values next to each other instead, several times smaller and much faster to loop over in C.

### How do generators save memory?

A generator produces values one at a time and keeps only its paused frame between them. `sum(x * x for x in range(10**8))` needs constant memory, while the list comprehension version builds a list of a hundred million ints first. The catch: a generator can only be consumed once.

### What is a `memoryview`?

A view on the memory of another object that supports the buffer protocol, such as `bytes`, `bytearray` or `array`. Slicing a `memoryview` doesn’t copy, so parsing a large binary buffer piece by piece stays fast and uses no extra memory.

### How can a closure keep a large object alive?

A nested function keeps every variable it uses from the enclosing scope in a cell. As long as the function exists, for example stored as a callback, those objects can’t be freed, even if you only needed one small value from a huge one. Copy out what you need before defining the function.

### How can an exception cause a memory leak?

A traceback references every frame it passed through, and every frame references its local variables. Storing an exception, for example in a list of errors, keeps all of those locals alive. That’s why Python deletes the name after `except E as e:`; store `str(e)` if you only need the message.

### What does `functools.lru_cache` do to memory?

It keeps a reference to every argument and result it stores. With `maxsize=None`, or `@cache`, it grows forever. On a method it also stores `self`, which keeps every instance alive. Give it a bounded size, and cache functions rather than methods.

### What does `id()` return?

An integer that is unique to an object for as long as it’s alive. In CPython it’s the memory address. Once an object is freed, a new object can get the same address, so two different objects created one after the other can report the same `id`.

### How does reference counting work in free-threaded Python?

Without the GIL, counter updates from different threads would race. Free-threaded builds use **biased reference counting**: the thread that owns an object updates a local count without atomics, and other threads update a shared count atomically. Some objects use deferred counting, and memory comes from mimalloc instead of pymalloc.

Counts on the map include only references created by the program. `sys.getrefcount()` reports one more (its own argument), and immortal objects report a huge fixed value.
