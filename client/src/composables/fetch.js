import { ref, watchEffect, toValue } from 'vue'
import { HTTP } from '@/services/API.js'

// export function useFetchOptions(url) {
//   const options = ref(null)
//   const errorFetchOpts = ref(null)

//   watchEffect(() => {
//     // reset state before fetching..
//     options.value = null
//     errorFetchOpts.value = null
//     // toValue() unwraps potential refs or getters
//     service
//       .getEndpoint(toValue(url))
//       .then(function (response) {
//         options.value = response.data
//       })
//       .catch((err) => {
//         errorFetchOpts.value = err
//       })
//   })
//   console.log('INSIDE', options)
//   return {options, errorFetchOpts}
// }

export function useFetchOptions(url) {
  const isLoading = ref(true)
  const options = ref(null)
  const errorFetchOpts = ref(null)

  const fetchOptions = async () => {
    isLoading.value = true
    try {
      await HTTP.get(toValue(url)).then(function (response) {
        options.value = response.data
      })
    } catch (err) {
      errorFetchOpts.value = err
    } finally {
      isLoading.value = false
    }
  }
  fetchOptions()
  return { options, errorFetchOpts }
}
