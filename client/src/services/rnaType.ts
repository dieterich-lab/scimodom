import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface RnaType {
  id: string
  label: string
}

class RnaTypeCache extends Cache<RnaType[]> {
  async getPromise(): Promise<RnaType[]> {
    try {
      const response = await HTTP.get('/catalogs/rna-types')
      return response.data as RnaType[]
    } catch (err) {
      console.log(`Failed to fetch /catalogs/rna-types: ${err}`)
      throw err
    }
  }
}

const rnaTypeCache = new RnaTypeCache()

export { type RnaType, rnaTypeCache }
