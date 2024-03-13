<script setup>
import { useForm } from 'vee-validate'

// use yup
function required(value) {
  return value ? true : 'This field is required'
}

const { defineField, handleSubmit, errors } = useForm({
  validationSchema: {
    title: required
  }
})
const [title, titleProps] = defineField('title')
const onSubmit = handleSubmit((values) => {
  // Submit to API
  console.log(values)
})
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1
        class="font-ham mb-4 text-3xl font-extrabold text-gray-900 dark:text-white/80 md:text-5xl lg:text-6xl"
      >
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
        >
          Upload
        </span>
        dataset
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Upload a dataset to the database
      </p>
      <Divider />
      <p class="indent-4 text-lg leading-relaxed mt-2 mb-4 dark:text-white/80">
        During upload you need to select the project to which your dataset belongs. If there is no
        project yet for this dataset, create one with the
        <RouterLink :to="{ name: 'project' }" class="text-primary-500 hover:text-secondary-500">
          project template request
          <i class="pi pi-arrow-up-right -ml-4 text-sm" />
        </RouterLink>
      </p>
    </SectionLayout>
  </DefaultLayout>
</template>
