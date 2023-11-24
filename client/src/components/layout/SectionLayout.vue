<script setup>
const props = defineProps({
  dark: {
    type: Boolean,
    default: false
  },
  dots: {
    type: Boolean,
    default: false
  },
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
  if (props.dark) classes.push('section--dark')
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
    <div v-if="dots" class="section__dots-bg dots-bg" />
    <!-- <slot name="outer" /> -->
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
.section__dots-bg {
  height: 700px;
  max-width: 1500px;
  max-height: 100%;
  margin: 0 auto;
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  opacity: 1;
}
.section--inner {
  position: relative;
  z-index: 2;
}
.section--dark {
  color: #fff;
  background: #0d2538;
}
.section--dark p {
  color: currentColor;
}
.section--dark h1,
.section--dark h2,
.section--dark h3,
.section--dark h4,
.section--dark a {
  color: #fff;
}
</style>
