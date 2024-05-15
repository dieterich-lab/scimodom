<script setup>
import { ref, onMounted } from 'vue'
import { useForm, useFieldArray } from 'vee-validate'
import { object, array, string, number, date } from 'yup'
import { HTTPSecure } from '@/services/API'

import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'

const props = defineProps(['nextCallback'])
const model = defineModel()

const validationSchema = object({
  forename: string().required('Forename is required!'),
  surname: string().required('Surname is required!'),
  contact_institution: string()
    .required('Institution is required!')
    .max(255, 'At most 255 characters allowed!'),
  contact_email: string()
    .required('Email is required!')
    .email('Invalid email!')
    .max(320, 'At most 320 characters allowed!'),
  title: string().required('Title is required!').max(255, 'At most 255 characters allowed!'),
  summary: string().required('Summary is required!'),
  date_published: date(),
  external_sources: array().of(
    object().shape({
      doi: string().max(255, 'At most 255 characters allowed!'),
      pmid: number()
        .integer()
        .typeError('PMID must be a number!')
        .nullable()
        .transform((_, val) => (val !== '' ? Number(val) : null))
    })
  )
})

const getInitialValues = () => {
  if (model.value === undefined) {
    return null
  } else {
    return { ...model.value }
  }
}

const { defineField, handleSubmit, errors } = useForm({
  validationSchema: validationSchema,
  initialValues: getInitialValues()
})
const [forename, forenameProps] = defineField('forename')
const [surname, surnameProps] = defineField('surname')
const [contact_institution, institutionProps] = defineField('contact_institution')
const [contact_email, emailProps] = defineField('contact_email')
const [title, titleProps] = defineField('title')
const [summary, summaryProps] = defineField('summary')
const [date_published, publishedProps] = defineField('date_published')
const { remove, push, fields } = useFieldArray('external_sources')

const onSubmit = handleSubmit((values) => {
  model.value = values
  props.nextCallback()
})

onMounted(() => {
  HTTPSecure.get('/user/get_username')
    .then((response) => {
      contact_email.value = response.data.username
    })
    .catch((err) => {
      // console.log(err.response.status)
      console.log(err)
      // on error what to do
    })
})
</script>

<template>
  <SectionLayout>
    <div>
      <form @submit.prevent="onSubmit">
        <div class="flex flex-col mx-auto">
          <div class="text-center -mt-4 mb-4 text-xl font-semibold dark:text-white/80">
            Project information
          </div>
        </div>
        <h3 class="mb-4 dark:text-white/80">Your contact details</h3>
        <div class="grid grid-cols-2 gap-y-2 gap-x-8">
          <FormTextInput v-model="forename" :error="errors.forename" placeholder="Forename"
            >Forename</FormTextInput
          >
          <FormTextInput v-model="surname" :error="errors.surname" placeholder="Surname"
            >Surname (family name)</FormTextInput
          >
          <FormTextInput
            v-model="contact_institution"
            :error="errors.contact_institution"
            placeholder="University of ..."
            >Institution</FormTextInput
          >
          <FormTextInput v-model="contact_email" :error="errors.contact_email"
            >Email address</FormTextInput
          >
        </div>
        <h3 class="mt-2 mb-4 dark:text-white/80">Project details</h3>
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
          <FormTextInput v-model="date_published" :error="errors.date_published" type="date"
            >Date published (add if published)</FormTextInput
          >
        </div>
        <h3 class="dark:text-white/80">Published project sources.</h3>
        <h3 class="mb-4 dark:text-white/80">
          Click <span class="inline font-semibold">"Add source"</span> to add DOI and/or PubMed-ID.
          Add as many as required. DOI or PubMed-ID can be empty.
        </h3>
        <Button @click="push({ doi: '', pmid: '' })" label="Add source" class="mt-2 mb-4" />
        <div class="grid grid-cols-3 gap-4 mt-2" v-for="(field, idx) in fields" :key="field.key">
          <FormTextInput
            v-model="field.value.doi"
            :error="errors[`external_sources[${idx}].doi`]"
            placeholder="10.XXXX/..."
            >DOI</FormTextInput
          >
          <FormTextInput
            v-model="field.value.pmid"
            :error="errors[`external_sources[${idx}].pmid`]"
            placeholder="PubMed-ID"
            >PMID</FormTextInput
          >
          <div class="place-self-start self-center">
            <Button @click="remove(idx)" label="Remove" />
          </div>
        </div>

        <br />
        <div class="flex pt-4 justify-end">
          <Button
            type="submit"
            label="Next"
            icon="pi pi-arrow-right"
            iconPos="right"
            class="p-4 text-primary-50 border border-white-alpha-30"
          >
          </Button>
        </div>
      </form>
    </div>
  </SectionLayout>
</template>
