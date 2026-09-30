async function greet() {
  console.log("2: inside greet");
  const name = await getName();
  console.log(`4: hello ${name}`);
}

function getName() {
  return Promise.resolve("Ada");
}

console.log("1: start");
greet();
console.log("3: end");
