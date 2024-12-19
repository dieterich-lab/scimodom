<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import { useForm, useFieldArray, type FieldEntry } from 'vee-validate'
import { object, array, string, number } from 'yup'

import SectionLayout from '@/components/layout/SectionLayout.vue'
import FormRnaTypeSelect from '@/components/ui/FormRnaTypeSelect.vue'
import FormModomicsSelect from '@/components/ui/FormModomicsSelect.vue'
import FormDetectionMethodSelect from '@/components/ui/FormDetectionMethodSelect.vue'
import FormTaxaSelect from '@/components/ui/FormTaxaSelect.vue'
import FormAssemblySelect from '@/components/ui/FormAssemblySelect.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'
import { type RnaType } from '@/services/rna_type'
import { type ProjectMetaData, type ProjectOrganism } from '@/services/management'
import { type Modomics } from '@/services/modomics'
import { type DetectionMethod } from '@/services/detection_method'
import { type Taxa } from '@/services/taxa'
import { type Assembly } from '@/services/assembly'

interface FormOrganism extends Partial<Omit<ProjectOrganism, 'taxa_id'>> {
  taxa_id?: string
}

interface FormDataMetadata extends Partial<Omit<ProjectMetaData, 'organism'>> {
  organism: FormOrganism
}

interface FormData {
  metadata: FormDataMetadata[]
}

const props = defineProps<{
  nextCallback: (event: Event) => void
  prevCallback: (event: Event) => void
}>()

export type ProjectMetaDataTabModel = ProjectMetaData[]

const model = defineModel<ProjectMetaDataTabModel>()

const pushValues: FormDataMetadata = {
  organism: {}
}

const validationSchema = object({
  metadata: array().of(
    object().shape({
      rna: string().max(32, 'At most 32 characters allowed!').required('RNA type is required!'),
      modomics_id: string()
        .max(128, 'At most 128 characters allowed!')
        .required('Modification is required!'),
      method_id: string().max(8, 'At most 8 characters allowed').required('Method is required!'),
      tech: string()
        .max(255, 'At most 255 characters allowed!')
        .required('Technology is required!'),
      organism: object().shape({
        taxa_id: number().integer().required('Organism is required!'),
        cto: string()
          .max(255, 'At most 255 characters allowed!')
          .required('Cell, tissue, or organ is required!'),
        assembly_id: number()
          .integer()
          .typeError('Assembly ID must be a number!')
          .transform((_, val) => (val !== '' ? Number(val) : null)),
        assembly_name: string()
          .max(128, 'At most 128 characters allowed!')
          .required(
            'Assembly is required! If selecting from existing (left), copy your selection above.'
          )
      }),
      note: string()
    })
  )
})

function getFormDataFromModel(): FormData | null {
  if (model.value) {
    const metadata: FormDataMetadata[] = model.value.map((x) => ({
      ...x,
      organism: {
        ...x.organism,
        taxa_id: String(x.organism.taxa_id)
      }
    }))
    return { metadata }
  } else {
    return null
  }
}

const { handleSubmit, errors } = useForm<FormData>({
  validationSchema: validationSchema,
  initialValues: getFormDataFromModel()
})
const { remove, push, fields } = useFieldArray<FormDataMetadata>('metadata')

const onSubmit = handleSubmit((values, ctx) => {
  model.value = values.metadata.map(
    (x) =>
      ({
        ...x,
        organism: {
          ...x.organism,
          taxa_id: x.organism?.taxa_id ? +x.organism.taxa_id : undefined
        }
      }) as ProjectMetaData
  )
  props.nextCallback(ctx?.evt as Event)
})

const disabled = computed(() => {
  return !fields.value?.length
})

function selectRnaType(field: FieldEntry<FormDataMetadata>, data: RnaType) {
  field.value.rna = data.id
}

function selectModomics(field: FieldEntry<FormDataMetadata>, data: Modomics) {
  field.value.modomics_id = data.id
}

function selectDetectionMethod(field: FieldEntry<FormDataMetadata>, data: DetectionMethod) {
  field.value.method_id = data.id
}

