import { Cache } from '@/utils/cache'
import { HTTP } from '@/services/API'

interface DetectionMethod {
  id: string
  cls: string
  meth: string
}

class DetectionMethodCache extends Cache<DetectionMethod[]> {
  async getPromise(): Promise<DetectionMethod[]> {
    const response = await HTTP.get<DetectionMethod[]>('/catalogs/methods')
    return response.data
  }
}

const detectionMethodCache = new DetectionMethodCache()

export { type DetectionMethod, detectionMethodCache }
