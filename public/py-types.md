---
title: "Python types explained: operator dispatch, +=, hashing | Runtime lines"
description: "The built-in types and where to use each one, how a + b is dispatched, when += changes things in place, and how dict keys are hashed."
url: https://superintelligence.ro/py-types
alternate_en: https://superintelligence.ro/py-types.md
alternate_ro: https://superintelligence.ro/ro/py-types.md
---

# Python types, and how they get along

Everything in Python is an object, and its type decides what operators do with it. Explore the type network, send two operands through the operator machinery, then watch `+=` and dict keys behave in ways that surprise most people.

## What happens when you write a + b

Python asks the left operand first. If its method returns `NotImplemented`, the right operand gets a turn with the reflected method. Pick two values and an operator; every step below was recorded from real CPython objects.

## += changes things in place, or doesn’t

`x += y` first tries `x.__iadd__(y)`. Mutable types implement it and change the object in place; immutable ones don’t, so Python falls back to `x = x + y` and rebinds the name.

## Dict keys and hashing

A dict keeps its entries in insertion order plus a small index table. `hash(key)` picks a slot, and keys that are equal must have equal hashes, which is exactly why `1`, `True` and `1.0` end up as one key.

## Interview questions: Python types

Short answers you can say out loud. Try answering each question yourself before you open it.

### Which built-in types are mutable?

`list`, `dict`, `set` and `bytearray`, plus most classes you write. `int`, `float`, `complex`, `bool`, `str`, `bytes`, `tuple`, `frozenset`, `range` and `None` are immutable: every “change” builds a new object.

### What makes an object hashable, and why does it matter?

It needs a `__hash__` that never changes during its lifetime, and objects that compare equal must hash equally. Only hashable objects can be dict keys or set members, which is why a list can’t be a key but a tuple of hashable items can.

### Why do `1`, `True` and `1.0` end up as one dict key?

They compare equal and have the same hash, so the dict treats them as one key. The first key object is kept and only the value is replaced, as the hashing stepper on this line shows.

### What happens when Python evaluates `a + b`?

It calls `a.__add__(b)`. If that returns `NotImplemented`, it tries `b.__radd__(a)`, and raises `TypeError` if both give up. If b’s type is a subclass of a’s type that overrides `__radd__`, b goes first.

### Is `x += y` the same as `x = x + y`?

Not for mutable types. `+=` calls `__iadd__` first, which extends a list in place, so every name for that list sees the change. Immutable types fall back to `x = x + y` and rebind only x. That’s also why `pair[0] += [2]` on a tuple both mutates the list and raises.

### What’s wrong with `def f(items=[])`?

Default values are evaluated once, when the function is defined, so every call shares the same list. Use `items=None` and create a new list inside the function.

### Why write `x is None` instead of `x == None`?

`None` is a singleton, so identity is the precise test. It’s also faster, and it can’t be fooled by a class whose `__eq__` says yes to everything.

### list, tuple, set or dict: how do you choose?

A list for an ordered collection you change, a tuple for a fixed record or a hashable key, a set for uniqueness and fast membership tests, and a dict for lookup by key. Reach for a `frozenset` when you need a set that is hashable.

### How do you copy a nested structure?

`list(x)`, `x.copy()`, `x[:]` and `copy.copy()` are shallow: the new container holds the same inner objects. `copy.deepcopy()` copies everything recursively.

### A tuple is immutable. Why can `t[0] += [1]` both raise an error and change the tuple?

`+=` first calls `list.__iadd__`, which extends the list inside the tuple in place, then tries to store the result back into `t[0]`, which raises `TypeError`. The tuple’s slots can’t change, but the objects in them can. For the same reason, a tuple that contains a list isn’t hashable.

### What is the contract between `__eq__` and `__hash__`?

Objects that compare equal must have equal hashes, and the hash must not change while the object is in a set or dict. That’s why defining `__eq__` sets `__hash__` to `None`: Python makes the class unhashable until you define a hash based on the same fields. `@dataclass(frozen=True)` does both for you.

### How does a dict work inside?

It’s a hash table. The key’s hash picks a slot in a small index array, collisions are resolved by probing other slots, and the index points into a compact array of entries kept in insertion order. Lookups, inserts and deletes are O(1) on average, and a hit is confirmed with `is` or `==` on the key.

### Are dicts ordered?

Yes, insertion order is guaranteed since Python 3.7. `OrderedDict` is still useful: it has `move_to_end`, its equality checks take order into account, and it’s handy for LRU caches. Sets have no order at all.

### What is duck typing?

Python cares what an object can do, not what class it is: anything with `__iter__` can be looped over, anything with `read()` can act as a file. Code usually just tries the operation and handles the exception (EAFP). For type checkers, `typing.Protocol` describes such a shape without inheritance.

### `NotImplemented` or `NotImplementedError`?

