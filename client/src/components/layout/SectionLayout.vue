<script setup>
const props = defineProps({
  framed: {
    type: Boolean,
    default: false
  },
  secondary: {
    type: Boolean,
    default: false
  },
  container: String
})

function sectionClass() {
  let classes = []
  if (props.secondary) classes.push('section--secondary')
  return classes
}
function sectionClassInner() {
  let classes = []
  if (props.framed) {
    classes.push('container--framed')
  }
  if (props.container) {
    classes.push('container-' + props.container)
  }
  return classes
}
</script>

<template>
  <section class="section" :class="sectionClass()">
    <div class="section--inner container mx-auto" :class="sectionClassInner()">
      <slot></slot>
    </div>
  </section>
</template>

<style scoped>
.section {
  padding: calc(2% + 25px) 0;
  position: relative;
  width: 100%;
  flex: 1;
}
.section--secondary {
  background-color: #f7f9f8;
  border-top: 1px solid #e2ecec;
  border-bottom: 1px solid #e2ecec;
}
.section--secondary + .section--secondary {
  border-top-color: transparent;
  margin-top: -1px;
}
.section--inner {
  position: relative;
  z-index: 2;
}
</style>
