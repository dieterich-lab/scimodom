<script setup>
import { ref, onMounted } from 'vue'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import service from '@/services/index.js'

const props = defineProps({
  eufid: {
    type: String,
    required: false,
    default: null
  }
})

const records = ref()
const recordsOverlay = ref(false)
const thisRecord = ref({})
const dt = ref()
const columns = [
  { field: 'project_title', header: 'Title' },
  { field: 'project_summary', header: 'Summary' },
  { field: 'date_added', header: 'Added' },
  { field: 'date_published', header: 'Published' }
]

// todo
const status = ref(['public', 'restricted'])

const filters = ref()
const initFilters = (defaultGlobal) => {
  filters.value = {
    global: { value: defaultGlobal, matchMode: FilterMatchMode.CONTAINS },
    rna: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    },
    modomics_sname: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }]
    },
    tech: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }]
    },
    taxa_sname: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    },
    cto: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }]
    },
    // access: { value: null, matchMode: FilterMatchMode.IN },
    access: {
      operator: FilterOperator.OR,
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    }
  }
}
initFilters(props.eufid)

const onExport = () => {
  dt.value.exportCSV()
}

const splitStr = (str) => {
  return str.split(',')
}

const onOverlay = (record) => {
  thisRecord.value = { ...record }
  recordsOverlay.value = true
}

