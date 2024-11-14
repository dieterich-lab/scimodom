import { DIALOG, type DialogStateStore } from '@/stores/DialogState'
import type { AxiosResponse } from 'axios'

async function handleRequestWithErrorReporting<T>(
  request: Promise<AxiosResponse>,
  failureMessage: string,
  dialogState: DialogStateStore,
  hideHttpStatus: boolean = false
): Promise<T> {
  let extraInfo = ''
  try {
    const response = await request
    if (response.status === 200) {
      return response.data as T
    }
    extraInfo = getErrorMessageFromResponse(response, hideHttpStatus)
  } catch (err) {
    extraInfo = getErrorMessageFromException(err as object, hideHttpStatus)
  }
  const finalError = `${failureMessage}: ${extraInfo}`
  dialogState.state = DIALOG.ERROR_ALERT
  dialogState.message = finalError
  throw new Error(finalError)
}

function getErrorMessageFromResponse(response: AxiosResponse, hideHttpStatus: boolean = false) {
  let message = `HTTP status ${response.status}`
  for (const field of ['message', 'msg']) {
    if (field in response.data) {
      if (hideHttpStatus) {
        message = response.data[field]
      } else {
        message = `${message} - ${response.data[field]}`
      }
    }
  }
  return message
}

function getErrorMessageFromException(err: object, hideHttpStatus: boolean = false): string {
  if ('response' in err) {
    return getErrorMessageFromResponse(err.response as AxiosResponse, hideHttpStatus)
  } else {
    return err.toString()
  }
}

export {
  handleRequestWithErrorReporting,
  getErrorMessageFromResponse,
  getErrorMessageFromException
}
