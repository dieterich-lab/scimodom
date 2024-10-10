import { test, expect } from 'vitest'
import { ByKeyCache, Cache, GroupedCache } from './cache'

interface TestValue {
  value: number
}

interface TestData extends TestValue {
  name: string
}

class TestCache extends Cache<TestData[]> {
  private readonly promise_fails: boolean
  public offset

  constructor(promise_fails: boolean = false) {
    super()
    this.promise_fails = promise_fails
    this.offset = 0
  }

  getPromise(): Promise<TestData[]> {
    if (this.promise_fails) {
      return Promise.reject('Failure')
    } else {
      return Promise.resolve([
        { name: 'a', value: 1 + this.offset },
        { name: 'b', value: 2.5 + this.offset },
        { name: 'c', value: 1 + this.offset }
      ])
    }
  }
}

test('Cache', async () => {
  const c = new TestCache()
  const data1 = await c.getData()
  expect(data1[0].value).toBe(1)
  expect(data1.length).toBe(3)
  const data2 = await c.getData()
  expect(data2[0].value).toBe(1)
})

test('ByKeyCache', async () => {
  const cache = new TestCache()
  const byKeyCache = new ByKeyCache(cache, (v) => v.name)
  const data1 = await byKeyCache.getData()
  expect(data1.get('a')?.value).toBe(1)
  expect(byKeyCache.getRevision()).toBe(1)
  const data2 = await byKeyCache.getData()
  expect(data2.get('b')?.value).toBe(2.5)
  expect(byKeyCache.getRevision()).toBe(1)

  cache.offset = 1
  await cache.getData(true)
  expect(cache.getRevision()).toBe(2)
  const data3 = await byKeyCache.getData()
  expect(byKeyCache.getRevision()).toBe(2)
  expect(data3.get('a')?.value).toBe(2)
})

test('GroupedCache', async () => {
  const cache = new TestCache()
  const groupedCache: GroupedCache<TestValue, TestData, number> = new GroupedCache(
    cache,
    (x) => x.value,
    (x) => {
      return { value: x.value }
    }
  )
  const data1 = await groupedCache.getData()
  expect(data1.length).toBe(2)
  expect(data1).toStrictEqual([{ value: 1 }, { value: 2.5 }])

  cache.offset = 1
  await cache.getData(true)
  const data2 = await groupedCache.getData()
  expect(data2).toStrictEqual([{ value: 2 }, { value: 3.5 }])
})
