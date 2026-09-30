const t0 = Date.now();
setTimeout(() => {
  console.log("timer (wanted 10 ms)", Date.now() - t0);
}, 10);

const start = Date.now();
while (Date.now() - start < 100) {
  // busy-wait: the call stack is never empty
}

console.log("loop done at 100 ms");
