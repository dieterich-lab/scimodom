// Contract between the interfaces of the services and the OpenAPI specs of the server
//
//   response: what the spec lets the server send must be usable as the client type
//             -> expectTypeOf<Spec>().toExtend<Client>()
//   request:  what the client sends must satisfy the spec
//             -> expectTypeOf<Client>().toExtend<Spec>()
//
// Where the client interface is a plain mirror of the schema, equality is checked
// instead (toEqualTypeOf).
import { expectTypeOf } from 'vitest'
import type { components as Attachment } from './.schemas/attachment'
import type { components as Browse } from './.schemas/browse'
import type { components as Catalog } from './.schemas/catalog'
import type { components as Comparison } from './.schemas/comparison'
import type { components as DatasetSpec } from './.schemas/dataset'
import type { components as ModificationSpec } from './.schemas/modification'
import type { components as ProjectSpec } from './.schemas/project'
import type { components as UploadSpec } from './.schemas/upload'
import type { components as UserSpec } from './.schemas/user'

import type { Assembly } from '@/services/assembly'
import type { BamFile } from '@/services/bamfile'
import type { BioTypesResponse } from '@/services/biotype'
import type { Chrom } from '@/services/chrom'
import type { ClosestRecord, IntersectRecord, SubtractRecord } from '@/services/comparison'
import type { Dataset, DatasetSummaryResponse, MayChangeDatasetResponse } from '@/services/dataset'
import type { UploadResponse } from '@/services/dataset-upload'
import type { DetectionMethod } from '@/services/detection-method'
import type { FeaturesResponse } from '@/services/feature'
import type {
  DatasetPostRequest,
  DatasetPostResponse,
  ProjectMetaData,
  ProjectOrganism,
  ProjectPostRequest,
  ProjectPostResponse
} from '@/services/management'
import type {
  GenomicContextResponse,
  ModificationResponse,
  SiteSummaryResponse,
  SiteWiseResponse,
  TargetSitesResponse
} from '@/services/modification'
import type { Modomics } from '@/services/modomics'
import type { Project } from '@/services/project'
import type { RnaType } from '@/services/rna-type'
import type { Selection } from '@/services/selection'
import type { Taxa } from '@/services/taxa'
import type { PostFileResponse } from '@/services/upload'
import type { LoginResponse } from '@/services/user'

// schemas that are arrays in the specs: the type of one item
type Item<T> = T extends readonly (infer U)[] ? U : never

// --- attachment ---

expectTypeOf<Item<Attachment['schemas']['BamFileList']>>().toEqualTypeOf<BamFile>()

// --- browse ---

expectTypeOf<Item<Browse['schemas']['Project']>>().toEqualTypeOf<Project>()

// --- catalog ---

// Taxon and Selection use toExtend: the client does not consume `phylum`
// (optional because of Selection), the spec always returns it (Taxa).

expectTypeOf<Item<Catalog['schemas']['RNAType']>>().toEqualTypeOf<RnaType>()
expectTypeOf<Item<Catalog['schemas']['Taxon']>>().toExtend<Taxa>()
expectTypeOf<Item<Catalog['schemas']['Modomics']>>().toEqualTypeOf<Modomics>()
expectTypeOf<Item<Catalog['schemas']['Method']>>().toEqualTypeOf<DetectionMethod>()
expectTypeOf<Item<Catalog['schemas']['Selection']>>().toExtend<Selection>()
expectTypeOf<Item<Catalog['schemas']['Chromosome']>>().toEqualTypeOf<Chrom>()
expectTypeOf<Item<Catalog['schemas']['Assembly']>>().toEqualTypeOf<Assembly>()
expectTypeOf<Catalog['schemas']['Biotype']>().toEqualTypeOf<BioTypesResponse>()
expectTypeOf<Catalog['schemas']['Feature']>().toEqualTypeOf<FeaturesResponse>()
expectTypeOf<Catalog['schemas']['Gene']>().toEqualTypeOf<string[]>()

// --- comparison ---

expectTypeOf<Comparison['schemas']['Intersect']>().toEqualTypeOf<{ records: IntersectRecord[] }>()
expectTypeOf<Comparison['schemas']['Closest']>().toEqualTypeOf<{ records: ClosestRecord[] }>()
expectTypeOf<Comparison['schemas']['Subtract']>().toEqualTypeOf<{ records: SubtractRecord[] }>()

// --- dataset ---

expectTypeOf<Item<DatasetSpec['schemas']['Dataset']>>().toEqualTypeOf<Dataset>()
expectTypeOf<DatasetSpec['schemas']['Count']>().toEqualTypeOf<DatasetSummaryResponse>()
expectTypeOf<DatasetSpec['schemas']['Permission']>().toEqualTypeOf<MayChangeDatasetResponse>()
expectTypeOf<DatasetSpec['schemas']['DatasetCreated']>().toEqualTypeOf<DatasetPostResponse>()
expectTypeOf<DatasetSpec['schemas']['AddDatasetBody']>().toEqualTypeOf<DatasetPostRequest>()

// --- modification ---

expectTypeOf<ModificationSpec['schemas']['Search']>().toEqualTypeOf<ModificationResponse>()
expectTypeOf<ModificationSpec['schemas']['Count']>().toEqualTypeOf<SiteSummaryResponse>()
expectTypeOf<ModificationSpec['schemas']['Site']>().toEqualTypeOf<SiteWiseResponse>()
expectTypeOf<ModificationSpec['schemas']['Context']>().toEqualTypeOf<GenomicContextResponse>()
expectTypeOf<ModificationSpec['schemas']['BED6']>().toEqualTypeOf<TargetSitesResponse>()

// --- project ---

// spec accepts null on date_published, doi, pmid and note, client omits them and never sends null

expectTypeOf<ProjectSpec['schemas']['Request']>().toEqualTypeOf<ProjectPostResponse>()
expectTypeOf<ProjectPostRequest>().toExtend<ProjectSpec['schemas']['ProjectTemplate']>()

// --- upload ---

expectTypeOf<UploadSpec['schemas']['Upload']>().toEqualTypeOf<PostFileResponse>()
expectTypeOf<UploadSpec['schemas']['Upload']>().toEqualTypeOf<UploadResponse>()

// --- user ---

expectTypeOf<UserSpec['schemas']['Token']>().toEqualTypeOf<LoginResponse>()
