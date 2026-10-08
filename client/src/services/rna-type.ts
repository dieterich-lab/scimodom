import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface RnaType {
  id: string
  name: string
}

class RnaTypeCache extends Cache<RnaType[]> {
  async getPromise(): Promise<RnaType[]> {
    const response = await HTTP.get<RnaType[]>('/catalogs/rna-types')
    return response.data
  }
}

const rnaTypeCache = new RnaTypeCache()

export { type RnaType, rnaTypeCache }
