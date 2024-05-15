import { defineStore } from 'pinia'
import { HTTPSecure } from '@/services/API'

const UPLOAD_STATE = Object.freeze({
  WAITING: Symbol('WAITING'),
  RUNNING: Symbol('RUNNING'),
  DONE: Symbol('DONE'),
  FAILED: Symbol('FAILED')
})

const MAX_PARALLEL_UPLOADS = 1
const WAIT_UNTIL_EXPIRING_SUCCESSFUL_JOB_MS = 10 * 60 * 1000

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

class ScheduledUpload {
  constructor(file, url, removeCallback) {
    let randomNumber = new Uint32Array(1)
    crypto.getRandomValues(randomNumber)
    this.id = randomNumber[0]
    this.file = file
    this.url = url
    this.state = UPLOAD_STATE.WAITING
    this.errorMessage = ''
    this.removeCallback = removeCallback
  }

  async run() {
    this.state = UPLOAD_STATE.RUNNING
    try {
      const response = await HTTPSecure.post(this.url, this.file)
      if (response.status === 200) {
        this.state = UPLOAD_STATE.DONE
        return
      }
      try {
        this.errorMessage = `Upload failed with HTTP status ${response.status}: ${response.data.message}`
      } catch {
        this.errorMessage = `Upload failed with HTTP status ${response.status}`
      }
    } catch (err) {
      this.errorMessage = err.toString()
    }
    this.state = UPLOAD_STATE.FAILED
  }

  remove() {
    this.removeCallback(this)
  }
}

const useUploadManager = defineStore('uploadManager', {
  state: () => {
    return {
      uploads: [],
      callback: null
    }
  },
  actions: {
    schedule(file, post_request) {
      const removeCallback = (x) => {
        this.remove(x)
      }
      const newUpload = new ScheduledUpload(file, post_request, removeCallback)
      this.uploads = [...this.uploads, newUpload]
      this.tryToStartUpload()
    },
    remove(upload) {
      this.uploads = this.uploads.filter((x) => x.id !== upload.id)
    },
    tryToStartUpload() {
      const running_uploads = this.uploads.filter((x) => x.state === UPLOAD_STATE.RUNNING)
      if (running_uploads.length >= MAX_PARALLEL_UPLOADS) {
        return
      }
      const waiting_uploads = this.uploads.filter((x) => x.state === UPLOAD_STATE.WAITING)
      if (waiting_uploads.length > 0) {
        void this.doUpload(waiting_uploads[0])
      }
    },
    async doUpload(upload) {
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