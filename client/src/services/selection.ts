import { Cache, GroupedCache } from '@/utils/cache'
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

interface Selection extends ModificationType, Cto, Technology {
  selection_id: number
}

class SelectionCache extends Cache<Selection[]> {
  async getPromise(): Promise<Selection[]> {
    const response = await HTTP.get<Selection[]>('/catalogs/selections')
    return response.data
  }
}

const selectionsCache = new SelectionCache()
const modificationTypeSelectionCache: GroupedCache<ModificationType, Selection, number> =
  new GroupedCache(
    selectionsCache,
    (x) => x.modification_id,
    (x) => {
      return {
        modification_id: x.modification_id,
        modomics_short_name: x.modomics_short_name,
        rna_type: x.rna_type,
        rna_type_name: x.rna_type_name
      }
    }
  )

const taxaSelectionCache: GroupedCache<Taxa, Selection, number> = new GroupedCache(
  selectionsCache,
  (x) => x.taxa_id,
  (x) => ({
    taxa_id: x.taxa_id,
    domain: x.domain,
    kingdom: x.kingdom,
    taxa_name: x.taxa_name,
    taxa_short_name: x.taxa_short_name
  })
)

const ctoSelectionCache: GroupedCache<Cto, Selection, number> = new GroupedCache(
  selectionsCache,
  (x) => x.organism_id,
  (x) => ({
    organism_id: x.organism_id,
    domain: x.domain,
    kingdom: x.kingdom,
    taxa_id: x.taxa_id,
    taxa_name: x.taxa_name,
    taxa_short_name: x.taxa_short_name,
    cto: x.cto
  })
)

const technologySelectionCache: GroupedCache<Technology, Selection, number> = new GroupedCache(
  selectionsCache,
  (x) => x.technology_id,
  (x) => {
    return {
      technology_id: x.technology_id,
      cls: x.cls,
      meth: x.meth,
      tech: x.tech
    }
  }
)

async function getCtosByModificationIds(modificationIds: number[]): Promise<Cto[]> {
  const organismIds = new Set<number>()
  for (const item of await selectionsCache.getData()) {
    if (modificationIds.includes(item.modification_id)) {
      organismIds.add(item.organism_id)
    }
  }
  return (await ctoSelectionCache.getData()).filter((x) => organismIds.has(x.organism_id))
}

async function getTechnologiesByModificationIdsAndOrganismId(
  modificationIds: number[],
  organismId: number
) {
  const technologyIds = new Set<number>()
  for (const item of await selectionsCache.getData()) {
    if (modificationIds.includes(item.modification_id) && item.organism_id === organismId) {
      technologyIds.add(item.technology_id)
    }
  }
  return (await technologySelectionCache.getData()).filter((x) =>
    technologyIds.has(x.technology_id)
  )
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

async function getTechnologiesByIds(technologyIds: number[]): Promise<Technology[]> {
  const candidates = (await technologySelectionCache.getData()).filter((x) =>
    technologyIds.includes(x.technology_id)
  )
  if (candidates.length > 0) {
    return candidates
  } else {
    throw Error(`Technologies '${technologyIds}' not found`)
  }
}

async function getModificationTypesByRnaType(rnaType: string): Promise<ModificationType[]> {
  return (await modificationTypeSelectionCache.getData()).filter((x) => x.rna_type === rnaType)
}

export {
  type Selection,
  type ModificationType,
  type Cto,
  type Technology,
  selectionsCache,
  modificationTypeSelectionCache,
  taxaSelectionCache,
  ctoSelectionCache,
  technologySelectionCache,
  getCtosByModificationIds,
  getTechnologiesByModificationIdsAndOrganismId,
  getSelectionsByTaxaId,
  getSelectionsByIds,
  getTechnologiesByIds,
  getModificationTypesByRnaType
}
