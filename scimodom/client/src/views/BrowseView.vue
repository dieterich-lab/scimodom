<script setup>
import { ref } from 'vue'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import { useToast } from 'primevue/usetoast'


const toast = useToast()
const dt = ref()

const products = ref([
  {
      smid: '1000',
      name: 'Dataset and/or paper name 1',
      rnaType: 'mRNA',
      modification: 'm6A',
      technology: 'DART-seq',
      species: '9606',
      cto: 'Heart',
      datePublished: '2023-06-06',
      dateAdded: '2023-06-06',
      doi: '10.123456',
      pmid: '123123',
      access: 'restricted',
      assembly: 'GRCh38.p13',
      annotationSrc: 'Ensembl',
      annotationVer: '106',
      seqPlatform: 'Illumina',
      basecalling: '',
    description: '1 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
   },
   {
      smid: '1001',
      name: 'Dataset and/or paper name 2',
      rnaType: 'mRNA',
      modification: 'm6A',
      technology: 'm6A-seq/MeRIP',
      species: '9606',
      cto: 'HEK293',
      datePublished: '2023-06-06',
      dateAdded: '2023-06-06',
      doi: '12.123456',
      pmid: '0123123',
      access: 'public',
      assembly: 'GRCh38.p13',
      annotationSrc: 'Ensembl',
      annotationVer: '106',
      seqPlatform: 'Illumina',
      basecalling: '',
     description: '2 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
   },
     {
      smid: '1002',
      name: 'Dataset and/or paper name 3',
      rnaType: 'mRNA',
      modification: 'm6A,m5C',
      technology: 'ONT',
      species: '9606',
      cto: 'Liver',
      datePublished: '2023-06-06',
      dateAdded: '2023-06-06',
      doi: '13.123456',
      pmid: '223123',
      access: 'public',
      assembly: 'GRCh38.p13',
      annotationSrc: 'Ensembl',
      annotationVer: '106',
      seqPlatform: 'ONT',
      basecalling: '',
       description: '3 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
   }
])

const columns = [
  { field: 'dateAdded', header: 'Added' },
  { field: 'datePublished', header: 'Published' },
  { field: 'doi', header: 'DOI' },
  { field: 'pmid', header: 'PMID' },
  { field: 'assembly', header: 'Assembly' },
  { field: 'annotationSrc', header: 'Annotation' },
  { field: 'annotationVer', header: 'Version' },
  { field: 'seqPlatform', header: 'Seq. Platform' },
  { field: 'basecalling', header: 'Basecalling' },
];


