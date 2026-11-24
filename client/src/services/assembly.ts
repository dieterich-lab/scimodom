import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

/**
 * What an assembly was installed from, null if it is not known:
 * any assembly that is not current, and any current assembly
 * installed before the manifest existed.
 */
interface AssemblySource {
  provider: string
  release: number
  archive: string | null
}

/**
 * An installed assembly, cf. GET /catalogs/assemblies.
 *
 * NOTE: every assembly of the organism is reported, including those
 * kept only to lift over from, which is what `current`
 * distinguishes. A dataset may be uploaded for any of them.
 */
interface Assembly {
  id: number
  name: string
  alt_name: string | null
  taxa_id: number
  taxa_name: string
  current: boolean
  source: AssemblySource | null
}

async function getAssembliesByTaxaId(
  taxaId: number,
  dialogState: DialogStateStore
): Promise<Assembly[]> {
  return await handleRequestWithErrorReporting(
    HTTP.get<Assembly[]>('/catalogs/assemblies', { params: { taxaId } }),
    `Failed to load Assembly: ${taxaId}`,
    dialogState
  )
}

export { type Assembly, type AssemblySource, getAssembliesByTaxaId }
