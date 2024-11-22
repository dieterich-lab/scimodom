import type { DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTPSecure } from '@/services/API'

interface DatasetPostRequest {
  smid: string
  file_id: string
  rna_type: string
  modification_id: number[]
  organism_id: number
  assembly_id: number
  technology_id: number
  title: string
}

interface ProjectOrganism {
  taxa_id: number
  cto: string
  assembly_name: string
  assembly_id: string
}

interface ProjectMetaData {
  rna: string
  modomics_id: string
  tech: string
  method_id: string
  note: string
  organism: ProjectOrganism
}

interface ExternalSource {
  doi?: string
  pmid?: number
}

interface ProjectInfo {
  title: string
  summary: string
  contact_name: string
  contact_institution: string
  contact_email: string
  date_published: string
}

interface ProjectPostRequest extends ProjectInfo {
  external_sources: ExternalSource[]
  metadata: ProjectMetaData[]
}

async function postDataset(
  request: DatasetPostRequest,
  dialogState: DialogStateStore
): Promise<void> {
  return await handleRequestWithErrorReporting<void>(
    HTTPSecure.post('/management/dataset', request),
    `Failed to post dataset`,
    dialogState
  )
}

async function postProject(request: ProjectPostRequest, dialogState: DialogStateStore) {
  return await handleRequestWithErrorReporting<void>(
    HTTPSecure.post('/management/project', request),
    `Failed to post project`,
    dialogState
  )
}

export {
  type DatasetPostRequest,
  type ProjectPostRequest,
  type ProjectInfo,
  type ProjectOrganism,
  type ProjectMetaData,
  type ExternalSource,
  postDataset,
  postProject
}
