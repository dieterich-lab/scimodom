import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface Modomics {
  id: string
  modomics_short_name: string
}

class ModomicsCache extends Cache<Modomics[]> {
  async getPromise(): Promise<Modomics[]> {
    const response = await HTTP.get<Modomics[]>('/catalogs/modomics')
    return response.data
  }
}

const modomicsCache = new ModomicsCache()

export { type Modomics, modomicsCache }
