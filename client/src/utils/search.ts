import {
  type Selection,
  type ModificationType,
  type Technology,
  type Cto
} from '@/services/selection'
import { type Taxa } from '@/services/taxa'
import type { Chrom } from '@/services/chrom'

type SearchBy = 'Modification' | 'Gene/Chrom'
interface PrimarySearchParameters {
  selections: Selection[]
  taxa: Taxa
  cto?: Cto
  modificationType?: ModificationType
  technologies?: Technology[]
  rna_type: 'WTS' // Will this be variable at some point???
}
interface SecondarySearchParameters {
  searchBy: SearchBy
  gene?: string
  biotypes?: string[]
  features?: string[]
  chrom?: Chrom
  chromStart?: number
  chromEnd?: number
}

interface SearchParameters extends PrimarySearchParameters, SecondarySearchParameters {
  state: 'complete'
}

interface DummySearchParameters extends SecondarySearchParameters {
  state: 'incomplete'
}

function isSearchParameter(
  x: SearchParameters | DummySearchParameters | undefined | null
): x is SearchParameters {
  return x?.state === 'complete'
}

export {
  type PrimarySearchParameters,
  type SecondarySearchParameters,
  type SearchBy,
  type SearchParameters,
  type DummySearchParameters,
  isSearchParameter
}
