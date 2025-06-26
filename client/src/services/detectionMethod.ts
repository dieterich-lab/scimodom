import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface DetectionMethod {
  id: string
  cls: string
  meth: string
}

class DetectionMethodCache extends Cache<DetectionMethod[]> {
  async getPromise(): Promise<DetectionMethod[]> {
    try {
      const response = await HTTP.get('/catalogs/methods')
      return response.data as DetectionMethod[]
    } catch (err) {
      console.log(`Failed to fetch /catalogs/methods: ${err}`)
      throw err
    }
  }
}

const detectionMethodCache = new DetectionMethodCache()

export { type DetectionMethod, detectionMethodCache }
