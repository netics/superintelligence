---
title: "The Node.js event loop explained, step by step | Runtime lines"
description: "How one thread juggles thousands of tasks: the call stack, the nextTick and promise queues, timers, the libuv phases and the thread pool."
url: https://superintelligence.ro/node
alternate_en: https://superintelligence.ro/node.md
alternate_ro: https://superintelligence.ro/ro/node.md
---

# The Node.js event loop, one stop at a time

Pick a scenario on the line below, then press Play or step with the arrow keys. Every callback travels from your code through Node’s queues onto the call stack, so you can see exactly why the output lands in that order.

## The rules behind every run

Every scenario above follows the same five rules, in this order.

- **Run the script to the end:** Synchronous code always finishes first. Nothing interrupts it: not timers, not I/O.
- **Drain the microtasks:** All `process.nextTick` callbacks, then all promise callbacks. Repeat until both queues are empty.
- **Go round the loop:** timers, pending callbacks, idle/prepare, poll, check, close callbacks. Each phase runs the callbacks waiting in its queue.
- **Drain microtasks after every callback:** Since Node 11, a promise or nextTick created inside a callback runs before the next callback of the same phase.
- **Wait, or exit:** Poll blocks while I/O is still pending. When no timers, handles or requests are left, the process exits.

**ES modules are different.** In an `.mjs` file, or with `"type": "module"`, the top level already runs inside a promise job, so promise callbacks run before `nextTick`. The classic example prints **A E C D B** there.

## Where each API sends its callback

Use this as a route map when you read unfamiliar async code: find the API, and you know which queue its callback waits in.

## Interview questions: the Node.js event loop

Short answers you can say out loud. Try answering each question yourself before you open it.

### Node is single-threaded. How does it handle thousands of connections?

Your JavaScript runs on one thread, but the waiting doesn’t. Node hands network I/O to the operating system (epoll, kqueue, IOCP) and file-system work to libuv’s thread pool, then runs your callback on the main thread when the result is ready. The main thread never waits; it only runs callbacks.

### What exactly is the event loop?

A loop inside libuv that cycles through phases: timers, pending callbacks, poll (I/O), check (`setImmediate`) and close callbacks. Each phase has a queue, and each callback runs to completion on the call stack before the next one starts.

### In what order do synchronous code, `process.nextTick`, promises and timers run?

Synchronous code first. Then the whole `nextTick` queue, then the whole promise microtask queue. Only then does the loop move on to `setTimeout` callbacks in the timers phase and `setImmediate` in the check phase. Both microtask queues are drained again after every single callback.

### Why do promises run before `process.nextTick` in an ES module?

Node starts an ES module from inside a promise job, so when its top-level code finishes, V8 is still draining the microtask queue and runs the promise callbacks you queued before Node gets to the `nextTick` queue. In CommonJS the `nextTick` queue goes first. The examples on this line are CommonJS: run scenario 1 as an `.mjs` file and C and D swap places.

### `setTimeout(fn, 0)` or `setImmediate(fn)`: which runs first?

From the main module it isn’t guaranteed; it depends on how quickly the loop starts. Inside an I/O callback, `setImmediate` always wins, because the check phase comes straight after the poll phase.

### What does the libuv thread pool do, and how big is it?

It runs work that has no non-blocking OS API: most `fs` calls, `dns.lookup`, and CPU-heavy `crypto` and `zlib` functions. It has 4 threads by default, set by `UV_THREADPOOL_SIZE`. Network sockets don’t use it.

### What blocks the event loop, and how do you fix it?

Any long synchronous work: a huge `JSON.parse`, sync `fs` or `crypto` calls, heavy loops, a regex with catastrophic backtracking. While it runs, no request, timer or promise can move. Split the work into chunks, stream the data, or move it to `worker_threads`.

### Why did my 10 ms timer fire after 100 ms?

A timer’s delay is a minimum, not a promise. The callback runs in the first timers phase after the delay has passed, so a long callback ahead of it delays it, exactly like the `loop done at 100 ms` scenario on this line.

### Can `process.nextTick` starve the event loop?

Yes. The `nextTick` queue is drained completely before the loop continues, so a callback that keeps scheduling another `nextTick` stops all I/O. `setImmediate` yields to I/O instead.

### When would you use `worker_threads`, and when `cluster`?

`worker_threads` run JavaScript in parallel inside one process and can share memory with `SharedArrayBuffer`; use them for CPU-heavy tasks. `cluster`, or several processes behind a load balancer, runs separate Node processes so a server can use every core.

### What is the difference between microtasks and macrotasks?

Macrotasks are the callbacks the loop picks up phase by phase: timers, I/O callbacks, `setImmediate`, close events. Microtasks are promise reactions and `queueMicrotask` callbacks, plus Node’s own `nextTick` queue. After every single macrotask callback, Node drains both microtask queues completely before it runs the next one.

### How is `queueMicrotask` different from `process.nextTick`?

`queueMicrotask` puts a callback on V8’s microtask queue, the same queue promise callbacks use. `process.nextTick` uses a separate Node queue that, in CommonJS, runs before it. Prefer `queueMicrotask`: it works the same in browsers and Node, and it can’t jump ahead of promises you already queued.

### What happens in the poll phase?

