import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

// interface also used for selection
interface Taxa {
  domain: string
  kingdom: string | null
  phylum?: string | null
  taxa_id: number
  taxa_name: string
  taxa_short_name: string
}

class TaxaCache extends Cache<Taxa[]> {
  async getPromise(): Promise<Taxa[]> {
    const response = await HTTP.get<Taxa[]>('/catalogs/taxa')
    return response.data
  }
}

const taxaCache = new TaxaCache()

export { type Taxa, taxaCache }
