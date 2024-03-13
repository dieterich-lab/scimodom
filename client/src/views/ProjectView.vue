<script setup>
import { ref, onMounted } from 'vue'
import { useForm } from 'vee-validate'
import { object, string, date } from 'yup'
import { HTTPSecure } from '@/services/API'

import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'
import FormButton from '@/components/ui/FormButton.vue'

const sources = ref([
  {
    doi: '',
    pmid: ''
  }
])

function addSource() {
  sources.value.push({
    doi: '',
    pmid: ''
  })
}

function rmSource(countSrc) {
  sources.value.splice(countSrc, 1)
}

const validationSchema = object({
  forename: string().required('Forename is required'),
  surname: string().required('Surname is required'),
  institution: string()
    .required('Institution is required')
    .max(255, 'At most 255 characters allowed'),
  email: string()
    .required('Email is required')
    .email('Invalid email')
    .max(320, 'At most 320 characters allowed'),
  title: string().required().max(255, 'At most 255 characters allowed'),
  summary: string().required('Summary is required'),
  published: date()
  // doi: string().max(255, 'At most 255 characters allowed')
})

const { defineField, handleSubmit, errors } = useForm({
  validationSchema: validationSchema
})
const [title, titleProps] = defineField('title')
const [summary, summaryProps] = defineField('summary')
const [forename, forenameProps] = defineField('forename')
const [surname, surnameProps] = defineField('surname')
const [institution, institutionProps] = defineField('institution')
const [email, emailProps] = defineField('email')
const [published, publishedProps] = defineField('published')

const onSubmit = handleSubmit((values) => {
  // Submit to API
  console.log(values)
})

onMounted(() => {
  HTTPSecure.get('/access/username')
    .then((response) => {
      email.value = response.data.username
    })
    .catch((err) => {
      // console.log(err.response.status)
      console.log(err)
      // on error what to do
    })
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
          Project
        </span>
        creation
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Fill the template and request to create a new project
      </p>
      <Divider />
      <p class="text-lg leading-relaxed mt-2 mb-4 dark:text-white/80">
        To upload data to an existing project, use the
        <RouterLink :to="{ name: 'upload' }" class="text-primary-500 hover:text-secondary-500">
          dataset upload form
          <i class="pi pi-arrow-up-right text-sm" />
        </RouterLink>
        <br />
        To create a new project, complete the form below.
      </p>

      <div>
        <form @submit.prevent="onSubmit">
          <h3 class="mt-8 dark:text-white/80">Your contact details</h3>
          <div class="grid grid-cols-2 gap-4">
            <FormTextInput v-model="forename" :error="errors.forename" placeholder="Forename"
              >Forename</FormTextInput
            >
            <FormTextInput v-model="surname" :error="errors.surname" placeholder="Surname"
              >Surname (family name)</FormTextInput
            >
            <FormTextInput
              v-model="institution"
              :error="errors.institution"
              placeholder="University of ..."
              >Institution</FormTextInput
            >
            <FormTextInput v-model="email" :error="errors.email">Email address</FormTextInput>
          </div>
          <h3 class="mt-4 dark:text-white/80">Project metadata</h3>
          <div class="grid grid-rows-3 gap-2">
            <FormTextInput
              v-model="title"
              :error="errors.title"
              placeholder="Transcriptome-wide profiling ..."
              >Title</FormTextInput
            >
            <FormTextArea
              v-model="summary"
              :error="errors.summary"
              placeholder="Profiling with technique T at site-specific resolution in human cell lines X, Y, Z under conditions A and B, etc."
            >
              Summary (project description)
            </FormTextArea>
            <FormTextInput v-model="date" :error="errors.date" type="date"
              >Date published</FormTextInput
            >
          </div>

          <Button @click="addSource" label="Add sources" />
          <div
            class="grid grid-cols-3 gap-4 mt-2"
            v-for="(src, countSrc) in sources"
            v-bind:key="countSrc"
          >
            <FormTextInput v-model="src.doi" error="TODO" placeholder="10.XXXX/..."
              >DOI</FormTextInput
            >
            <FormTextInput v-model="src.pmid" error="TODO" placeholder="PubMed-ID"
              >PMID</FormTextInput
            >
            <Button @click="rmSource(countSrc)" label="Remove" text raised />
          </div>

          <!-- <InputText v-model="title" :error="errors.title">Title</InputText>
               <InputText v-model="summary" :error="errors.summary">Summary</InputText>
               <InputText v-model="forename" :error="errors.forename">Forename</InputText>
               <InputText v-model="surname" :error="errors.surname">Surname (family name)</InputText>

               <InputText v-model="institution" :error="errors.institution">Institution</InputText>
               <InputText v-model="date" :error="errors.date" type="date">Date published</InputText> -->

          <br />
          <FormButton type="submit">Submit</FormButton>
        </form>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
