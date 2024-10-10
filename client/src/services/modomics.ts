import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface Modomics {
  id: string
  reference_id: number
  name: string
  short_name: string
  moiety: string
}

class ModomicsCache extends Cache<Modomics[]> {
  async getPromise(): Promise<Modomics[]> {
    try {
      const response = await HTTP.get('/modomics')
      return response.data as Modomics[]
    } catch (err) {
      console.log(`Failed to fetch all Modomics: ${err}`)
      throw err
    }
  }
}

const modomicsCache = new ModomicsCache()

export { type Modomics, modomicsCache }