onMounted(() => {
  service
    .getEndpoint('/browse')
    .then(function (response) {
      records.value = response.data
    })
    .catch((error) => {
      console.log(error)
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
          Browse
        </span>
        the data repository
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Use filters to find available dataset
      </p>
      <Divider />
      <div>
        <div>
          <DataTable
            :value="records"
            dataKey="dataset_id"
            ref="dt"
            exportFilename="scimodom_browse"
            :paginator="true"
            :rows="5"
            v-model:filters="filters"
            filterDisplay="menu"
            :globalFilterFields="[
              'project_id',
              'dataset_id',
              'dataset_title',
              'project_title',
              'project_summary',
              'date_published',
              'date_added',
              'doi',
              'pmid',
              'rna',
              'modomics_sname',
              'tech',
              'taxa_sname',
              'cto',
              'access'
            ]"
            paginatorTemplate="FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink  RowsPerPageDropdown"
            :rowsPerPageOptions="[5, 10, 25]"
            currentPageReportTemplate="Showing {first} to {last} of {totalRecords} records"
          >
            <template #header>
              <div class="grid grid-cols-3 gap-4">
                <div class="col-span-2 space-x-2">
                  <span class="p-input-icon-left">
                    <!-- <i class="pi pi-search text-sm text-crmb" /> -->
                    <InputText
                      size="small"
                      v-model="filters['global'].value"
                      placeholder="Search"
                      :pt="{
                        root: ({ context }) => ({
                          class: [
                            {
                              'hover:border-secondary-500 dark:hover:border-secondary-400':
                                !context.disabled,
                              'focus:outline-none focus:outline-offset-0 focus:ring focus:ring-secondary-500 dark:focus:ring-secondary-400':
                                !context.disabled
                            }
                          ]
                        })
                      }"
                      :ptOptions="{ mergeProps: true }"
                    />
                  </span>
                  <Button
                    icon="pi pi-filter-slash"
                    size="small"
                    label="Clear"
                    severity="secondary"
                    outlined
                    raised
                    @click="initFilters(null)"
                  />
                </div>
                <div class="text-right">
                  <Button
                    icon="pi pi-external-link"
                    size="small"
                    label="Export"
                    severity="secondary"
                    raised
                    @click="onExport($event)"
                  />
                </div>
              </div>
            </template>
            <template #empty> No results found. </template>
            <Column field="project_id" header="SMID" style="display: none"></Column>
            <Column field="dataset_id" header="EUFID" style="display: none"></Column>
            <Column field="dataset_title" header="Title" style="width: 25%"></Column>
            <Column field="rna" header="RNA" filterField="rna" style="width: 5%">
              <template #body="{ data }">
                {{ data.rna }}
              </template>
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  class="p-column-filter"
                  placeholder="Search by RNA type"
                />
              </template>
            </Column>
            <Column
              field="modomics_sname"
              header="Modification"
              filterField="modomics_sname"
              style="width: 10%"
            >
              <template #body="{ data }">
                {{ data.modomics_sname }}
              </template>
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  class="p-column-filter"
                  placeholder="Search by modification"
                />
              </template>
            </Column>
            <Column field="tech" header="Technology" filterField="tech" style="width: 15%">
              <template #body="{ data }">
                {{ data.tech }}
              </template>
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  class="p-column-filter"
                  placeholder="Search by technology"
                />
              </template>
            </Column>
            <Column
              field="taxa_sname"
              header="Organism"
              filterField="taxa_sname"
              style="width: 10%"
            >
              <template #body="{ data }">
                {{ data.taxa_sname }}
              </template>
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  class="p-column-filter"
                  placeholder="Search by organism"
                />
              </template>
            </Column>
            <Column field="cto" header="Cell/Tissue" filterField="cto" style="width: 10%">
              <template #body="{ data }">
                {{ data.cto }}
              </template>
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  class="p-column-filter"
                  placeholder="Search by cell, tissue, organ"
                />
              </template>
            </Column>
            <Column
              field="access"
              header="Access"
              filterField="access"
              :showFilterMatchModes="false"
              style="width: 5%"
            >
              <template #body="{ data }">
                {{ data.access }}
              </template>
              <template #filter="{ filterModel }">
                <Dropdown
                  v-model="filterModel.value"
                  :options="status"
                  placeholder="Select access..."
                >
                </Dropdown>
              </template>
            </Column>

            <!-- export columns shown in dialog -->
            <Column field="project_title" header="Project" style="display: none"></Column>
            <Column field="project_summary" header="Summary" style="display: none"></Column>
            <Column field="date_added" header="Added" style="display: none"></Column>
            <Column field="date_published" header="Published" style="display: none"></Column>
            <Column field="doi" header="DOI" style="display: none"></Column>
            <Column field="pmid" header="PMID" style="display: none"></Column>

            <Column :exportable="false" style="width: 5%">
              <template #body="slotProps">
                <Button
                  icon="pi pi-plus"
                  outlined
                  rounded
                  severity="secondary"
                  class="mr-2"
                  @click="onOverlay(slotProps.data)"
                />
              </template>
            </Column>
          </DataTable>
        </div>

        <Dialog
          v-model:visible="recordsOverlay"
          header="Additional information"
          :modal="true"
          :pt="{
            root: { class: 'w-fit' },
            closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
          }"
          :ptOptions="{ mergeProps: true }"
        >
          <div>
            <div class="flex space-x-12 mb-6">
              <span class="inline-block font-semibold pr-2">SMID:</span>
              {{ thisRecord.project_id }}
              <span class="inline-block font-semibold pr-2">EUFID:</span>
              {{ thisRecord.dataset_id }}
            </div>
            <DataTable
              :value="records.filter((val) => val.dataset_id == thisRecord.dataset_id)"
              tableStyle="min-width: 50rem"
            >
              <Column
                v-for="col of columns"
                :key="col.field"
                :field="col.field"
                :header="col.header"
              ></Column>
              <Column field="doi" header="DOI">
                <template #body="{ data }">
                  <ul class="list-none" v-for="doi in splitStr(data.doi)">
                    <a
                      class="text-secondary-500 pr-12"
                      target="_blank"
                      :href="`https://doi.org/${doi}`"
                      >{{ doi }}</a
                    >
                  </ul>
                </template>
              </Column>
              <Column field="pmid" header="PMID">
                <template #body="{ data }">
                  <ul class="list-none" v-for="pmid in splitStr(data.pmid)">
                    <a
                      class="text-secondary-500"
                      target="_blank"
                      :href="`http://www.ncbi.nlm.nih.gov/pubmed/${pmid}`"
                      >{{ pmid }}</a
                    >
                  </ul>
                </template>
              </Column>
            </DataTable>
          </div>
        </Dialog>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
