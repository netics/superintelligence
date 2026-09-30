---
title: "JavaScript types explained: typeof, ==, copies, floats | Runtime lines"
description: "The typeof junction, how V8 stores each type, copies versus references, the exact == algorithm, truthiness and the 64 bits inside a number."
url: https://superintelligence.ro/js-types
alternate_en: https://superintelligence.ro/js-types.md
alternate_ro: https://superintelligence.ro/ro/js-types.md
---

# JavaScript types, sorted at the junction

Every JavaScript value is one of seven primitive types or an object. Send values through the `typeof` junction, flip the cards to see how V8 stores them, trace exactly what `==` does, and take a number apart bit by bit.

## Seven primitives and one object type

Primitives are immutable and compared by value; objects are mutable and compared by reference. Flip a card to see how V8 represents that type.

**Stack or heap?** You’ll often read that primitives live on the stack and objects on the heap. In V8 almost everything lives on the heap, and a variable holds a pointer to it; only small integers (Smis) fit inside the slot itself. What really separates primitives is that they can’t be changed, so sharing one is invisible.

## Copy or share?

Assigning a primitive copies it. Assigning an object copies a reference. Spread copies one level deep; `structuredClone` copies all the way down.

## What == actually does

`===` never converts. `==` follows a fixed list of conversion rules from the spec, one step at a time. Pick two values and follow the trace, or click any square in the grid.

## Truthy or falsy?

An `if` converts its condition with `Boolean()`. Exactly eight values are falsy; everything else, including some surprising ones, is truthy. Pick a value, then pick the bin you think it belongs in.

## Inside a number

A JavaScript `number` is an IEEE 754 double: 1 sign bit, 11 exponent bits and 52 fraction bits. Type a value, pick a preset, or flip any bit and watch the number change.

## Interview questions: JavaScript types

Short answers you can say out loud. Try answering each question yourself before you open it.

### What are JavaScript’s types?

Seven primitives (`undefined`, `null`, `boolean`, `number`, `bigint`, `string` and `symbol`) plus objects. Arrays, functions, dates, maps and class instances are all objects.

### What can `typeof` return?

Eight strings: "undefined", "boolean", "number", "bigint", "string", "symbol", "object" and "function". `typeof null` is "object" because of a historical bug, so test for null with `=== null` and for arrays with `Array.isArray()`.

### `==` or `===`?

Default to `===`, which never converts types. `==` applies conversion rules: `null` and `undefined` only equal each other, booleans become numbers, a string compared with a number becomes a number, and objects are turned into primitives. The one common use of `==` is `x == null`, which checks for null or undefined.

### Is JavaScript pass-by-reference?

No. Everything is passed by value, but the value of an object variable is a reference. A function can mutate an object you pass in, but reassigning the parameter doesn’t change your variable. Python works the same way.

### Shallow copy or deep copy?

Spread, `Object.assign` and `slice()` copy one level, so nested objects stay shared. `structuredClone` copies deeply, including `Map`, `Set`, `Date` and circular references, but it throws on functions, and class instances come back as plain objects.

### Why is `0.1 + 0.2 !== 0.3`?

Numbers are 64-bit IEEE 754 doubles, and 0.1, 0.2 and 0.3 have no exact binary form, so each is stored as the nearest double and the rounding errors don’t cancel out. Compare with a tolerance, or keep money in integer cents.

### Which values are falsy?

`false`, `0`, `-0`, `0n`, `""`, `null`, `undefined` and `NaN` (plus the legacy `document.all` in browsers). Everything else is truthy, including `"0"`, `"false"`, `[]` and `{}`.

### What is `Number.MAX_SAFE_INTEGER`, and why does it matter?

253 − 1. Above it, not every integer can be represented, so a 64-bit ID from a database can silently change when parsed as a number. Keep such IDs as strings or `BigInt`.

### `null` or `undefined`?

`undefined` means a value was never set: a missing property, an unassigned variable, a function with no return. `null` is an explicit “no value” that you assign. JSON has `null` but no `undefined`, and `JSON.stringify` drops properties whose value is `undefined`.

### Why is `typeof null` equal to `"object"`?

A bug from the first JavaScript engine: values carried a type tag, objects had tag 0, and `null` was the null pointer, which also read as 0. Changing it now would break the web, so it stays. Test for null with `x === null`.

### How do you reliably check that a value is an array?

`Array.isArray(x)`. `typeof` says `"object"`, and `instanceof Array` fails for arrays from another realm, such as an iframe or a `vm` context, because each realm has its own `Array` constructor.

### What is `NaN`, and how do you test for it?

The IEEE 754 value for an undefined result, like `0 / 0` or `Number("abc")`. Its type is `number`, and it isn’t equal to anything, itself included, so `x === NaN` is always false. Use `Number.isNaN(x)`; the global `isNaN` converts first, so `isNaN("abc")` is true.

### How is `Object.is` different from `===`?

In exactly two cases: `Object.is(NaN, NaN)` is true, and `Object.is(0, -0)` is false. Everything else matches `===`. React uses it to decide whether state changed, and `Map`, `Set` and `includes` use a variant that treats `0` and `-0` as equal.

