<script setup>
import { ref, onMounted } from 'vue'
import { useForm, useFieldArray } from 'vee-validate'
import { object, array, string, number, date } from 'yup'
import { HTTPSecure } from '@/services/API'

import { toTree, toCascade, nestedSort, toIds } from '@/utils/index.js'
import { HTTP } from '@/services/API.js'
import {
  updModification,
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'

const modification = ref([])
const method = ref([])
const taxid = ref([])
const assembly = ref([])
const selectedModification = ref()
const selectedMethod = ref()
const selectedType = ref()
const selectedTaxid = ref()
const selectedAssembly = ref()

// TODO define in BE
const rna = ref(['mRNA', 'rRNA'])

import FormDropdown from '@/components/ui/FormDropdown.vue'

import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'
import FormButton from '@/components/ui/FormButton.vue'

const props = defineProps(['nextCallback'])
const model = defineModel()

const validationSchema = object({
  metadata: array().of(
    object().shape({
      rna: string().required('RNA type is required!'), //.nullable().transform((value) => !!value ? value : null),
      modification: string().required('Modification is required!'), //.nullable().transform((value) => !!value ? value : null),
      method: string().required('Method is required!'), //.nullable().transform((value) => !!value ? value : null),
      technology: string().required('Technology is required!'),
      taxid: number().integer().required('Organism is a required field!'),
      organism: string().required('Cell, tissue, or organ is required!'),
      assembly: number()
        .integer()
        .typeError('Assembly ID must be a number!')
        .transform((_, val) => (val !== '' ? Number(val) : null)),
      freeAssembly: string(),
      note: string()
    })
  )
})

const initialValues = {
  rna: '',
  modification: '',
  method: '',
  technology: '',
  taxid: null,
  organism: '',
  assembly: null,
  freeAssembly: '',
  note: ''
}

const getInitialValues = () => {
  if (model.value === undefined) {
    return initialValues
  } else {
    return { ...model.value }
  }
}
console.log('INITIAL', getInitialValues())

const { handleSubmit, errors } = useForm({
  validationSchema: validationSchema,
  initialValues: getInitialValues()
})

const { remove, push, fields } = useFieldArray('metadata')

console.log('FIELDS', fields)

const onSubmit = handleSubmit((values) => {
  // Submit to API
  console.log('ON SUBMIT')
  console.log(values)
  //  model.value = values
  //  props.nextCallback()
})

const getAssemblies = () => {
  HTTP.get(`/assembly/${selectedTaxid.value.key}`)
    .then(function (response) {
      assembly.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
}

onMounted(() => {
  HTTP.get('/modification')
    .then(function (response) {
      modification.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/method')
    .then(function (response) {
      method.value = toCascade(toTree(response.data, ['cls', 'meth'], 'id'))
      // console.log(method.value)
      nestedSort(method.value, ['child1'])
      // console.log('2', method.value)
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/taxid')
    .then(function (response) {
      let opts = response.data
      opts = opts.map((item) => {
        const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
        return { ...item, kingdom }
      })
      taxid.value = toCascade(toTree(opts, ['kingdom', 'taxa_sname'], 'id'))
      nestedSort(taxid.value, ['child1'])
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
        <!-- <h3 class="dark:text-white/80">Your contact details</h3> -->

        <h3 class="mt-4 mb-2 dark:text-white/80">Project metadata...</h3>
        <Button @click="push(initialValues)" label="Add metadata" />
        <div class="grid grid-cols-2 gap-4 mt-2" v-for="(field, idx) in fields" :key="field.key">
          <div class="inline-flex flex-col gap-2">
            <label for="rnaDropdown" class="text-primary-500 font-semibold"> RNA type </label>
            <Dropdown
              id="rnaDropdown"
              v-model="field.value.rna"
              :options="rna"
              placeholder="Select RNA type"
              :class="errors[`metadata[${idx}].rna`] ? '!ring-red-700' : ''"
            />
            <span class="inline-flex items-baseline">
              <i
                :class="
                  errors[`metadata[${idx}].rna`]
                    ? 'pi pi-times-circle place-self-center text-red-700'
                    : ''
                "
              />
              <span :class="['pl-1 place-self-center', 'text-red-700']"
                >{{ errors[`metadata[${idx}].rna`] }}&nbsp;</span
              >
            </span>
          </div>
          <div class="inline-flex flex-col gap-2">
            <label for="modDropdown" class="text-primary-500 font-semibold"> Modification </label>
            <Dropdown
              id="modDropdown"
              v-model="selectedModification"
              @change="field.value.modification = selectedModification.id"
              editable
              :options="modification"
              optionLabel="modomics_sname"
              placeholder="Select RNA modification"
              :class="errors[`metadata[${idx}].modification`] ? '!ring-red-700' : ''"
            />
            <span class="inline-flex items-baseline">
              <i
                :class="
                  errors[`metadata[${idx}].modification`]
                    ? 'pi pi-times-circle place-self-center text-red-700'
                    : ''
                "
              />
              <span :class="['pl-1 place-self-center', 'text-red-700']"
                >{{ errors[`metadata[${idx}].modification`] }}&nbsp;</span
              >
            </span>
          </div>
          <div class="inline-flex flex-col gap-2">
            <label for="methDropdown" class="text-primary-500 font-semibold"> Method </label>
            <CascadeSelect
              id="methDropdown"
              v-model="selectedMethod"
              @change="field.value.method = selectedMethod.key"
              :options="method"
              optionLabel="label"
              optionGroupLabel="label"
              :optionGroupChildren="['child1', 'child2']"
              placeholder="Select method"
              :class="errors[`metadata[${idx}].method`] ? '!ring-red-700' : ''"
            />
            <span class="inline-flex items-baseline">
              <i
                :class="
                  errors[`metadata[${idx}].method`]
                    ? 'pi pi-times-circle place-self-center text-red-700'
                    : ''
                "
              />
              <span :class="['pl-1 place-self-center', 'text-red-700']"
                >{{ errors[`metadata[${idx}].method`] }}&nbsp;</span
              >
            </span>
          </div>
          <FormTextInput
            v-model="field.value.technology"
            :error="errors[`metadata[${idx}].technology`]"
            placeholder="Tech-seq"
            >Technology</FormTextInput
          >
          <div class="inline-flex flex-col gap-2">
            <label for="orgDropdown" class="text-primary-500 font-semibold"> Organism </label>
            <CascadeSelect
              id="orgDropdown"
              v-model="selectedTaxid"
              @change="[(field.value.taxid = selectedTaxid.key), getAssemblies()]"
              :options="taxid"
              optionLabel="label"
              optionGroupLabel="label"
              :optionGroupChildren="['child1']"
              placeholder="Select organism"
              :class="errors[`metadata[${idx}].taxid`] ? '!ring-red-700' : ''"
            />
            <span class="inline-flex items-baseline">
              <i
                :class="
                  errors[`metadata[${idx}].taxid`]
                    ? 'pi pi-times-circle place-self-center text-red-700'
                    : ''
                "
              />
              <span :class="['pl-1 place-self-center', props.errMsgCls]"
                >{{ errors[`metadata[${idx}].taxid`] }}&nbsp;</span
              >
            </span>
          </div>
          <FormTextInput
            v-model="field.value.organism"
            :error="errors[`metadata[${idx}].organism`]"
            placeholder="e.g. HeLa, mESC, or Heart"
            >Cell, tissue, organ</FormTextInput
          >
          <div class="inline-flex flex-col gap-2">
            <label for="asmbDropdown" class="text-primary-500 font-semibold">
              Assembly (select from existing assemblies)
            </label>
            <Dropdown
              id="asmbDropdown"
              v-model="selectedAssembly"
              @change="field.value.assembly = selectedAssembly.id"
              :options="assembly"
              optionLabel="name"
              placeholder="Select assembly"
              :class="errors[`metadata[${idx}].assembly`] ? '!ring-red-700' : ''"
            />
            <span class="inline-flex items-baseline">
              <i
                :class="
                  errors[`metadata[${idx}].assembly`]
                    ? 'pi pi-times-circle place-self-center text-red-700'
                    : ''
                "
              />
              <span :class="['pl-1 place-self-center', 'text-red-700']"
                >{{ errors[`metadata[${idx}].assembly`] }}&nbsp;</span
              >
            </span>
          </div>
          <FormTextInput
            v-model="field.value.freeAssembly"
            :error="errors[`metadata[${idx}].freeAssembly`]"
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
          FIELDS:
          {{ fields }}
          <br />
          ERRORS:
          {{ errors }}
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
