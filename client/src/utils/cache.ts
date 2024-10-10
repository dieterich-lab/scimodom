const NO_SUCH_REVISION = -1

abstract class Cache<T> {
  private data: T | null
  private revision: number

  constructor() {
    this.data = null
    this.revision = 0
  }

  abstract getPromise(): Promise<T>

  public isUptodate(): boolean {
    return true
  }

  public async getData(refresh: boolean = false): Promise<Readonly<T>> {
    if (!this.isUptodate() || this.data === null || refresh) {
      const promise = this.getPromise()
      this.data = await promise
      this.revision += 1
    }
    return this.data
  }

  public getRevision() {
    return this.revision
  }
}

abstract class DependentCache<MASTER_T, MY_T> extends Cache<MY_T> {
  protected masterCache: Cache<MASTER_T>
  private masterCacheRevision: number

  constructor(masterCache: Cache<MASTER_T>) {
    super()
    this.masterCache = masterCache
    this.masterCacheRevision = NO_SUCH_REVISION
  }

  protected abstract convertMasterCache(data: MASTER_T): MY_T

  async getPromise(): Promise<MY_T> {
    const data = await this.masterCache.getData()
    this.masterCacheRevision = this.masterCache.getRevision()
    return this.convertMasterCache(data)
  }

  public isUptodate(): boolean {
    return this.masterCacheRevision === this.masterCache.getRevision()
  }
}

class ByKeyCache<KEY, VALUE> extends DependentCache<VALUE[], Map<KEY, VALUE>> {
  private readonly getKey: (v: VALUE) => KEY

  constructor(masterCache: Cache<VALUE[]>, getKey: (v: VALUE) => KEY) {
    super(masterCache)
    this.getKey = getKey
  }

  protected convertMasterCache(asList: readonly VALUE[]): Map<KEY, VALUE> {
    return asList.reduce((map, value) => {
      map.set(this.getKey(value), value)
      return map
    }, new Map<KEY, VALUE>())
  }
}

class GroupedCache<GROUPED_VALUES, RAW_VALUES extends GROUPED_VALUES, KEY> extends DependentCache<
  RAW_VALUES[],
  GROUPED_VALUES[]
> {
  private readonly getKey: (x: RAW_VALUES) => KEY
  private readonly getValue: (x: RAW_VALUES) => GROUPED_VALUES

  constructor(
    masterCache: Cache<RAW_VALUES[]>,
    getKey: (x: RAW_VALUES) => KEY,
    getValue: (x: RAW_VALUES) => GROUPED_VALUES
  ) {
    super(masterCache)
    this.getKey = getKey
    this.getValue = getValue
  }

  protected convertMasterCache(data: RAW_VALUES[]): GROUPED_VALUES[] {
    const byKey = new Map<KEY, GROUPED_VALUES>()
    for (const item of data) {
      const key: KEY = this.getKey(item)
      if (!byKey.has(key)) {
        byKey.set(key, this.getValue(item))
      }
    }
    return [...byKey.values()]
  }
}

export { Cache, DependentCache, ByKeyCache, GroupedCache }
