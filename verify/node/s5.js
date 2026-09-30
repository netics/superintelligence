process.nextTick(() => {
  console.log("tick 1");
  Promise.resolve().then(() => console.log("promise 2"));
});

Promise.resolve().then(() => {
  console.log("promise 1");
  process.nextTick(() => console.log("tick 2"));
});
