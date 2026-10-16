import type { DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTPAuth } from '@/services/API'

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

interface DatasetPostResponse {
  dataset_id: string
}

interface ProjectPostResponse {
  request_id: string
}

async function postDataset(
  request: DatasetPostRequest,
  dialogState: DialogStateStore
): Promise<DatasetPostResponse> {
  return await handleRequestWithErrorReporting(
    HTTPAuth.post<DatasetPostResponse>('/datasets', request),
    `Failed to post dataset`,
    dialogState
  )
}

async function postProject(
  request: ProjectPostRequest,
  dialogState: DialogStateStore
): Promise<ProjectPostResponse> {
  return await handleRequestWithErrorReporting(
    HTTPAuth.post<ProjectPostResponse>('/projects/requests', request),
    `Failed to post project request`,
    dialogState
  )
}

export {
  type DatasetPostRequest,
  type DatasetPostResponse,
  type ProjectPostRequest,
  type ProjectPostResponse,
  type ProjectInfo,
  type ProjectOrganism,
  type ProjectMetaData,
  type ExternalSource,
  postDataset,
  postProject
}
