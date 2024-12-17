import { Cache, GroupedCache } from '@/utils/cache'
import { HTTP } from '@/services/API'
import { type Taxa } from '@/services/taxa'

interface ModificationType {
  modification_id: number
  modomics_sname: string
  rna_name: string
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
    try {
      const response = await HTTP.get('/selections')
      return response.data as Selection[]
    } catch (err) {
      console.log(`Failed to fetch selections: ${err}`)
      throw err
    }
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
        modomics_sname: x.modomics_sname,
        rna_name: x.rna_name
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
    taxa_sname: x.taxa_sname
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
    taxa_sname: x.taxa_sname,
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
  const canidates = (await technologySelectionCache.getData()).filter((x) =>
    technologyIds.includes(x.technology_id)
  )
  if (canidates.length > 0) {
    return canidates
  } else {
    throw Error(
      `Wanted technologies with IDs ${technologyIds} but got 0! That should never happen!`
    )
  }
}

async function getModificationTypesByRnaName(rnaName: string): Promise<ModificationType[]> {
  return (await modificationTypeSelectionCache.getData()).filter((x) => x.rna_name === rnaName)
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
  getModificationTypesByRnaName
}
