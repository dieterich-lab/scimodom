import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

interface Assembly {
  id: number
  name: string
}

async function getAssembliesByTaxaId(
  taxaId: number,
  dialogState: DialogStateStore
): Promise<Assembly[]> {
  return await handleRequestWithErrorReporting<Assembly[]>(
    HTTP.get(`/catalogs/taxa/${taxaId}/assemblies`),
    `Failed to load Assembly: ${taxaId}`,
    dialogState
  )
}

export { type Assembly, getAssembliesByTaxaId }
