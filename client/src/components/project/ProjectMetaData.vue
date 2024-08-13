<script setup>
import { ref, computed, onMounted } from 'vue'
import { useForm, useFieldArray } from 'vee-validate'
import { object, array, string, number } from 'yup'
import { HTTP } from '@/services/API'
import { toTree, toCascade, nestedSort } from '@/utils/index.js'

import FormDropdown from '@/components/ui/FormDropdown.vue'
import FormCascade from '@/components/ui/FormCascade.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'

const props = defineProps(['nextCallback', 'prevCallback'])
const model = defineModel()

const rna = ref([])
const modification = ref([])
const method = ref([])
const taxa = ref([])
const assembly = ref([])

const pushValues = {
  rna: '',
  modomics_id: '',
  method_id: '',
  tech: '',
  taxa_id: null,
  cto: '',
  assembly_id: null,
  assembly_name: '',
  note: ''
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
        ),
      note: string()
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

const { handleSubmit, errors } = useForm({
  validationSchema: validationSchema,
  initialValues: getInitialValues()
})
const { remove, push, fields } = useFieldArray('metadata')

const onSubmit = handleSubmit((values) => {
  model.value = values
  props.nextCallback()
})

const disabled = computed(() => {
  return fields.value.length == 0
})

const getAssemblies = (taxid) => {
  HTTP.get(`/assembly/${taxid}`)
    .then(function (response) {
      assembly.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
}

onMounted(() => {
  HTTP.get('/rna_types')
    .then(function (response) {
      rna.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/modomics')
    .then(function (response) {
      modification.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/methods')
    .then(function (response) {
      method.value = toCascade(toTree(response.data, ['cls', 'meth'], 'id'))
      nestedSort(method.value, ['child1'])
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/taxa')
    .then(function (response) {
      let opts = response.data
      opts = opts.map((item) => {
        const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
        return { ...item, kingdom }
      })
      taxa.value = toCascade(toTree(opts, ['kingdom', 'taxa_sname'], 'id'))
      nestedSort(taxa.value, ['child1'])
    })
    .catch((error) => {
      console.log(error)
    })
})
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
          <FormDropdown
            v-model="field.value.rna"
            :options="rna"
            optionValue="id"
            :error="errors[`metadata[${idx}].rna`]"
            placeholder="Select RNA type"
            >RNA type
          </FormDropdown>
          <FormDropdown
            v-model="field.value.modomics_id"
            :options="modification"
            optionLabel="modomics_sname"
            optionValue="id"
            :error="errors[`metadata[${idx}].modomics_id`]"
            placeholder="Select modification"
            >Modification
          </FormDropdown>
          <FormCascade
            v-model="field.value.method_id"
            :options="method"
            optionValue="key"
            :error="errors[`metadata[${idx}].method_id`]"
            placeholder="Select method"
            >Method
          </FormCascade>
          <FormTextInput
            v-model="field.value.tech"
            :error="errors[`metadata[${idx}].tech`]"
            placeholder="Tech-seq"
            >Technology
          </FormTextInput>
          <FormCascade
            v-model="field.value.taxa_id"
            :options="taxa"
            optionValue="key"
            @change="getAssemblies($event)"
            :error="errors[`metadata[${idx}].taxa_id`]"
            placeholder="Select organism"
            >Organism
          </FormCascade>
          <FormTextInput
            v-model="field.value.cto"
            :error="errors[`metadata[${idx}].cto`]"
            placeholder="e.g. HeLa, mESC, or Heart"
            >Cell, tissue, organ</FormTextInput
          >
          <FormDropdown
            v-model="field.value.assembly_id"
            :options="assembly"
            optionLabel="name"
            optionValue="id"
            :error="errors[`metadata[${idx}].assembly_id`]"
            placeholder="Select assembly"
            >Assembly (select from existing assemblies)
          </FormDropdown>
          <FormTextInput
            v-model="field.value.assembly_name"
            :error="errors[`metadata[${idx}].assembly_name`]"
            placeholder="e.g. NCBI36 (Ensembl release 54)"
            >Assembly (if not available)</FormTextInput
          >
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
