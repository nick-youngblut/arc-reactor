export type ColumnType = 'text' | 'numeric' | 'dropdown';

export interface SamplesheetColumn {
  key: string;
  label: string;
  type: ColumnType;
  required?: boolean;
  options?: string[];
  defaultValue?: string | number;
  helpText?: string;
}

const scrnaSeqColumns: SamplesheetColumn[] = [
  {
    key: 'sample',
    label: 'Sample',
    type: 'text',
    required: true,
    helpText: 'Sample identifier'
  },
  {
    key: 'fastq_1',
    label: 'FASTQ R1',
    type: 'text',
    required: true,
    helpText: 'Path to R1 FASTQ (gs://...)'
  },
  {
    key: 'fastq_2',
    label: 'FASTQ R2',
    type: 'text',
    required: true,
    helpText: 'Path to R2 FASTQ (gs://...)'
  },
  {
    key: 'expected_cells',
    label: 'Expected Cells',
    type: 'numeric',
    required: false,
    defaultValue: 10000,
    helpText: 'Optional expected cell count'
  }
];

const pipelineColumns: Record<string, SamplesheetColumn[]> = {
  'nf-core/scrnaseq': scrnaSeqColumns
};

export const getSamplesheetColumns = (pipeline?: string | null) => {
  if (!pipeline) return scrnaSeqColumns;
  return pipelineColumns[pipeline] ?? scrnaSeqColumns;
};
