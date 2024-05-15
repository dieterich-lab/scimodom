import { DIALOG } from '@/stores/DialogState'

async function handleRequestWithErrorReporting(request, failureMessage, dialogState) {
  let extraInfo = ''
  try {
    const response = await request
    if (response.status === 200) {
      return response.data
    }
    extraInfo = `HTTP status ${response.status}`
    for (let field of ['message', 'msg']) {
      if (response.data.hasOwn(field)) {
        extraInfo = `${extraInfo} - ${response.data[field]}`
      }
    }
  } catch (err) {
    extraInfo = err.toString()
  }
  const finalError = `${failureMessage}: ${extraInfo}`
  console.log(finalError)
  dialogState.state = DIALOG.ALERT
  dialogState.message = finalError
  throw new Error(finalError)
}

export { handleRequestWithErrorReporting }
