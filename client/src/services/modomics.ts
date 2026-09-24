import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface Modomics {
  id: string
  modomics_sname: string
}

class ModomicsCache extends Cache<Modomics[]> {
  async getPromise(): Promise<Modomics[]> {
    try {
      const response = await HTTP.get('/catalogs/modomics')
      return response.data as Modomics[]
    } catch (err) {
      console.log(`Failed to fetch /catalogs/modomics: ${err}`)
      throw err
    }
  }
}

const modomicsCache = new ModomicsCache()

export { type Modomics, modomicsCache }
