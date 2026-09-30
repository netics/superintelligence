const fs = require("fs");

fs.readFile(__filename, () => {
  console.log("1: file read");

  setTimeout(() => {
    console.log("3: timeout");
  }, 0);

  setImmediate(() => {
    console.log("2: immediate");
  });
});
