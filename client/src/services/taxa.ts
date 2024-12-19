import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

// interface also used for selection
interface Taxa {
  domain: string
  kingdom: string | null
  phylum: string | null
  taxa_id: number
  taxa_name: string
  taxa_sname: string
}

class TaxaCache extends Cache<Taxa[]> {
  async getPromise(): Promise<Taxa[]> {
    try {
      const response = await HTTP.get('/taxa')
      return response.data as Taxa[]
    } catch (err) {
      console.log(`Failed to fetch Taxa: ${err}`)
      throw err
    }
  }
}

const taxaCache = new TaxaCache()

export { type Taxa, taxaCache }
