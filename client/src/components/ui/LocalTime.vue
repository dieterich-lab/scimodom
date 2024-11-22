<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    epoch?: number
    showTime?: boolean
  }>(),
  {
    showTime: true
  }
)

function pad(x: number) {
  if (x < 10) {
    return '0' + x
  } else {
    return '' + x
  }
}

let formattedDate = ''

if (props.epoch) {
  const d = new Date(0)
  d.setUTCSeconds(props.epoch)
  const yyyy = d.getFullYear()
  const mm = pad(d.getMonth() + 1)
  const dd = pad(
    d.getDate()
  ) /* Really getDate? not getDay or getDayOfMonth? Yes - really getDate! */
  let time = ''
  if (props.showTime) {
    const HH = pad(d.getHours())
    const MM = pad(d.getMinutes())
    const SS = pad(d.getSeconds())
    time = ` ${HH}:${MM}:${SS}`
  }

  formattedDate = `${yyyy}-${mm}-${dd}${time}`
}
</script>
<template>
  {{ formattedDate }}
</template>
