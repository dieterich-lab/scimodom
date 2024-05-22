import { DIALOG } from '@/stores/DialogState'

async function handleRequestWithErrorReporting(request, failureMessage, dialogState) {
  let extraInfo = ''
  try {
    const response = await request
    if (response.status === 200) {
      return response.data
    }
    extraInfo = getErrorMessageFromResponse(response)
  } catch (err) {
    extraInfo = getErrorMessageFromException(err)
  }
  const finalError = `${failureMessage}: ${extraInfo}`
  console.log(finalError)
  dialogState.state = DIALOG.ALERT
  dialogState.message = finalError
  throw new Error(finalError)
}

function getErrorMessageFromResponse(response) {
  let message = `HTTP status ${response.status}`
  for (let field of ['message', 'msg']) {
    if (field in response.data) {
      message = `${message} - ${response.data[field]}`
    }
  }
  return message
}

function getErrorMessageFromException(err) {
  try {
    return getErrorMessageFromResponse(err.response)
  } catch (e) {
    return err.toString()
  }
}

export {
  handleRequestWithErrorReporting,
  getErrorMessageFromResponse,
  getErrorMessageFromException
}