### How can a primitive like `"abc"` have methods?

When you write `"abc".toUpperCase()`, the engine uses a temporary `String` wrapper to find the method on `String.prototype`; the primitive itself doesn’t change. Never create wrappers yourself with `new String` or `new Boolean`: `new Boolean(false)` is an object, so it’s truthy.

### How does JavaScript turn an object into a primitive?

It calls `obj[Symbol.toPrimitive](hint)` if it exists. Otherwise it tries `valueOf()` then `toString()` for a number hint, and the other way round for a string hint. That’s why `[] + {}` is `"[object Object]"`: `[]` becomes `""`, `{}` becomes `"[object Object]"`, and `+` joins strings.

### What is `BigInt`, and when do you use it?

An integer type of any size, written `123n`, with `typeof"bigint"`. Use it for IDs, money in minor units or anything beyond 253. You can’t mix it with numbers in arithmetic (`1n + 1` throws a `TypeError`), it has no fractions, and `JSON.stringify` throws on it.

### What is a `Symbol` for?

A unique value, mostly used as a property key that can’t clash with any other key, even one with the same description. `for...in`, `Object.keys` and `JSON.stringify` skip symbol keys. Built-in ones like `Symbol.iterator` let your objects plug into language features such as `for...of`.

### Does `const` make an object immutable?

No. `const` only stops you from rebinding the name; the object it points at can still change. `Object.freeze` stops changes to the object’s own properties, but it’s shallow: nested objects stay mutable unless you freeze them too.

### `structuredClone` or `JSON.parse(JSON.stringify(x))`?

Prefer `structuredClone`: it copies `Date`, `Map`, `Set`, typed arrays and circular references. The JSON round trip drops `undefined` and functions, turns dates into strings and `NaN` into `null`, and throws on cycles and `BigInt`. Neither copies functions or keeps class prototypes.

### What is a Smi?

A small integer that V8 stores inside the pointer itself, tagged by its lowest bit, so it needs no allocation. Numbers that don’t fit, such as fractions, `-0` or large integers, become a HeapNumber: a 64-bit float in a separate heap object. That’s why integer-heavy code is often faster.

### What are hidden classes, and why does property order matter?

V8 gives every object a hidden class, or shape, that records its properties and where they are stored. Objects built with the same properties in the same order share a shape, so property access can be cached and becomes very fast. Adding properties in different orders, or using `delete`, creates new shapes and slows that code down.

### What are packed and holey arrays?

V8 tracks what an array holds: only small integers, only doubles, or anything, and whether it has holes. Packed small-integer arrays are the fastest. Transitions only go one way: after `arr.push(1.5)` or a hole like `arr[100] = 1`, that array never becomes fast again. `new Array(n)` starts out holey.

### Why does JavaScript have `-0`?

IEEE 754 floats keep a sign bit even for zero. `0 === -0` is true, but `1 / -0` is `-Infinity` and `Object.is(0, -0)` is false. It shows up when a small negative value rounds to zero, and it can tell you which direction a value approached zero from.

### How do you handle money without float errors?

Store integer minor units such as cents, with `BigInt` if they can get large, or use a decimal library, and format with `Intl.NumberFormat`. `toFixed` is not a fix: it rounds the binary value, so `(1.005).toFixed(2)` is `"1.00"`, because 1.005 is really 1.00499999...

### `parseInt` or `Number`?

`parseInt` reads digits until it hits something else, so `parseInt("12px")` is 12. `Number` converts the whole string or returns `NaN`, so `Number("12px")` is `NaN`, but `Number("")` is 0. Always give `parseInt` a radix, and never pass it numbers: `parseInt(0.0000005)` is 5.

### When is `==` acceptable?

For `x == null`, which is true only for `null` and `undefined`, so it catches both in one check. Many style guides allow exactly that one case and use `===` everywhere else.

### What is the difference between `??` and `||`?

`a || b` falls back to `b` for every falsy value, including `0`, `""` and `false`. `a ?? b` falls back only for `null` and `undefined`. For defaults such as `count ?? 10` you want `??`, so that a real 0 is kept.

### `Map` or a plain object?

Use a `Map` for dictionaries with dynamic keys: keys can be any value, including objects, it has `size`, iterates in insertion order and has no inherited keys like `__proto__` to worry about. Object keys are always strings or symbols, and integer-like keys are listed first, in numeric order. Use objects for records with fixed fields.

### What is a `WeakMap` for?

Attaching data to objects you don’t own without keeping them alive. Keys must be objects, and once a key is unreachable anywhere else, the entry can be garbage collected. Because entries can disappear at any time, a `WeakMap` can’t be iterated and has no `size`. Typical uses: caches and private data per DOM node.

typeof results, conversions and truthiness follow the ECMAScript specification and match V8 in Node.js and Chrome. The copy example prints `10 20 Bob [ 'dev', 'ops' ] [ 'dev', 'ops', 'qa' ]` in Node.js 22.
