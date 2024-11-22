<script setup lang="ts">
import { useForm, useFieldArray } from 'vee-validate'
import { object, array, string, number, date } from 'yup'
import { type ProjectInfo, type ExternalSource } from '@/services/management'
import Button from 'primevue/button'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import { useAccessToken } from '@/stores/AccessToken'
import { useDialogState, DIALOG } from '@/stores/DialogState'

const props = defineProps<{
  nextCallback: (event: Event) => void
}>()

interface FormExternalSource {
  doi?: string
  pmid?: string
}

interface FormData extends Omit<ProjectInfo, 'contact_name' | 'external_sources'> {
  forename: string
  surname: string
  external_sources: FormExternalSource[]
}

export interface ProjectInfoTabModel extends ProjectInfo {
  external_sources: ExternalSource[]
}

const model = defineModel<ProjectInfoTabModel>()

const accessToken = useAccessToken()
const dialogState = useDialogState()

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
      doi: string()
        .max(255, 'At most 255 characters allowed!')
        .matches(/^10\./, { message: 'DOI must start with "10."!' })
        .nullable()
        .transform((_, val) => (val !== '' ? val : null)),
      pmid: number()
        .integer()
        .typeError('PMID must be a number!')
        .nullable()
        .transform((_, val) => (val !== '' ? Number(val) : null))
    })
  )
})

const { defineField, handleSubmit, errors } = useForm<FormData>({
  validationSchema: validationSchema,
  initialValues: model.value ? getFormDataFromModel(model.value) : null
})
const [forename] = defineField('forename')
const [surname] = defineField('surname')
const [contact_institution] = defineField('contact_institution')
const [contact_email] = defineField('contact_email')
const [title] = defineField('title')
const [summary] = defineField('summary')
const [date_published] = defineField('date_published')
const { remove, push, fields } = useFieldArray<FormExternalSource>('external_sources')

if (accessToken.email) {
  contact_email.value = accessToken.email
} else {
  dialogState.message = 'You are not logged in - maybe your session expired.'
  dialogState.state = DIALOG.LOGIN
}

const onSubmit = handleSubmit((values, ctx) => {
  const contact_name = `${values.surname}, ${values.forename}`
  const external_sources = values.external_sources
    ? values.external_sources
        .filter(({ doi, pmid }) => doi || pmid)
        .map(({ doi, pmid }) => ({ doi, pmid: pmid ? +pmid : undefined }))
    : []
  model.value = {
    ...(values as FormData),
    contact_name,
    external_sources
  }
  props.nextCallback(ctx.evt as Event)
})

function getFormDataFromModel(x: ProjectInfoTabModel): FormData {
  const [surname, forename] = x.contact_name.split(', ')
  const external_sources: FormExternalSource[] = x.external_sources.map((s) => ({
    doi: s.doi,
    pmid: String(s.pmid)
  }))
  return { ...x, surname, forename, external_sources }
}
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
          <FormTextInput v-model="forename" :error="errors.forename" placeholder="Forename">
            Forename
          </FormTextInput>
          <FormTextInput v-model="surname" :error="errors.surname" placeholder="Surname">
            Surname (family name)
          </FormTextInput>
          <FormTextInput
            v-model="contact_institution"
            :error="errors.contact_institution"
            placeholder="University of ..."
          >
            Institution
          </FormTextInput>
          <FormTextInput v-model="contact_email" :error="errors.contact_email">
            Email address
          </FormTextInput>
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
          <FormTextInput v-model="date_published" :error="errors.date_published" type="date">
            Date published (add if published)
          </FormTextInput>
        </div>
        <h3 class="dark:text-white/80">Published project sources.</h3>
        <h3 class="mb-4 dark:text-white/80">
          Click <span class="inline font-semibold">"Add source"</span> to add DOI and/or PubMed-ID.
          Add as many as required. DOI or PubMed-ID can be empty.
        </h3>
        <Button
          @click="push({ doi: undefined, pmid: undefined })"
          label="Add source"
          class="mt-2 mb-4"
        />
        <div class="grid grid-cols-3 gap-4 mt-2" v-for="(field, idx) in fields" :key="field.key">
          <FormTextInput
            v-model="field.value.doi"
            :error="errors[`external_sources[${idx}].doi`]"
            placeholder="10.XXXX/..."
          >
            DOI
          </FormTextInput>
          <FormTextInput
            v-model="field.value.pmid"
            :error="errors[`external_sources[${idx}].pmid`]"
            placeholder="PubMed-ID"
          >
            PMID
          </FormTextInput>
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
