import { test, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUploadManager, ScheduledUpload, UPLOAD_STATE } from '@/stores/UploadManager'
import { HTTPSecure, handleRequest } from '@/services/API'
import type { ucs2 } from 'punycode'

vi.mock('@/services/API', () => ({
  HTTPSecure: { post: vi.fn() },
  handleRequest: vi.fn()
}))

const mockedPost = vi.mocked(HTTPSecure.post)
const mockedHandle = vi.mocked(handleRequest)

// use deterministic so `remove` assertions are stable
let nextId = 0
beforeEach(() => {
  nextId = 0
  vi.spyOn(crypto, 'getRandomValues').mockImplementation((array) => {
    ;(array as Uint32Array)[0] = nextId++
    return array
  })

  mockedPost.mockReset()
  mockedHandle.mockReset()
  mockedHandle.mockResolvedValue(undefined)

  setActivePinia(createPinia())
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

function makeFile(name = 'a.bedrmod', size = 100): File {
  const file = new File(['x'], name, { type: 'application/octet-stream' })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

test('ScheduledUpload starts in WAITING with an empty error message', () => {
  const upload = new ScheduledUpload(makeFile(), '/uploads', 'info', () => {})

  expect(upload.state).toBe(UPLOAD_STATE.WAITING)
  expect(upload.errorMessage).toBe('')
  expect(upload.info).toBe('info')
  expect(upload.url).toBe('/uploads')
})

test('ScheduledUpload marks an oversize file as FAILED at construction', () => {
  const upload = new ScheduledUpload(
    makeFile('big.bedrmod', 2 * 1024 * 1024 * 1024 + 1),
    '/uploads',
    'info',
    () => {}
  )

  expect(upload.state).toBe(UPLOAD_STATE.FAILED)
  expect(upload.errorMessage).toEqual('File too large (max. 2147483648 bytes)')
})

test('ScheduledUpload.run moves WAITING -> RUNNING -> DONE on success', async () => {
  const upload = new ScheduledUpload(makeFile(), '/uploads', 'info', () => {})

  const promise = upload.run()
  expect(upload.state).toBe(UPLOAD_STATE.RUNNING)

  await promise
  expect(upload.state).toBe(UPLOAD_STATE.DONE)
  expect(mockedPost).toHaveBeenCalledWith('/uploads', upload.file)
})

test('ScheduledUpload.run moves RUNNING -> FAILED and records the error', async () => {
  mockedHandle.mockRejectedValueOnce(new Error('network down'))
  const upload = new ScheduledUpload(makeFile(), '/uploads', 'info', () => {})

  await upload.run()

  expect(upload.state).toBe(UPLOAD_STATE.FAILED)
  expect(upload.errorMessage).toBe('Error: network down')
})

test('ScheduledUpload.remove calls the supplied callback with itself', () => {
  const callback = vi.fn()
  const upload = new ScheduledUpload(makeFile(), '/uploads', 'info', callback)

  upload.remove()

  expect(callback).toHaveBeenCalledWith(upload)
})

// store - parallel limit

test('schedule adds an upload and starts it immediately', async () => {
  const store = useUploadManager()

  store.schedule(makeFile('a.bedrmod'), '/uploads', 'a')

  expect(store.uploads).toHaveLength(1)
  expect(store.uploads[0].state).toBe(UPLOAD_STATE.RUNNING)
  expect(mockedPost).toHaveBeenCalledTimes(1)

  await vi.runAllTimersAsync()
})

test('schedule queues a second upload while one is running', async () => {
  const resolvers: Array<() => void> = []
  mockedHandle.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        resolvers.push(resolve)
      })
  )

  const store = useUploadManager()

  store.schedule(makeFile('a.bedrmod'), '/uploads', 'a')
  store.schedule(makeFile('b.bedrmod'), '/uploads', 'b')

  // a is running, b is queued, and only one POST has been issued.
  expect(store.uploads).toHaveLength(2)
  expect(store.uploads[0].state).toBe(UPLOAD_STATE.RUNNING)
  expect(store.uploads[1].state).toBe(UPLOAD_STATE.WAITING)
  expect(mockedPost).toHaveBeenCalledTimes(1)
  expect(resolvers).toHaveLength(1)

  // Finish a; b should start.
  resolvers[0]()
  await vi.advanceTimersByTimeAsync(0)

  expect(store.uploads[0].state).toBe(UPLOAD_STATE.DONE)
  expect(store.uploads[1].state).toBe(UPLOAD_STATE.RUNNING)
  expect(mockedPost).toHaveBeenCalledTimes(2)
  expect(resolvers).toHaveLength(2)

  // Finish b so no timer is left pending.
  resolvers[1]()
  await vi.advanceTimersByTimeAsync(0)

  expect(store.uploads[1].state).toBe(UPLOAD_STATE.DONE)
})

