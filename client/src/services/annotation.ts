import { Cache } from '@/utils/cache'
import { handleRequest, HTTP } from '@/services/API'

/**
 * An annotation in use, with the assembly it is in the coordinate
 * system of and where the release it comes from is served.
 *
 * `browse_url` is the page of the source for this organism at that
 * release, built server-side: nothing here knows the URL layout of
 * a source, nor which release is installed. It is null for a source
 * that serves no browsable page for a release, cf.
 * GET /catalogs/annotations.
 */
interface Annotation {
  id: number
  source: string
  release: number
  archive: string | null
  browse_url: string | null
  assembly_id: number
  assembly_name: string
  taxa_id: number
  taxa_name: string
}

// cf. scimodom.utils.specs.enums.AnnotationSource. The cache holds
// every source; only the lookups below are Ensembl-specific
const ENSEMBL = 'ensembl'

class AnnotationCache extends Cache<Annotation[]> {
  async getPromise(): Promise<Annotation[]> {
    // through handleRequest, so a failure is a RequestError that
    // trashRequestErrors recognises: a consumer that can do without
    // the annotations says so, cf. HomeRelease and SearchView
    return await handleRequest(
      HTTP.get<Annotation[]>('/catalogs/annotations'),
      'Failed to load annotations'
    )
  }
}

const annotationCache = new AnnotationCache()

async function getEnsemblAnnotation(taxaId: number): Promise<Annotation | undefined> {
  return (await annotationCache.getData()).find((x) => x.taxa_id === taxaId && x.source === ENSEMBL)
}

/**
 * The Ensembl page to build record links from, or null if this
 * organism has no Ensembl annotation.
 */
async function getEnsemblBrowseUrl(taxaId: number): Promise<string | null> {
  return (await getEnsemblAnnotation(taxaId))?.browse_url ?? null
}

export { type Annotation, annotationCache, getEnsemblBrowseUrl }
