import js from '../../../frontend/node_modules/@eslint/js/src/index.js';
import globals from '../../../frontend/node_modules/globals/index.js';
export default [{files:['**/*.cjs'],languageOptions:{ecmaVersion:2022,sourceType:'commonjs',globals:globals.node},rules:js.configs.recommended.rules}];
