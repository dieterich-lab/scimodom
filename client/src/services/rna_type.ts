import { HTTP } from '@/services/API'
import { Cache } from '@/utils/cache'

interface RnaType {
  id: string
  label: string
}

class RnaTypeCache extends Cache<RnaType[]> {
  async getPromise(): Promise<RnaType[]> {
    try {
      const response = await HTTP.get('/rna_types')
      return response.data as RnaType[]
    } catch (err) {
      console.log(`Failed to fetch all RNA types: ${err}`)
      throw err
    }
  }
}

const rnaTypeCache = new RnaTypeCache()

export { type RnaType, rnaTypeCache }
