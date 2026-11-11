import { Cache, GroupedCache, uniqueByKey } from '@/utils/cache'
import { HTTP } from '@/services/API'
import { type Taxa } from '@/services/taxa'

interface ModificationType {
  modification_id: number
  modomics_short_name: string
  rna_type: string
  rna_type_name: string
}

interface Cto extends Taxa {
  organism_id: number // may be a bad name - the database table is called 'Organism'
  cto: string
}

interface Technology {
  technology_id: number
  cls: string
  meth: string
  tech: string
}

// w/o selection_id
interface SelectionBase extends ModificationType, Cto, Technology {}

interface Selection extends SelectionBase {
  selection_id: number
}

// a selection itself is first created on dataset upload
interface ProjectSelection extends SelectionBase {
  selection_id: number | null
}

class SelectionCache extends Cache<Selection[]> {
  async getPromise(): Promise<Selection[]> {
    const response = await HTTP.get<Selection[]>('/catalogs/selections')
    return response.data
  }
}

// selections of a project, not cached
async function getProjectSelections(projectId: string): Promise<ProjectSelection[]> {
  const response = await HTTP.get<ProjectSelection[]>(`/projects/${projectId}/selections`)
  return response.data
}

function toModificationType(x: SelectionBase): ModificationType {
  return {
    modification_id: x.modification_id,
    modomics_short_name: x.modomics_short_name,
    rna_type: x.rna_type,
    rna_type_name: x.rna_type_name
  }
}

function toTaxa(x: SelectionBase): Taxa {
  return {
    taxa_id: x.taxa_id,
    domain: x.domain,
    kingdom: x.kingdom,
    taxa_name: x.taxa_name,
    taxa_short_name: x.taxa_short_name
  }
}

function toCto(x: SelectionBase): Cto {
  return {
    organism_id: x.organism_id,
    domain: x.domain,
    kingdom: x.kingdom,
    taxa_id: x.taxa_id,
    taxa_name: x.taxa_name,
    taxa_short_name: x.taxa_short_name,
    cto: x.cto
  }
}

function toTechnology(x: SelectionBase): Technology {
  return {
    technology_id: x.technology_id,
    cls: x.cls,
    meth: x.meth,
    tech: x.tech
  }
}

const selectionsCache = new SelectionCache()

const modificationTypeSelectionCache: GroupedCache<ModificationType, Selection, number> =
  new GroupedCache(selectionsCache, (x) => x.modification_id, toModificationType)

const taxaSelectionCache: GroupedCache<Taxa, Selection, number> = new GroupedCache(
  selectionsCache,
  (x) => x.taxa_id,
  toTaxa
)

// NOTE: an empty list is a valid choice (no selections)
async function resolveSelections(
  selections?: readonly SelectionBase[]
): Promise<readonly SelectionBase[]> {
  return selections ?? (await selectionsCache.getData())
}

async function getSelectionsByIds(
  modificationId: number,
  organismId: number,
  technologyIds: number[]
): Promise<Selection[]> {
  return (await selectionsCache.getData()).filter(
    (x) =>
      x.modification_id === modificationId &&
      x.organism_id === organismId &&
      technologyIds.includes(x.technology_id)
  )
}

async function getSelectionsByTaxaId(taxaId: number): Promise<Selection[]> {
  return (await selectionsCache.getData()).filter((x) => x.taxa_id === taxaId)
}

// These functions group the selections they are given (e.g. those of a project) and do not
// use the grouped caches above, which are built from all selections only. The grouping is
// recomputed on each call, which is cheap for the number of selections (cf. resolveSelections).

function getModificationTypes(selections: readonly SelectionBase[]): ModificationType[] {
  return uniqueByKey(selections, (x) => x.modification_id, toModificationType)
}

function getModificationTypesByRnaType(
  selections: readonly SelectionBase[],
  rnaType: string
): ModificationType[] {
  return getModificationTypes(selections).filter((x) => x.rna_type === rnaType)
}

function getCtos(selections: readonly SelectionBase[]): Cto[] {
  return uniqueByKey(selections, (x) => x.organism_id, toCto)
}

function getCtosByModificationIds(
  selections: readonly SelectionBase[],
  modificationIds: number[]
): Cto[] {
  const organismIds = new Set<number>()
  for (const item of selections) {
    if (modificationIds.includes(item.modification_id)) {
      organismIds.add(item.organism_id)
    }
  }
  return getCtos(selections).filter((x) => organismIds.has(x.organism_id))
}

function getTechnologies(selections: readonly SelectionBase[]): Technology[] {
  return uniqueByKey(selections, (x) => x.technology_id, toTechnology)
}

function getTechnologiesByModificationIdsAndOrganismId(
  selections: readonly SelectionBase[],
  modificationIds: number[],
  organismId: number
): Technology[] {
  const technologyIds = new Set<number>()
  for (const item of selections) {
    if (modificationIds.includes(item.modification_id) && item.organism_id === organismId) {
      technologyIds.add(item.technology_id)
    }
  }
  return getTechnologies(selections).filter((x) => technologyIds.has(x.technology_id))
}

export {
  type Selection,
  type ProjectSelection,
  type SelectionBase,
  type ModificationType,
  type Cto,
  type Technology,
  selectionsCache,
  modificationTypeSelectionCache,
  taxaSelectionCache,
  resolveSelections,
  getProjectSelections,
  getModificationTypesByRnaType,
  getCtos,
  getCtosByModificationIds,
  getTechnologiesByModificationIdsAndOrganismId,
  getSelectionsByTaxaId,
  getSelectionsByIds
}