const productDialog = ref(false);
const deleteProductDialog = ref(false);
const deleteProductsDialog = ref(false);
const product = ref({});
const selectedProducts = ref();
const filters = ref()
const initFilters = () => {
  filters.value = {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    name: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }] },
    rnaType: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }] },
    modification: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }] },
    technology: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }] },
    species: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }] },
    cto: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }] },
    // access: { value: null, matchMode: FilterMatchMode.IN },
    access: { operator: FilterOperator.OR, constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }] }
  }
}
initFilters()
const clearFilter = () => {
  initFilters();
}
const submitted = ref(false);
const statuses = ref(['public', 'restricted']);
const openNew = () => {
    product.value = {};
    submitted.value = false;
    productDialog.value = true;
};
const hideDialog = () => {
    productDialog.value = false;
    submitted.value = false;
};
const saveProduct = () => {
    submitted.value = true;

    if (product.value.name.trim()) {
        if (product.value.id) {
            product.value.inventoryStatus = product.value.inventoryStatus.value ? product.value.inventoryStatus.value : product.value.inventoryStatus;
            products.value[findIndexById(product.value.id)] = product.value;
            toast.add({severity:'success', summary: 'Successful', detail: 'Product Updated', life: 3000});
        }
        else {
            product.value.id = createId();
            product.value.code = createId();
            product.value.image = 'product-placeholder.svg';
            product.value.inventoryStatus = product.value.inventoryStatus ? product.value.inventoryStatus.value : 'INSTOCK';
            products.value.push(product.value);
            toast.add({severity:'success', summary: 'Successful', detail: 'Product Created', life: 3000});
        }

        productDialog.value = false;
        product.value = {};
    }
};
const editProduct = (prod) => {
    product.value = {...prod};
    productDialog.value = true;
};
const confirmDeleteProduct = (prod) => {
    product.value = prod;
    deleteProductDialog.value = true;
};
const deleteProduct = () => {
    products.value = products.value.filter(val => val.id !== product.value.id);
    deleteProductDialog.value = false;
    product.value = {};
    toast.add({severity:'success', summary: 'Successful', detail: 'Product Deleted', life: 3000});
};
const findIndexById = (id) => {
    let index = -1;
    for (let i = 0; i < products.value.length; i++) {
        if (products.value[i].id === id) {
            index = i;
            break;
        }
    }

    return index;
};
const createId = () => {
    let id = '';
    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for ( var i = 0; i < 5; i++ ) {
        id += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return id;
}
const exportCSV = () => {
    dt.value.exportCSV();
};
const confirmDeleteSelected = () => {
    deleteProductsDialog.value = true;
};
const deleteSelectedProducts = () => {
    products.value = products.value.filter(val => !selectedProducts.value.includes(val));
    deleteProductsDialog.value = false;
    selectedProducts.value = null;
    toast.add({severity:'success', summary: 'Successful', detail: 'Products Deleted', life: 3000});
};

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
                    <Button label="New" icon="pi pi-plus" severity="success" class="mr-2" @click="openNew" disabled />
                </template>

                <template #end>
                    <FileUpload mode="basic" accept="image/*" :maxFileSize="1000000" label="Import" chooseLabel="Import" class="mr-2 inline-block" disabled />
                    <Button label="Export" icon="pi pi-upload" severity="help" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable ref="dt" :value="products" v-model:selection="selectedProducts" dataKey="smid"
              :paginator="true" :rows="10" v-model:filters="filters" filterDisplay="menu"
              :globalFilterFields="['smid', 'name', 'rnaType', 'modification', 'technology', 'species', 'cto', 'access']"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown" :rowsPerPageOptions="[5,10,25]"
                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} products">
                <template #header>
                    <div class="flex justify-between">
                      <Button type="button" icon="pi pi-filter-slash" label="Clear" outlined @click="clearFilter()" />
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
                    <InputText v-model="filterModel.value" type="text" class="p-column-filter" placeholder="Search by name" />
                  </template>
                </Column>
                <Column field="rnaType" header="RNA" filterField="rnaType" style="width: 10%">
                    <template #body="{ data }">
                        {{ data.rnaType }}
                    </template>
                    <template #filter="{ filterModel }">
                      <InputText v-model="filterModel.value" type="text" class="p-column-filter" placeholder="Search by RNA type" />
                    </template>
                </Column>
                <Column field="modification" header="Modification" filterField="modification" style="width: 10%">
                  <template #body="{ data }">
                    {{ data.modification }}
                  </template>
                  <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" class="p-column-filter" placeholder="Search by modification" />
                  </template>
                </Column>
                <Column field="technology" header="Technology" filterField="technology" style="width: 20%">
                  <template #body="{ data }">
                    {{ data.technology }}
                  </template>
                  <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" class="p-column-filter" placeholder="Search by technology" />
                  </template>
                </Column>
                <Column field="species" header="Organism" filterField="species" style="width: 10%">
                  <template #body="{ data }">
                    {{ data.species}}
                  </template>
                  <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" class="p-column-filter" placeholder="Search by organism" />
                  </template>
                </Column>

                <Column field="cto" header="Cell-Organ" filterField="cto" style="width: 10%">
                  <template #body="{ data }">
                    {{ data.cto}}
                  </template>
                  <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" class="p-column-filter" placeholder="Search by organism" />
                  </template>
                </Column>


                <Column field="access" header="Access" filterField="access" :showFilterMatchModes="false" style="width: 5%">
                  <template #body="{ data }">
                    {{ data.access}}
                  </template>
                  <template #filter="{ filterModel }">
                    <Dropdown v-model="filterModel.value" :options="statuses" placeholder="Select access...">
                    </Dropdown>
                  </template>
                </Column>

                <!-- export columns shown in dialog -->
                <Column field="dateAdded" header="Added" style="display:none"></Column>
                <Column field="datePublished" header="Published" style="display:none"></Column>
                <Column field="doi" header="DOI" style="display:none"></Column>
                <Column field="pmid" header="PMID" style="display:none"></Column>
                <Column field="assembly" header="Assembly" style="display:none"></Column>
                <Column field="annotationSrc" header="Annotation" style="display:none"></Column>
                <Column field="annotationVer" header="Version" style="display:none"></Column>
                <Column field="seqPlatform" header="Seq. Platform" style="display:none"></Column>
                <Column field="basecalling" header="Basecalling" style="display:none"></Column>
                <Column field="description" header="Description" style="display:none"></Column>

                <Column :exportable="false" style="width: 5%">
                    <template #body="slotProps">
                        <Button icon="pi pi-plus" outlined rounded class="mr-2" @click="editProduct(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="productDialog" header="Additional information" :modal="true" class="p-fluid">
          <div>
            <h2>{{ product.name  }}</h2>
            <p>{{ product.description }}</p>
            <DataTable :value="products.filter(val => val.smid == product.smid)" tableStyle="min-width: 50rem">
              <Column v-for="col of columns" :key="col.field" :field="col.field" :header="col.header"></Column>
            </DataTable>
          </div>
        </Dialog>

	</div>
    </SectionLayout>
  </DefaultLayout>
</template>
