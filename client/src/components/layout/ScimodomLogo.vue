<script setup lang="ts">
import Logo from '@/assets/images/scimodom-logo.svg'
</script>

<template>
  <div>
    <RouterLink to="/" title="Home">
      <Logo
        class="max-w-[155px] h-auto -mt-0.5 mr-6 dark:filter dark:grayscale dark:invert"
        alt="https://scimodom.dieterichlab.org"
      />
    </RouterLink>
  </div>
</template>
