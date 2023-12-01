<script setup>
import { ref, onMounted } from 'vue'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import service from '@/services/index.js'

const records = ref()
const dt = ref()
const recordsOverlay = ref(false)
const thisRecord = ref({})
const filters = ref()
// todo
const status = ref(['public', 'restricted'])
const columns = [
  { field: 'project_title', header: 'Project' },
  { field: 'project_summary', header: 'Summary' },
  { field: 'date_added', header: 'Added' },
  { field: 'date_published', header: 'Published' },
  { field: 'doi', header: 'DOI' },
  { field: 'pmid', header: 'PMID' }
]

const initFilters = () => {
  filters.value = {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
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

initFilters()

const clearFilter = () => {
  initFilters()
}

const onExport = () => {
  dt.value.exportCSV()
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
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmgs-50 from-10% via-crmgs-25 via-40% via-crmbs-50 via-60% to-crmbs-100 to-100"
        >
          Browse
        </span>
        the data repository
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">
        Use filters to find available dataset
      </p>
      <Divider :pt="{ root: { class: 'bg-crmg' } }" />
      <div>
        <div>
          <DataTable
            ref="dt"
            :value="records"
            dataKey="dataset_id"
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
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
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
                    />
                  </span>
                  <Button
                    icon="pi pi-filter-slash"
                    size="small"
                    label="Clear"
                    outlined
                    @click="clearFilter()"
                    :pt="{
                      root: {
                        class:
                          'text-crmb border-crmb hover:border-crmb/75 focus:ring-crmb/75 focus:outline-none'
                      }
                    }"
                  />
                </div>
                <div class="text-right">
                  <Button
                    icon="pi pi-external-link"
                    size="small"
                    label="Export"
                    @click="onExport($event)"
                    :pt="{
                      root: {
                        class:
                          'bg-crmb border-crmb hover:bg-crmb/75 hover:border-crmb/75 focus:ring-crmb/75 focus:outline-none focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(2,176,237,1),0_1px_2px_0_rgba(0,0,0,1)]'
                      }
                    }"
                  />
                </div>
              </div>
            </template>
            <template #empty> No results found. </template>
            <Column field="project_id" header="SMID" style="width: 5%"></Column>
            <Column field="dataset_id" header="EUFID" style="width: 5%"></Column>
            <Column field="dataset_title" header="Title" style="width: 5%"></Column>
            <Column field="rna" header="RNA" filterField="rna" style="width: 10%">
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
              style="width: 25%"
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
            <Column field="tech" header="Technology" filterField="tech" style="width: 20%">
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
                  class="mr-2"
                  @click="onOverlay(slotProps.data)"
                  :pt="{
                    root: {
                      class:
                        'text-crmb border-crmb hover:border-crmb/75 focus:ring-crmb/75 focus:outline-none'
                    }
                  }"
                />
              </template>
            </Column>
          </DataTable>
        </div>

        <Dialog
          v-model:visible="recordsOverlay"
          header="Additional information"
          :modal="true"
          class="p-fluid"
        >
          <div>
            <h2>{{ thisRecord.dataset_id }}</h2>
            <p>{{ thisRecord.sequencing_platform }}</p>
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
            </DataTable>
          </div>
        </Dialog>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