function selectTaxa(field: FieldEntry<FormDataMetadata>, data: Taxa) {
  field.value.organism.taxa_id = String(data.taxa_id)
}

function selectAssembly(field: FieldEntry<FormDataMetadata>, data: Assembly) {
  field.value.organism.assembly_id = String(data.id)
  field.value.organism.assembly_name = data.name
}
</script>
<template>
  <SectionLayout>
    <div>
      <form @submit.prevent="onSubmit">
        <div class="flex flex-col mx-auto">
          <div class="text-center -mt-4 mb-4 text-xl font-semibold dark:text-white/80">
            Project metadata
          </div>
        </div>
        <h3 class="mt-0 mb-4 dark:text-white/80">
          Click <span class="inline font-semibold">"Add metadata"</span> to add a metadata sheet for
          a dataset. Add a new metadata sheet for each dataset that belongs to this project or for
          each modification associated with a single dataset. Consult the
          <RouterLink
            :to="{ name: 'management-docs' }"
            target="_blank"
            class="inline-flex items-center font-semibold text-primary-500 hover:text-secondary-500"
            >Documentation
          </RouterLink>
          for more information and examples. At least one metadata sheet is required!
        </h3>
        <h3 class="mt-0 mb-4 dark:text-white/80">
          To submit, click <span class="inline font-semibold">"Next"</span>. You cannot go back
          after this step. Click <span class="inline font-semibold">"Back"</span> to modify the
          project form.
        </h3>
        <Button @click="push(pushValues)" label="Add metadata" class="mt-4 mb-4" />
        <div
          class="grid grid-cols-2 gap-y-2 gap-x-8 mt-4"
          v-for="(field, idx) in fields"
          :key="field.key"
        >
          <FormRnaTypeSelect
            :error="errors[`metadata[${idx}].rna`]"
            @change="(rnaType) => selectRnaType(field, rnaType)"
          />

          <FormModomicsSelect
            :error="errors[`metadata[${idx}].modomics_id`]"
            @change="(data) => selectModomics(field, data)"
          />

          <FormDetectionMethodSelect
            :error="errors[`metadata[${idx}].method_id`]"
            @change="(method) => selectDetectionMethod(field, method)"
          />

          <FormTextInput
            v-model="field.value.tech"
            :error="errors[`metadata[${idx}].tech`]"
            placeholder="Tech-seq"
          >
            Technology
          </FormTextInput>

          <FormTaxaSelect
            @change="(data) => selectTaxa(field, data)"
            :error="errors[`metadata[${idx}].organism.taxa_id`]"
          />

          <FormTextInput
            v-model="field.value.organism.cto"
            :error="errors[`metadata[${idx}].organism.cto`]"
            placeholder="e.g. HeLa, mESC, or Heart"
          >
            Cell, tissue, organ
          </FormTextInput>

          <FormAssemblySelect
            :taxa-id="field.value.organism.taxa_id ? +field.value.organism.taxa_id : undefined"
            @change="(data) => selectAssembly(field, data)"
            :error="errors[`metadata[${idx}].organism.assembly_id`]"
          />

          <FormTextInput
            v-model="field.value.organism.assembly_name"
            :error="errors[`metadata[${idx}].organism.assembly_name`]"
            placeholder="e.g. NCBI36 (Ensembl release 54)"
          >
            Assembly (if not available)
          </FormTextInput>

          <FormTextArea
            v-model="field.value.note"
            :error="errors[`metadata[${idx}].note`]"
            placeholder="Tech-seq sources: 10.XXXX/... This metadata template is for published data (PubMed-ID, GEO, ...), etc."
          >
            Additional notes for this metadata template.
          </FormTextArea>

          <div class="place-self-start self-center">
            <Button @click="remove(idx)" label="Remove metadata" />
          </div>
        </div>
        <br />
        <div class="flex pt-4 justify-between">
          <Button label="Back" severity="secondary" icon="pi pi-arrow-left" @click="prevCallback" />
          <Button
            type="submit"
            label="Next"
            icon="pi pi-arrow-right"
            iconPos="right"
            :disabled="disabled"
          />
        </div>
      </form>
    </div>
  </SectionLayout>
</template>
