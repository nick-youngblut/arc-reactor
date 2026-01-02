import type { SamplesheetColumn } from './columnConfig';
import type { SamplesheetRow } from './validators';

const parseCsvLine = (line: string) => {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];

    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
      continue;
    }

    current += char;
  }

  result.push(current.trim());
  return result;
};

const defaultRow = (columns: SamplesheetColumn[]) => {
  return columns.reduce<SamplesheetRow>((acc, column) => {
    acc[column.key] = column.defaultValue ?? '';
    return acc;
  }, {});
};

export const parseSamplesheetCsv = (csvText: string, columns: SamplesheetColumn[]) => {
  const text = csvText.trim();
  if (!text) return [defaultRow(columns)];

  const lines = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (!lines.length) return [defaultRow(columns)];

  const rawHeader = parseCsvLine(lines[0]).map((value) => value.toLowerCase());
  const columnKeys = columns.map((column) => column.key);
  const headerMatches = rawHeader.some((header) =>
    columnKeys.some((key) => key.toLowerCase() === header)
  );

  const startIndex = headerMatches ? 1 : 0;
  const headerMap = headerMatches
    ? rawHeader.map((header) => columnKeys.find((key) => key.toLowerCase() === header) ?? '')
    : columnKeys;

  const rows = lines.slice(startIndex).map((line) => {
    const values = parseCsvLine(line);
    return columns.reduce<SamplesheetRow>((acc, column, index) => {
      const headerKey = headerMap[index] ?? column.key;
      const value = values[index] ?? '';
      if (headerKey === column.key) {
        acc[column.key] = value;
      }
      return acc;
    }, { ...defaultRow(columns) });
  });

  return rows.length ? rows : [defaultRow(columns)];
};

export const serializeSamplesheetCsv = (rows: SamplesheetRow[], columns: SamplesheetColumn[]) => {
  const header = columns.map((column) => column.key).join(',');
  const body = rows
    .map((row) =>
      columns
        .map((column) => {
          const value = row[column.key] ?? '';
          const stringValue = typeof value === 'string' ? value : String(value ?? '');
          if (stringValue.includes(',') || stringValue.includes('"')) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(',')
    )
    .join('\n');

  return `${header}\n${body}`.trim();
};