`NotImplemented` is a value you return from a binary method such as `__add__` or `__eq__` to say “I don’t know this type”, so Python tries the other operand’s method. `NotImplementedError` is an exception you raise in a method that subclasses must override. Raising the first or returning the second are both bugs.

### When does Python call `__radd__`?

For `a + b`, when `a` has no `__add__` or it returns `NotImplemented`, Python tries `b.__radd__(a)`. One exception: if `b`’s type is a subclass of `a`’s type and overrides `__radd__`, it goes first, so subclasses can take control. It’s how `sum()` works on custom types starting from `0`.

### Are type hints checked at runtime?

No. Python ignores them when it runs your code; tools such as mypy and pyright check them before it runs. They are available at runtime through `typing.get_type_hints()` and `annotationlib`, which is how libraries like Pydantic and FastAPI validate data. Since 3.14 annotations are evaluated lazily, only when something asks for them.

### Can a Python int overflow?

No, ints have arbitrary precision and grow as needed; `sys.maxsize` is the largest container size, not the largest int. Big ints just get slower. Since 3.11, converting an int with more than 4300 digits to or from a string raises `ValueError` by default, to prevent denial-of-service attacks.

### What do `//` and `%` do with negative numbers?

`//` rounds down, towards minus infinity, so `-7 // 2` is `-4`, and `%` takes the sign of the divisor: `-7 % 2` is `1`. JavaScript, C and Java truncate towards zero instead. `int(-3.5)` truncates too, giving `-3`.

### Why is `round(2.5)` equal to 2?

Python rounds halves to the nearest even number (banker’s rounding), so `round(2.5)` is 2 and `round(3.5)` is 4; that avoids a bias when you add many rounded values. `round(2.675, 2)` gives `2.67` because 2.675 can’t be stored exactly. For money, use `decimal.Decimal`.

### `str` or `bytes`?

`str` is text, a sequence of Unicode code points. `bytes` is raw 8-bit data from files, sockets or hashes. Python 3 never converts between them implicitly: `encode()` text into bytes and `decode()` bytes into text at the edges of your program, naming the encoding, usually UTF-8.

### Why can `len("é")` be 2?

`len` counts code points, not what you see. “é” can be one code point (U+00E9) or two: “e” plus a combining accent. Normalise with `unicodedata.normalize("NFC", s)` before comparing or counting. Internally, CPython stores each string with 1, 2 or 4 bytes per character, depending on its widest one.

### Why is building a string with `+=` in a loop slow?

Strings are immutable, so each `+=` can create a new string and copy everything so far, which is O(n²) overall. CPython sometimes extends in place, but other implementations don’t, and you can’t rely on it. Collect the parts in a list and call `"".join(parts)` once, or use `io.StringIO`.

### `isinstance(x, T)` or `type(x) is T`?

`isinstance` accepts subclasses and abstract base classes such as `collections.abc.Mapping`, which is almost always what you want. It has one classic surprise: `bool` is a subclass of `int`, so `isinstance(True, int)` is true and `True + True` is 2. Use `type(x) is T` only when subclasses must be rejected.

### How fast is `x in` a list, a set and a dict?

A list checks every element in turn: O(n). Sets and dicts hash `x` and look in one slot: O(1) on average. Turning a list into a set before checking thousands of values in a loop is one of the easiest big speed-ups. `x in range(...)` is O(1) too: it’s just arithmetic.

### namedtuple, dataclass, TypedDict or dict?

`namedtuple`: an immutable, lightweight tuple with field names. `dataclass`: a normal class with generated `__init__`, `__repr__` and `__eq__`, mutable or frozen, with defaults and methods. `TypedDict`: type hints for dicts that stay plain dicts, such as JSON payloads. A plain `dict`: truly dynamic keys.

### Is `sorted` stable, and what does it need?

Yes. Python’s sort is stable, so items with equal keys keep their order, and you can sort by several keys in several passes, the least important first. It’s O(n log n) and very fast on data that is already partly sorted. It only needs `<`; mixing types that can’t be compared, like `None` and `int`, raises `TypeError`.

### How does Python decide whether an object is truthy?

It calls `__bool__` if the class defines it, otherwise `__len__`, and treats anything else as true. So `None`, `False`, zero of every numeric type and empty containers are falsy. Watch out for `if not x:` when 0 or an empty list is a valid value; write `if x is None:` instead.

### What is the difference between an iterable and an iterator?

An iterable, like a list, can give you a fresh iterator with `iter()`, as often as you like. An iterator remembers its position, returns the next item from `__next__` and is used up after one pass. Generators and file objects are iterators, which is why looping over one a second time yields nothing.

Dispatch traces were recorded by calling each dunder method on real objects in CPython 3.12. String hashes change every run unless `PYTHONHASHSEED` is set, so the hash shown for `'1'` is one possible value.
