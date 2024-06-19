import { test, expect } from 'vitest'

import { convertToProjectTemplate } from '@/components/project/helper.js'

const INPUT_DATA = {
  forename: 'Erno',
  surname: 'Testibus',
  contact_institution: 'Some Institution',
  contact_email: 'email@example.com',
  title: 'Some project',
  summary: 'Summary',
  date_published: null,
  external_sources: [
    {
      doi: 'abc',
      pmid: 123
    }
  ],
  metadata: [
    {
      rna: 'rnaABC',
      modomics_id: 456,
      method_id: 678,
      tech: 'techABC',
      taxa_id: 1234,
      cto: 'ctoCTO',
      assembly_id: null,
      assembly_name: 'MyAssembly',
      note: ''
    }
  ]
}

const OUTPUT_DATA = {
  title: 'Some project',
  summary: 'Summary',
  contact_email: 'email@example.com',
  contact_institution: 'Some Institution',
  contact_name: 'Testibus, Erno',
  date_published: null,
  external_sources: [
    {
      doi: 'abc',
      pmid: 123
    }
  ],
  metadata: [
    {
      method_id: 678,
      modomics_id: 456,
      note: '',
      organism: {
        assembly_id: null,
        assembly_name: 'MyAssembly',
        cto: 'ctoCTO',
        taxa_id: 1234
      },
      rna: 'rnaABC',
      tech: 'techABC'
    }
  ]
}

test('Convert ProjectForm to ProjectTemplate correctly', () => {
  expect(convertToProjectTemplate(INPUT_DATA)).toStrictEqual(OUTPUT_DATA)
})
