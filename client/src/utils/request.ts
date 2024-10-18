import { DIALOG, type DialogStateStore } from '@/stores/DialogState'
import type { AxiosResponse } from 'axios'

async function handleRequestWithErrorReporting<T>(
  request: Promise<AxiosResponse>,
  failureMessage: string,
  dialogState: DialogStateStore
): Promise<T> {
  let extraInfo = ''
  try {
    const response = await request
    if (response.status === 200) {
      return response.data as T
    }
    extraInfo = getErrorMessageFromResponse(response)
  } catch (err) {
    extraInfo = getErrorMessageFromException(err as object)
  }
  const finalError = `${failureMessage}: ${extraInfo}`
  console.log(finalError)
  dialogState.state = DIALOG.ALERT
  dialogState.message = finalError
  throw new Error(finalError)
}

function getErrorMessageFromResponse(response: AxiosResponse) {
  let message = `HTTP status ${response.status}`
  for (const field of ['message', 'msg']) {
    if (field in response.data) {
      message = `${message} - ${response.data[field]}`
    }
  }
  return message
}

function getErrorMessageFromException(err: object): string {
  if ('response' in err) {
    return getErrorMessageFromResponse(err.response as AxiosResponse)
  } else {
    return err.toString()
  }
}

export {
  handleRequestWithErrorReporting,
  getErrorMessageFromResponse,
  getErrorMessageFromException
}
