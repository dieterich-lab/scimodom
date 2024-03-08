<template>
  <div
    class="flex flex-col px-8 py-8 gap-4"
    style="
      border-radius: 12px;
      background-image: radial-gradient(
        circle at center,
        rgb(var(--primary-600)),
        rgb(var(--primary-500)),
        rgb(var(--primary-400))
      );
    "
  >
    <slot></slot>
  </div>
</template>
