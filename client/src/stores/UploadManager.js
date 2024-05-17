import { defineStore } from 'pinia'
import { HTTPSecure } from '@/services/API'
import { getErrorMessageFromException, getErrorMessageFromResponse } from '@/utils/request'

const UPLOAD_STATE = Object.freeze({
  WAITING: Symbol('WAITING'),
  RUNNING: Symbol('RUNNING'),
  DONE: Symbol('DONE'),
  FAILED: Symbol('FAILED')
})

const MAX_PARALLEL_UPLOADS = 1
const WAIT_UNTIL_EXPIRING_SUCCESSFUL_JOB_MS = 10 * 60 * 1000

const MAX_FILE_SIZE = 1024 * 1024 * 1024
const MAX_FILE_SIZE_ERROR = `File to large (max ${MAX_FILE_SIZE} bytes)`

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

class ScheduledUpload {
  constructor(file, url, info, removeCallback) {
    let randomNumber = new Uint32Array(1)
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
      const response = await HTTPSecure.post(this.url, this.file)
      if (response.status === 200) {
        this.state = UPLOAD_STATE.DONE
        return
      }
      this.errorMessage = getErrorMessageFromResponse(response)
    } catch (err) {
      this.errorMessage = getErrorMessageFromException(err)
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
    schedule(file, post_request, info) {
      const removeCallback = (x) => {
        this.remove(x)
      }
      const newUpload = new ScheduledUpload(file, post_request, info, removeCallback)
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