test('the parallel limit starts the queued upload only after the first finishes', async () => {
  let resolveFirst: () => void = () => {}
  mockedHandle.mockImplementationOnce(
    () => new Promise<void>((resolve) => (resolveFirst = resolve))
  )
  const store = useUploadManager()

  store.schedule(makeFile('a.bedrmod'), '/uploads', 'a')
  store.schedule(makeFile('b.bedrmod'), '/uploads', 'b')

  expect(mockedPost).toHaveBeenCalledTimes(1)

  resolveFirst()
  await vi.advanceTimersByTimeAsync(0)

  expect(mockedPost).toHaveBeenCalledTimes(2)
  expect(store.uploads[0].state).toBe(UPLOAD_STATE.DONE)
  expect(store.uploads[1].state).toBe(UPLOAD_STATE.DONE)
})

test('a failed upload does not block the next one', async () => {
  mockedHandle.mockRejectedValueOnce(new Error('boom'))
  const store = useUploadManager()

  store.schedule(makeFile('a.bedrmod'), '/uploads', 'a')
  store.schedule(makeFile('b.bedrmod'), '/uploads', 'b')

  await vi.advanceTimersByTimeAsync(0)

  expect(store.uploads).toHaveLength(2)
  expect(store.uploads[0].state).toBe(UPLOAD_STATE.FAILED)
  expect(store.uploads[1].state).toBe(UPLOAD_STATE.DONE)
})

// store removal

test('remove drops the upload from the list', async () => {
  const store = useUploadManager()
  store.schedule(makeFile('a.bedrmod'), '/uploads', 'a')

  const upload = store.uploads[0]
  store.remove(upload)

  expect(store.uploads).toHaveLength(0)

  await vi.runAllTimersAsync()
})

test('a successful upload is removed automatically after the expiry delay', async () => {
  const store = useUploadManager()
  store.schedule(makeFile('a.bedrmod'), '/uploads', 'a')

  // let the upload complete, but do not advance past the expiry window...
  await vi.advanceTimersByTimeAsync(0)
  expect(store.uploads).toHaveLength(1)
  expect(store.uploads[0].state).toBe(UPLOAD_STATE.DONE)

  // ... now advance
  // the scheduled sleep resolves and doUpload calls remove()
  await vi.advanceTimersByTimeAsync(10 * 60 * 1000 + 1)

  expect(store.uploads).toHaveLength(0)
})

test('a failed upload is NOT removed automatically', async () => {
  mockedHandle.mockRejectedValueOnce(new Error())
  const store = useUploadManager()
  store.schedule(makeFile('a.bedrmod'), '/uploads', 'a')

  await vi.runAllTimersAsync()
  await vi.advanceTimersByTimeAsync(10 * 60 * 1000 + 1)

  expect(store.uploads).toHaveLength(1)
  expect(store.uploads[0].state).toBe(UPLOAD_STATE.FAILED)
})

test('an oversize file is never posted and remains in the list', async () => {
  const store = useUploadManager()
  store.schedule(makeFile('big.bedrmod', 2 * 1024 * 1024 * 1024 + 1), '/uploads', 'big')

  await vi.runAllTimersAsync()

  expect(mockedPost).not.toHaveBeenCalled()
  expect(store.uploads).toHaveLength(1)
  expect(store.uploads[0].state).toBe(UPLOAD_STATE.FAILED)
})
