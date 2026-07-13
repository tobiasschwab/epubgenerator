module.exports = {
  root: true,
  env: { browser: true, es2021: true },
  extends: ["eslint:recommended"],
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  settings: { react: { version: "18" } },
  ignorePatterns: ["dist", "node_modules"],
};
