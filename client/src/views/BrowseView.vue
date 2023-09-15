<script setup>
import { ref, onMounted } from 'vue'
import service from '@/services/index.js'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import { useToast } from 'primevue/usetoast'

const toast = useToast()
const dt = ref()

const columns = [
  { field: 'date_added', header: 'Added' },
  { field: 'date_published', header: 'Published' },
  { field: 'doi', header: 'DOI' },
  { field: 'pmid', header: 'PMID' },
  { field: 'assembly', header: 'Assembly' },
  { field: 'annotation_src', header: 'Annotation' },
  { field: 'annotation_ver', header: 'Version' },
  { field: 'seq_platform', header: 'Seq. Platform' },
  { field: 'basecalling', header: 'Basecalling' }
]

const endpoints = ['/dataset']
const products = ref()
onMounted(() => {
  service
    .getConcurrent(endpoints)
    .then(function (response) {
      products.value = response[0].data
    })
    .catch((error) => {
      console.log(error)
    })
})

const productDialog = ref(false)
const deleteProductDialog = ref(false)
const deleteProductsDialog = ref(false)
const product = ref({})
const selectedProducts = ref()
const filters = ref()
const initFilters = () => {
  filters.value = {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    name: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }]
    },
    rna_type: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }]
    },
    modification: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }]
    },
    technology: {
      operator: FilterOperator.AND,
      constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }]
    },
    taxid: {
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
const submitted = ref(false)
const statuses = ref(['public', 'restricted'])
const openNew = () => {
  product.value = {}
  submitted.value = false
  productDialog.value = true
}
const hideDialog = () => {
  productDialog.value = false
  submitted.value = false
}
const saveProduct = () => {
  submitted.value = true

  if (product.value.name.trim()) {
    if (product.value.id) {
      product.value.inventoryStatus = product.value.inventoryStatus.value
        ? product.value.inventoryStatus.value
        : product.value.inventoryStatus
      products.value[findIndexById(product.value.id)] = product.value
      toast.add({
        severity: 'success',
        summary: 'Successful',
        detail: 'Product Updated',
        life: 3000
      })
    } else {
      product.value.id = createId()
      product.value.code = createId()
      product.value.image = 'product-placeholder.svg'
      product.value.inventoryStatus = product.value.inventoryStatus
        ? product.value.inventoryStatus.value
        : 'INSTOCK'
      products.value.push(product.value)
      toast.add({
        severity: 'success',
        summary: 'Successful',
        detail: 'Product Created',
        life: 3000
      })
    }

    productDialog.value = false
    product.value = {}
  }
}
const editProduct = (prod) => {
  product.value = { ...prod }
  productDialog.value = true
}
const confirmDeleteProduct = (prod) => {
  product.value = prod
  deleteProductDialog.value = true
}
const deleteProduct = () => {
  products.value = products.value.filter((val) => val.id !== product.value.id)
  deleteProductDialog.value = false
  product.value = {}
  toast.add({ severity: 'success', summary: 'Successful', detail: 'Product Deleted', life: 3000 })
}
const findIndexById = (id) => {
  let index = -1
  for (let i = 0; i < products.value.length; i++) {
    if (products.value[i].id === id) {
      index = i
      break
    }
  }

  return index
}
const createId = () => {
  let id = ''
  var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  for (var i = 0; i < 5; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return id
}
const exportCSV = () => {
  dt.value.exportCSV()
}
const confirmDeleteSelected = () => {
  deleteProductsDialog.value = true
}
const deleteSelectedProducts = () => {
  products.value = products.value.filter((val) => !selectedProducts.value.includes(val))
  deleteProductsDialog.value = false
  selectedProducts.value = null
  toast.add({ severity: 'success', summary: 'Successful', detail: 'Products Deleted', life: 3000 })
}
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100"
        >
          Browse
        </span>
        the data repository
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">
        Use filters to find available dataset
      </p>
      <Divider :pt="{ root: { class: 'bg-crmapgreen' } }" />
      <div>
        <div class="card">
          <Toolbar class="mb-4">
            <template #start>
              <Button
                label="New"
                icon="pi pi-plus"
                severity="success"
                class="mr-2"
                @click="openNew"
                disabled
              />
            </template>
            <template #end>
              <FileUpload
                mode="basic"
                accept="image/*"
                :maxFileSize="1000000"
                label="Import"
                chooseLabel="Import"
                class="mr-2 inline-block"
                disabled
              />
              <Button
                label="Export"
                icon="pi pi-upload"
                severity="help"
                @click="exportCSV($event)"
              />
            </template>
          </Toolbar>

          <DataTable
            ref="dt"
            :value="products"
            v-model:selection="selectedProducts"
            dataKey="smid"
            :paginator="true"
            :rows="10"
            v-model:filters="filters"
            filterDisplay="menu"
            :globalFilterFields="[
              'smid',
              'name',
              'rna_type',
              'modification',
              'technology',
              'taxid',
              'cto',
              'access'
            ]"
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
            :rowsPerPageOptions="[5, 10, 25]"
            currentPageReportTemplate="Showing {first} to {last} of {totalRecords} products"
          >
            <template #header>
              <div class="flex justify-between">
                <Button
                  type="button"
                  icon="pi pi-filter-slash"
                  label="Clear"
                  outlined
                  @click="clearFilter()"
                />
                <span class="p-input-icon-left">
                  <i class="pi pi-search" />
                  <InputText v-model="filters['global'].value" placeholder="Search..." />
                </span>
              </div>
            </template>
            <template #empty> No results found. </template>
            <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
            <Column field="smid" header="SMID" sortable style="width: 5%"></Column>
            <Column field="name" header="Name" filterField="name" style="width: 25%">
              <template #body="{ data }">
                {{ data.name }}
              </template>
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  class="p-column-filter"
                  placeholder="Search by name"
                />
              </template>
            </Column>
            <Column field="rna_type" header="RNA" filterField="rna_type" style="width: 10%">
              <template #body="{ data }">
                {{ data.rna_type }}
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
              field="modification"
              header="Modification"
              filterField="modification"
              style="width: 10%"
            >
              <template #body="{ data }">
                {{ data.modification }}
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
              field="technology"
              header="Technology"
              filterField="technology"
              style="width: 20%"
            >
              <template #body="{ data }">
                {{ data.technology }}
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
            <Column field="taxid" header="Organism" filterField="taxid" style="width: 10%">
              <template #body="{ data }">
                {{ data.taxid }}
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

            <Column field="cto" header="Cell-Organ" filterField="cto" style="width: 10%">
              <template #body="{ data }">
                {{ data.cto }}
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
                  :options="statuses"
                  placeholder="Select access..."
                >
                </Dropdown>
              </template>
            </Column>

            <!-- export columns shown in dialog -->
            <Column field="date_added" header="Added" style="display: none"></Column>
            <Column field="date_published" header="Published" style="display: none"></Column>
            <Column field="doi" header="DOI" style="display: none"></Column>
            <Column field="pmid" header="PMID" style="display: none"></Column>
            <Column field="assembly" header="Assembly" style="display: none"></Column>
            <Column field="annotation_src" header="Annotation" style="display: none"></Column>
            <Column field="annotation_ver" header="Version" style="display: none"></Column>
            <Column field="seq_platform" header="Seq. Platform" style="display: none"></Column>
            <Column field="basecalling" header="Basecalling" style="display: none"></Column>
            <Column field="description" header="Description" style="display: none"></Column>

            <Column :exportable="false" style="width: 5%">
              <template #body="slotProps">
                <Button
                  icon="pi pi-plus"
                  outlined
                  rounded
                  class="mr-2"
                  @click="editProduct(slotProps.data)"
                />
              </template>
            </Column>
          </DataTable>
        </div>

        <Dialog
          v-model:visible="productDialog"
          header="Additional information"
          :modal="true"
          class="p-fluid"
        >
          <div>
            <h2>{{ product.name }}</h2>
            <p>{{ product.description }}</p>
            <DataTable
              :value="products.filter((val) => val.smid == product.smid)"
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
