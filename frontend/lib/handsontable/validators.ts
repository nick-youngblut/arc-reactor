import type { ValidationResult } from '@/stores/workspaceStore';

import type { SamplesheetColumn } from './columnConfig';

export const validateRequired = (value: unknown) => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  return true;
};

export const validateGcsPath = (value: unknown) => {
  if (value === null || value === undefined || value === '') return true;
  if (typeof value !== 'string') return false;
  return /^gs:\/\/.+/.test(value.trim());
};

export const validateNumeric = (value: unknown) => {
  if (value === null || value === undefined || value === '') return true;
  const num = typeof value === 'number' ? value : Number(value);
  if (Number.isNaN(num)) return false;
  return Number.isInteger(num) && num > 0;
};

export type SamplesheetRow = Record<string, string | number | null>;

export const validateSamplesheetRows = (
  rows: SamplesheetRow[],
  columns: SamplesheetColumn[]
): { result: ValidationResult; invalidCells: Set<string> } => {
  const errors: ValidationResult['errors'] = [];
  const warnings: ValidationResult['warnings'] = [];
  const invalidCells = new Set<string>();

  rows.forEach((row, rowIndex) => {
    const sampleName = typeof row.sample === 'string' ? row.sample : undefined;

    columns.forEach((column) => {
      const value = row[column.key];
      const cellKey = `${rowIndex}:${column.key}`;

      if (column.required && !validateRequired(value)) {
        errors.push({
          field: column.key,
          message: `${column.label} is required.`,
          sample: sampleName
        });
        invalidCells.add(cellKey);
        return;
      }

      if (column.key.startsWith('fastq') && !validateGcsPath(value)) {
        errors.push({
          field: column.key,
          message: `${column.label} must be a gs:// path.`,
          sample: sampleName
        });
        invalidCells.add(cellKey);
        return;
      }

      if (column.type === 'numeric' && !validateNumeric(value)) {
        errors.push({
          field: column.key,
          message: `${column.label} must be a positive integer.`,
          sample: sampleName
        });
        invalidCells.add(cellKey);
        return;
      }
    });

    const expectedCells = row.expected_cells;
    const numericExpected =
      expectedCells === null || expectedCells === undefined || expectedCells === ''
        ? null
        : typeof expectedCells === 'number'
          ? expectedCells
          : Number(expectedCells);

    if (numericExpected !== null && !Number.isNaN(numericExpected) && numericExpected < 5000) {
      warnings.push({
        field: 'expected_cells',
        message: 'Expected cells under 5000 may reduce sensitivity.',
        sample: sampleName
      });
    }
  });

  return {
    result: {
      isValid: errors.length === 0,
      errors,
      warnings
    },
    invalidCells
  };
};
