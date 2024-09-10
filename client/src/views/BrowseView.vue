<script setup>
import { ref, onMounted } from 'vue'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import { getApiUrl } from '@/services/API.js'
import { loadDatasets } from '@/services/dataset'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import DatasetInfo from '@/components/dataset/DatasetInfo.vue'

const props = defineProps({
  eufid: {
    type: String,
    required: false,
    default: null
  }
})

const records = ref()
const showDetails = ref(false)
const selectedDataset = ref({})
const dt = ref()

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
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    },
    tech: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    },
    taxa_sname: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    },
    cto: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    }
  }
}
initFilters(props.eufid)

const getFileName = () => {
  let stamp = new Date()
  return 'scimodom_browse_' + stamp.toISOString().replaceAll(/:/g, '')
}

const onExport = () => {
  dt.value.exportCSV()
}

const onOverlay = (record) => {
  selectedDataset.value = { ...record }
  showDetails.value = true
}

onMounted(() => {
  loadDatasets(records, null, false)
})
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="Browse the data repository" />
      <SubTitle>Use filters to find available dataset</SubTitle>

      <Divider />

      <div>
        <div>
          <DataTable
            :value="records"
            dataKey="dataset_id"
            ref="dt"
            :exportFilename="getFileName()"
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
              'cto'
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
            <Column field="project_title" header="Project title" style="display: none"></Column>
            <Column field="dataset_id" header="EUFID" style="width: 5%"></Column>
            <Column field="dataset_title" header="Dataset title" style="width: 30%"></Column>
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
            <Column field="tech" header="Technology" filterField="tech" style="width: 10%">
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

            <!-- export columns shown in dialog -->
            <Column field="sequencing_platform" header="Platform" style="display: none"></Column>
            <Column field="basecalling" header="Basecalling" style="display: none"></Column>
            <Column
              field="bioinformatics_workflow"
              header="Bioinformatics"
              style="display: none"
            ></Column>
            <Column field="experiment" header="Experiment" style="display: none"></Column>
            <Column field="project_summary" header="Project summary" style="display: none"></Column>
            <Column field="doi" header="DOI" style="display: none"></Column>
            <Column field="pmid" header="PMID" style="display: none"></Column>

            <Column :exportable="false" style="width: 5%">
              <template #header>
                <span v-tooltip.top="'Click for dataset information'">Info</span>
              </template>
              <template #body="slotProps">
                <Button
                  icon="pi pi-info"
                  outlined
                  rounded
                  severity="secondary"
                  @click="onOverlay(slotProps.data)"
                />
              </template>
            </Column>
            <Column :exportable="false" field="dataset_id" style="width: 5%">
              <template #body="{ data }">
                <a :href="getApiUrl(`transfer/dataset/${data.dataset_id}`)">
                  <Button text severity="secondary" label="Download" />
                </a>
              </template>
            </Column>
          </DataTable>
        </div>

        <DatasetInfo v-model:visible="showDetails" :dataset="selectedDataset" />
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
'
