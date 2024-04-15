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

const modification = ref()
const method = ref()
const selectedModification = ref()
const selectedMethod = ref()
const selectedType = ref()

// TODO define in BE
const rna = ref([{ key: 'mRNA' }, { key: 'rRNA' }])

import FormDropdown from '@/components/ui/FormDropdown.vue'

import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormTextArea from '@/components/ui/FormTextArea.vue'
import FormButton from '@/components/ui/FormButton.vue'

const props = defineProps(['nextCallback'])
const model = defineModel()

const validationSchema = object({
  metadata: array().of(
    object().shape({
      rna: string().required('RNA type is required@'),
      modification: string().required('Modification is required!'),
      method: string().required('Method is required!'),
      technology: string().required('Technology is required!'),
      taxid: number().integer(),
      organism: string(),
      assembly: string(), //?
      note: string()
    })
  )
})

// const getInitialValues = () => {
//     if (model.value === undefined) {
//         return { doi: '', pmid: null }
//     } else {
//         return { ...model.value}
//     }
// }

const { defineField, handleSubmit, errors } = useForm({
  validationSchema: validationSchema
  // initialValues: getInitialValues()
})
// const [forename, forenameProps] = defineField('forename')
// const [surname, surnameProps] = defineField('surname')
// const [institution, institutionProps] = defineField('institution')
// const [email, emailProps] = defineField('email')
// const [title, titleProps] = defineField('title')
// const [summary, summaryProps] = defineField('summary')
// const [published, publishedProps] = defineField('published')

const { remove, push, fields } = useFieldArray('metadata')

const onSubmit = handleSubmit((values) => {
  // Submit to API
  console.log(values)
  //  model.value = values
  //  props.nextCallback()
})

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
})
</script>

<template>
  <SectionLayout>
    <div>
      <form @submit.prevent="onSubmit">
        <!-- <h3 class="dark:text-white/80">Your contact details</h3> -->

        <h3 class="mt-4 mb-2 dark:text-white/80">Project metadata...</h3>
        <Button
          @click="
            push({
              rna: '',
              modification: '',
              method: '',
              technology: '',
              taxid: '',
              organism: '',
              assembly: '',
              note: ''
            })
          "
          label="Add metadata"
        />
        <div class="grid grid-cols-2 gap-4 mt-2" v-for="(field, idx) in fields" :key="field.key">
          <FormDropdown
            v-model.getKey="field.value.rna"
            :options="rna"
            optionLabel="key"
            :error="errors[`metadata[${idx}].rna`]"
            placeholder="Select RNA type"
            >RNA type</FormDropdown
          >
          <Dropdown
            v-model="selectedModification"
            @change="field.value.modification = selectedModification.id"
            editable
            :options="modification"
            optionLabel="modomics_sname"
            placeholder="Select RNA modification"
          />

          <div class="inline-flex flex-col gap-2">
            <label for="meth" class="text-primary-500 font-semibold"> Method </label>
            <CascadeSelect
              id="meth"
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
              <span :class="['pl-1 place-self-center', props.errMsgCls]"
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
          {{ fields }}
          <!-- <FormTextInput
                 v-model="field.value.doi"
                 :error="errors[`sources[${idx}].doi`]"
                 placeholder="10.XXXX/..."
                 >DOI</FormTextInput
                 >
                 <FormTextInput
                 v-model="field.value.pmid"
                 :error="errors[`sources[${idx}].pmid`]"
                 placeholder="PubMed-ID"
                 >PMID</FormTextInput
                 > -->
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
