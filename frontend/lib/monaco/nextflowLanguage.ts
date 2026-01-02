import type { Monaco } from '@monaco-editor/react';

export const registerNextflowLanguage = (monaco: Monaco) => {
  const languageId = 'nextflow';

  if (monaco.languages.getLanguages().some((lang) => lang.id === languageId)) {
    return;
  }

  monaco.languages.register({ id: languageId });

  monaco.languages.setMonarchTokensProvider(languageId, {
    tokenizer: {
      root: [
        [/\b(params|process|workflow|include|from|into|input|output|script|when)\b/, 'keyword'],
        [/\b(true|false|null)\b/, 'constant'],
        [/\b\d+(\.\d+)?\b/, 'number'],
        [/"([^"\\]|\\.)*"/, 'string'],
        [/'([^'\\]|\\.)*'/, 'string'],
        [/\/\/.*$/, 'comment'],
        [/\/\*[\s\S]*?\*\//, 'comment']
      ]
    }
  });

  monaco.languages.setLanguageConfiguration(languageId, {
    comments: {
      lineComment: '//',
      blockComment: ['/*', '*/']
    },
    brackets: [
      ['{', '}'],
      ['[', ']'],
      ['(', ')']
    ],
    autoClosingPairs: [
      { open: '{', close: '}' },
      { open: '[', close: ']' },
      { open: '(', close: ')' },
      { open: '"', close: '"' },
      { open: "'", close: "'" }
    ]
  });
};
