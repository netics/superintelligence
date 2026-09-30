---
title: "Runtime lines: how Node.js and Python actually run your code"
description: "An interactive, visual reference for full-stack engineers preparing for interviews: the Node.js event loop, Python memory and the GIL, and the JavaScript and Python type systems, step by step, with interview questions for each."
url: https://superintelligence.ro/
alternate_en: https://superintelligence.ro/index.md
alternate_ro: https://superintelligence.ro/ro/index.md
---

An interactive reference for full-stack interviews

# How Node.js and Python actually run your code

Five explorers, drawn as lines on a transit map. Step through real programs one line at a time and watch the call stack, the heap, the GIL and the type system move. Every output was checked against real Node.js and CPython, and every line ends with the interview questions it prepares you for.
[Start with the event loop](https://superintelligence.ro/node)

## NNode event loop

How one thread juggles thousands of tasks: the call stack, the nextTick and promise queues, timers, the libuv phases and the thread pool.
You’ll be ready for
- Does a promise callback run before `setTimeout(fn, 0)`?
- `setImmediate` or `setTimeout`: which fires first?
- What blocks the event loop, and how do you fix it?
[Open the line](https://superintelligence.ro/node) [Interview questions](https://superintelligence.ro/node#n-ref)

## MPython memory

Names, objects and reference counts, how the cycle collector frees what refcounting can’t, and why pymalloc keeps memory after you delete things.
You’ll be ready for
- Is Python pass-by-value or pass-by-reference?
- What’s the difference between `is` and `==`?
- Why doesn’t memory drop after `del`?
[Open the line](https://superintelligence.ro/memory) [Interview questions](https://superintelligence.ro/memory#m-ref)

## GThe GIL

Four threads and one lock on a live timeline: CPU-bound versus I/O-bound work, free-threaded Python, processes, and a race condition you can step through.
You’ll be ready for
- Do threads make Python code faster?
- Does the GIL make my code thread-safe?
- Threads, processes or asyncio: how do you choose?
[Open the line](https://superintelligence.ro/gil) [Interview questions](https://superintelligence.ro/gil#g-ref)

## JJavaScript types

The `typeof` junction, how V8 stores each type, copies versus references, the exact `==` algorithm, truthiness and the 64 bits inside a number.
You’ll be ready for
- Why is `[] == false` true?
- Shallow copy or deep copy?
- Why is `0.1 + 0.2 !== 0.3`?
[Open the line](https://superintelligence.ro/js-types) [Interview questions](https://superintelligence.ro/js-types#j-ref)

## PPython types

The built-in types and where to use each one, how `a + b` is dispatched, when `+=` changes things in place, and how dict keys are hashed.
You’ll be ready for
- What makes an object hashable?
- What happens when Python evaluates `a + b`?
- What’s wrong with `def f(items=[])`?
[Open the line](https://superintelligence.ro/py-types) [Interview questions](https://superintelligence.ro/py-types#p-ref)

### Step through it

**Play**, **Next** and **Back** move one line of code at a time. Use ← and → to step, Space to play, and pick a speed that suits you.

### Outputs you can trust

Every printed output was checked against Node.js 22 and CPython 3.12. The JavaScript passes ESLint and the Python is formatted with black.

### Built for revision

Each line ends with interview questions and short answers you can say out loud. Link straight to a line with `#node`, `#memory`, `#gil`, `#js-types` or `#py-types`.
