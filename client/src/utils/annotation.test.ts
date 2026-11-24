import { test, expect } from 'vitest'
import { type Annotation } from '@/services/annotation'
import { formatAssemblies, formatReleases } from '@/utils/annotation'

function annotation(overrides: Partial<Annotation> = {}): Annotation {
  return {
    id: 1,
    source: 'ensembl',
    release: 110,
    archive: 'jul2023',
    browse_url: 'https://jul2023.archive.ensembl.org/Homo_sapiens',
    assembly_id: 1,
    assembly_name: 'GRCh38',
    taxa_id: 9606,
    taxa_name: 'Homo sapiens',
    ...overrides
  }
}

test('formatAssemblies names each assembly with its organism', () => {
  expect(
    formatAssemblies([
      annotation(),
      annotation({
        id: 2,
        assembly_id: 2,
        assembly_name: 'GRCm39',
        taxa_id: 10090,
        taxa_name: 'Mus musculus'
      })
    ])
  ).toBe('GRCh38 (Homo sapiens) and GRCm39 (Mus musculus)')
})

test('formatAssemblies reports an assembly once however it is annotated', () => {
  expect(
    formatAssemblies([annotation(), annotation({ id: 2, source: 'gtrnadb', release: 19 })])
  ).toBe('GRCh38 (Homo sapiens)')
})

test('formatReleases', () => {
  expect(formatReleases([annotation()])).toBe('Ensembl release 110')
})

test('formatReleases reports one entry per source and release', () => {
  expect(
    formatReleases([
      annotation(),
      annotation({
        id: 2,
        assembly_id: 2,
        taxa_id: 10090,
        taxa_name: 'Mus musculus',
        assembly_name: 'GRCm39'
      }),
      annotation({ id: 3, source: 'gtrnadb', release: 19, archive: null, browse_url: null })
    ])
  ).toBe('Ensembl release 110 and GtRNAdb release 19')
})

test('formatReleases capitalises a source it has no label for', () => {
  expect(formatReleases([annotation({ source: 'some-provider' })])).toBe(
    'Some-provider release 110'
  )
})

test('formatting is empty without annotations', () => {
  // the sentence has to read without them
  expect(formatAssemblies([])).toBe('')
  expect(formatReleases([])).toBe('')
})
