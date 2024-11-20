import { defineStore } from 'pinia'
import { HTTPSecure, handleRequest } from '@/services/API'

enum UPLOAD_STATE {
  WAITING = 'WAITING',
  RUNNING = 'RUNNING',
  DONE = 'DONE',
  FAILED = 'FAILED'
}

const MAX_PARALLEL_UPLOADS = 1
const WAIT_UNTIL_EXPIRING_SUCCESSFUL_JOB_MS = 10 * 60 * 1000

const MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024
const MAX_FILE_SIZE_ERROR = `File to large (max ${MAX_FILE_SIZE} bytes)`

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

class ScheduledUpload {
  public readonly id: number
  public state: UPLOAD_STATE
  public readonly file: File
  public readonly url: string
  public info: string
  public errorMessage: string
  public readonly removeCallback: (x: ScheduledUpload) => void

  constructor(file: File, url: string, info: string, removeCallback: (x: ScheduledUpload) => void) {
    const randomNumber = new Uint32Array(1)
    crypto.getRandomValues(randomNumber)
    this.id = randomNumber[0]
    this.file = file
    this.url = url
    this.info = info
    this.state = UPLOAD_STATE.WAITING
    this.errorMessage = ''
    this.removeCallback = removeCallback
    if (file.size > MAX_FILE_SIZE) {
      this.state = UPLOAD_STATE.FAILED
      this.errorMessage = MAX_FILE_SIZE_ERROR
    }
  }

  async run() {
    this.state = UPLOAD_STATE.RUNNING
    try {
      await handleRequest(HTTPSecure.post(this.url, this.file))
      this.state = UPLOAD_STATE.DONE
    } catch (err) {
      this.errorMessage = `${err}`
      this.state = UPLOAD_STATE.FAILED
    }
  }

  remove() {
    this.removeCallback(this)
  }
}

const useUploadManager = defineStore('uploadManager', {
  state: () => {
    return { uploads: [] as ScheduledUpload[] }
  },
  actions: {
    schedule(file: File, post_request: string, info: string) {
      const removeCallback = (x: ScheduledUpload) => {
        this.remove(x)
      }
      const newUpload = new ScheduledUpload(file, post_request, info, removeCallback)
      this.uploads = [...this.uploads, newUpload]
      this.tryToStartUpload()
    },
    remove(upload: ScheduledUpload) {
      this.uploads = this.uploads.filter((x) => x.id !== upload.id)
    },
    tryToStartUpload() {
      const running_uploads = this.uploads.filter((x) => x.state === UPLOAD_STATE.RUNNING)
      if (running_uploads.length >= MAX_PARALLEL_UPLOADS) {
        return
      }
      const waiting_uploads = this.uploads.filter((x) => x.state === UPLOAD_STATE.WAITING)
      if (waiting_uploads.length > 0) {
        const next_upload = waiting_uploads[0]
        void this.doUpload(next_upload)
      }
    },
    async doUpload(upload: ScheduledUpload) {
      try {
        await upload.run()
      } finally {
        this.tryToStartUpload()
      }
      if (upload.state === UPLOAD_STATE.DONE) {
        await sleep(WAIT_UNTIL_EXPIRING_SUCCESSFUL_JOB_MS)
        this.remove(upload)
      }
    }
  }
})

export { useUploadManager, ScheduledUpload, UPLOAD_STATE }
