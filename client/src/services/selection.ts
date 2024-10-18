import { Cache, GroupedCache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface ModificationType {
  modification_id: number
  modomics_sname: string
  rna_name: string
}

interface Organism {
  organism_id: number
  domain: string
  kingdom: string | null
  taxa_id: number
  taxa_name: string
  taxa_sname: string
  cto: string
}

interface Technology {
  technology_id: number
  cls: string
  meth: string
  tech: string
}

interface Selection extends ModificationType, Organism, Technology {
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
const modificationTypeCache: GroupedCache<ModificationType, Selection, number> = new GroupedCache(
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
const organismCache: GroupedCache<Organism, Selection, number> = new GroupedCache(
  selectionsCache,
  (x) => x.organism_id,
  (x) => {
    return {
      organism_id: x.organism_id,
      domain: x.domain,
      kingdom: x.kingdom,
      taxa_id: x.taxa_id,
      taxa_name: x.taxa_name,
      taxa_sname: x.taxa_sname,
      cto: x.cto
    }
  }
)

const technologyCache: GroupedCache<Technology, Selection, number> = new GroupedCache(
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

async function getOrganimsByModificationId(modificationId: number): Promise<Organism[]> {
  const organimIds = new Set<number>()
  for (const item of await selectionsCache.getData()) {
    if (item.modification_id === modificationId) {
      organimIds.add(item.organism_id)
    }
  }
  return (await organismCache.getData()).filter((x) => x.organism_id in organimIds)
}

async function getTechnologyByModificationIdAndOrganimId(
  modificationId: number,
  organismId: number
) {
  const technologyIds = new Set<number>()
  for (const item of await selectionsCache.getData()) {
    if (item.modification_id === modificationId && item.organism_id === organismId) {
      technologyIds.add(item.technology_id)
    }
  }
  return (await technologyCache.getData()).filter((x) => x.technology_id in technologyIds)
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
      x.technology_id in technologyIds
  )
}

async function getSelectionsByOrganismId(organismId: number): Promise<Selection[]> {
  return (await selectionsCache.getData()).filter((x) => x.organism_id === organismId)
}

async function getTechnologiesByIds(technologyIds: number[]): Promise<Technology[]> {
  const canidates = (await technologyCache.getData()).filter(
    (x) => x.technology_id in technologyIds
  )
  if (canidates.length > 0) {
    return canidates
  } else {
    throw Error(
      `Wanted ONE technologies with IDs ${technologyIds} but got 0! That should never happen!`
    )
  }
}

export {
  type Selection,
  type ModificationType,
  type Organism,
  type Technology,
  selectionsCache,
  modificationTypeCache,
  organismCache,
  technologyCache,
  getOrganimsByModificationId,
  getTechnologyByModificationIdAndOrganimId,
  getSelectionsByOrganismId,
  getSelectionsByIds,
  getTechnologiesByIds
}
