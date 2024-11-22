import { handleRequestWithErrorReporting, HTTP } from '@/services/API'
import type { DialogStateStore } from '@/stores/DialogState'

interface Assembly {
  id: number
  name: string
}

async function getAssembliesByTaxaId(
  taxaId: number,
  dialogState: DialogStateStore
): Promise<Assembly[]> {
  return await handleRequestWithErrorReporting<Assembly[]>(
    HTTP.get(`/assembly/${taxaId}`),
    `Failed to load assemblies for Taxa ID ${taxaId}`,
    dialogState
  )
}

export { type Assembly, getAssembliesByTaxaId }
