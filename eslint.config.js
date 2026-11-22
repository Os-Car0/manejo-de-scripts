const js = require('@eslint/js');
const globals = require('globals');
module.exports = [
  { ignores: ['node_modules/**', 'coverage/**', 'evidence/**', 'dist/**', 'tmp/**'] },
  js.configs.recommended,
  { files: ['**/*.js'], languageOptions: { ecmaVersion: 2024, globals: globals.node }, rules: { 'no-unused-vars': ['error', { argsIgnorePattern: '^_' }] } },
  { files: ['public/**/*.js'], languageOptions: { globals: globals.browser } },
  { files: ['tests/**/*.js'], languageOptions: { globals: globals.jest } }
];
