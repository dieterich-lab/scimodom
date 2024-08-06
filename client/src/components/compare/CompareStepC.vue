<script setup>
const model = defineModel()
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-row">
      <div class="w-1/2">
        <RadioButton v-model="model" inputId="criteria1" name="step3" value="intersect-true" />
        <label for="criteria1" class="ml-2">
          <span class="inline font-bold">Intersection</span>
        </label>
        <p class="mt-0 ml-8 text-sm">
          Search for overlaps between <span class="font-semibold">1</span> and
          <span class="font-semibold">2</span> on the same strand.
        </p>
      </div>
      <div class="w-1/2">
        <RadioButton v-model="model" inputId="criteria2" name="step3" value="intersect-false" />
        <label for="criteria3" class="ml-2">
          <span class="inline font-bold">Intersection (strand-unaware)</span>
        </label>
        <p class="mt-0 ml-8 text-sm">
          Search for overlaps between <span class="font-semibold">1</span> and
          <span class="font-semibold">2</span> without respect to strand.
        </p>
      </div>
    </div>
    <div class="flex flex-row">
      <div class="w-1/2">
        <RadioButton v-model="model" inputId="criteria3" name="step3" value="closest-true" />
        <label for="criteria3" class="ml-2">
          <span class="inline font-bold">Closest</span>
        </label>
        <p class="mt-0 ml-8 text-sm">
          Search for closest non-overlaps in <span class="font-semibold">2</span> (wrt.
          <span class="font-semibold">1</span>) on the same strand.
        </p>
      </div>
      <div class="w-1/2">
        <RadioButton v-model="model" inputId="criteria4" name="step3" value="closest-false" />
        <label for="criteria3" class="ml-2">
          <span class="inline font-bold">Closest (strand-unaware)</span>
        </label>
        <p class="mt-0 ml-8 text-sm">
          Search for closest non-overlaps in <span class="font-semibold">2</span> (wrt.
          <span class="font-semibold">1</span>) without respect to strand.
        </p>
      </div>
    </div>
    <div class="flex flex-row">
      <div class="w-1/2">
        <RadioButton v-model="model" inputId="criteria5" name="step3" value="subtract-true" />
        <label for="criteria5" class="ml-2">
          <span class="inline font-bold">Difference</span>
        </label>
        <p class="mt-0 ml-8 text-sm">
          Search for strict non-overlaps in reference (modifications in
          <span class="font-semibold">1</span> but not in <span class="font-semibold">2</span>) on
          the same strand.
        </p>
      </div>
      <div class="w-1/2">
        <RadioButton v-model="model" inputId="criteria6" name="step3" value="subtract-false" />
        <label for="criteria6" class="ml-2">
          <span class="inline font-bold">Difference (strand-unaware)</span>
        </label>
        <p class="mt-0 ml-8 text-sm">
          Search for strict non-overlaps in reference (modifications in
          <span class="font-semibold">1</span> but not in <span class="font-semibold">2</span>)
          without respect to strand.
        </p>
      </div>
    </div>
  </div>
</template>