The loop asks the OS for finished I/O and runs those callbacks. If there is nothing to run, it waits there for new I/O, but only until the nearest timer is due. If a `setImmediate` is queued, it doesn’t wait at all and moves straight on to the check phase.

### How does `async`/`await` map onto the event loop?

An `async` function runs synchronously up to its first `await`. There it returns a pending promise to its caller, and the rest of the function is resumed later as a microtask once the awaited value settles. Nothing runs in parallel: `await` just splits your function into callbacks.

### What happens to an unhandled promise rejection or an uncaught exception?

Since Node 15, an unhandled rejection emits `unhandledRejection`, and if nothing handles it, it is thrown as an uncaught exception and the process exits with an error. In an `uncaughtException` handler, log and exit: the process is in an unknown state, so let a supervisor restart it instead of carrying on.

### Does `fs.promises` avoid the thread pool?

No. The promise, callback and sync versions of `fs` do the same work; the async ones run it on libuv’s thread pool and only differ in how you get the result. Network I/O, including `fetch` and `http`, is the part that goes to the OS without the pool.

### Why can slow DNS make file reads slow?

`dns.lookup`, which `http` and `net` use by default, calls `getaddrinfo` on the thread pool. With only 4 threads, a few slow lookups can occupy the whole pool and `fs`, `crypto` and `zlib` work queues up behind them. Raise `UV_THREADPOOL_SIZE`, cache lookups, or use `dns.resolve`, which queries the network directly.

### What are streams, and why use them?

Streams move data in chunks instead of loading it all at once, so a 10 GB file uses the same memory as a 10 KB one, and processing starts with the first chunk. There are four kinds: Readable, Writable, Duplex (both, like a socket) and Transform (a Duplex that changes the data, like gzip).

### What is backpressure?

It is what happens when the producer is faster than the consumer. `write()` returns `false` once the internal buffer passes `highWaterMark`, and you should stop writing until `'drain'`. Ignore it and the buffer grows until the process runs out of memory. `pipe()` and `pipeline()` handle it for you.

### Why use `stream.pipeline` instead of `.pipe()`?

`.pipe()` doesn’t forward errors: if one stream fails, the others stay open and leak file descriptors or sockets. `pipeline()` destroys every stream when any of them fails and gives you one callback, or one promise from `stream/promises`, for success or error.

### Is `emitter.emit()` asynchronous?

No. `emit()` calls every listener synchronously, in the order they were added, on the current call stack, and returns only when all of them have finished. A slow listener blocks the emitter. And an `'error'` event with no listener throws.

### How do you find out that the event loop is blocked?

Measure the delay: `perf_hooks.monitorEventLoopDelay()` gives a histogram of how late the loop is, and `performance.eventLoopUtilization()` shows how busy it is. To find the cause, take a CPU profile with `--cpu-prof` or the inspector and look for long synchronous frames in the flame graph.

### Why prefer a recursive `setTimeout` over `setInterval` for polling?

`setInterval` fires on schedule whether or not the previous async run has finished, so slow requests overlap and pile up. Scheduling the next `setTimeout` at the end of each run guarantees a gap between runs and makes back-off easy.

### How do worker threads share data?

Each worker has its own V8 isolate and event loop, so nothing is shared by default. `postMessage` copies data with the structured clone algorithm; listing an `ArrayBuffer` as transferable moves it instead of copying. Only a `SharedArrayBuffer` is truly shared, and you coordinate access to it with `Atomics`.

### `spawn`, `exec`, `execFile` or `fork`?

`spawn` starts a program and streams its output. `exec` runs a command through a shell and buffers the output, so it’s open to shell injection and limited by `maxBuffer`. `execFile` is `exec` without the shell. `fork` starts another Node process with an IPC channel for `send()` and `'message'`.

### How do you shut down a Node server gracefully?

On `SIGTERM`, call `server.close()` to stop accepting connections and let in-flight requests finish; close idle keep-alive connections (`closeIdleConnections()`); then close database pools and queues, and exit. Add a hard timeout so a stuck request can’t hold the process forever.

### What is `AsyncLocalStorage` for?

It carries context, such as a request ID or the current user, through every callback and `await` that follows from a request, without passing it as an argument. It is the async equivalent of thread-local storage, and it is how loggers and tracing tools tag everything done for one request.

### How do you cancel an async operation?

With an `AbortController`. Pass its `signal` to `fetch`, `fs.readFile`, the promise versions of the timers, `events.once` or your own functions, then call `abort()`. `AbortSignal.timeout(ms)` gives you a signal that aborts on its own.

### Why doesn’t my Node script exit?

The loop keeps running while anything still holds it open: a timer, an open socket or server, a database pool, a child process. Close what you opened. For a handle that shouldn’t keep the process alive on its own, such as a background interval, call `.unref()`.

### Does `Promise.all` run things in parallel?

It runs nothing: the operations started when you created the promises, and `Promise.all` only waits for them. They wait concurrently, and it rejects as soon as one rejects, without cancelling the others. Use `allSettled` to get every result, `any` for the first success, `race` for the first to settle, and a limiter such as `p-limit` when you have thousands of tasks.

Outputs verified with Node.js 22 running CommonJS files. Since libuv 1.45 (Node 20 and later), the timers step technically runs at the end of each iteration, after close callbacks; the order of phases shown here is the same.
