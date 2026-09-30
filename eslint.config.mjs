import globals from "globals";

const rules = {
  "no-unused-vars": ["error", { args: "after-used" }],
  "no-undef": "error",
  "prefer-const": "error",
  "no-var": "error",
  eqeqeq: ["error", "always"],
  semi: ["error", "always"],
  "no-redeclare": "error",
  "no-unreachable": "error",
  "no-dupe-keys": "error",
  "no-empty": "error",
  curly: ["error", "all"],
};

export default [
  { ignores: ["node_modules/**", "public/**"] },
  {
    files: [".cache/site.js"],
    languageOptions: { ecmaVersion: 2023, sourceType: "script", globals: { ...globals.browser } },
    rules,
  },
  {
    files: ["verify/node/**/*.js"],
    languageOptions: { ecmaVersion: 2023, sourceType: "commonjs", globals: { ...globals.node } },
    rules,
  },
];
