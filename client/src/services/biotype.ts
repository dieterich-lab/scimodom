import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTP } from '@/services/API'

async function getBioTypes(rnaType: string = '', dialogState: DialogStateStore): Promise<string[]> {
  return await handleRequestWithErrorReporting<string[]>(
    HTTP.get(`/biotypes/${rnaType ? rnaType : ''}`),
    'Failed to load biotypes',
    dialogState
  )
}

export { getBioTypes }
