<script setup lang="ts">
import SectionLayout from '@/components/layout/SectionLayout.vue'
</script>
<template>
  <SectionLayout :secondary="true">
    <div>
      <div class="px-4 py-8 md:px-6 lg:px-8 text-center">
        <h1 class="font-ham text-4xl font-semibold m-auto p-4 dark:text-white/80">
          <span>Roadmap</span>
        </h1>
        <p class="text-xl font-medium text-gray-600 p-4 dark:text-surface-400">
          We are working hard to improve Sci-ModoM, and we want to share our ideas for 2025/2026.
          These are planned to be implemented in parallel to any regular maintenance work involving
          review of issues, PRs and support to the wider community.
        </p>
      </div>
      <!-- ROADMAP ---- -->
      <div class="overflow-auto">
        <div class="min-w-min">
          <div class="flex gap-3 mb-3">
            <div class="flex shrink-0 w-56"></div>
            <div
              class="flex-1 bg-slate-400 text-white font-bold text-center p-3 text-xl border-solid rounded-md dark:text-surface-900"
            >
              Q1/Q2
            </div>
            <div
              class="flex-1 bg-slate-400 text-white font-bold text-center p-3 text-xl border-solid rounded-md dark:text-surface-900"
            >
              Q3/Q4
            </div>
            <div
              class="flex-1 bg-slate-400 text-white font-bold text-center p-3 text-xl border-solid rounded-md dark:text-surface-900"
            >
              Q5/Q6
            </div>
            <div
              class="flex-1 bg-slate-400 text-white font-bold text-center p-3 text-xl border-solid rounded-md dark:text-surface-900"
            >
              Q7/Q8
            </div>
          </div>
          <!-- FUNCTIONALITY ----------- -->
          <div class="flex flex-col gap-3">
            <div class="flex gap-3 border-1 pb-3">
              <div
                class="flex shrink-0 p-3 bg-gb-2 text-white border-solid rounded-md font-bold text-lg items-center justify-center w-56 dark:text-surface-900"
              >
                Functionality
              </div>
              <div class="flex-1 flex gap-3 flex-col">
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Data Annotation & Features</h2>
                  <p class="mt-0 mb-3 leading-tight">
                    Interactome resources, sequence context, and more ...
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 15%"></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Database</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Add version (assembly, annotation) and cache management, upgrade DB to latest
                    version.
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
              </div>
              <div class="flex-1 flex gap-3 flex-col">
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Assembly & Annotation</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Add more species (model organisms) and data.
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
              </div>
              <div class="flex-1 flex gap-3 flex-col">
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">RNA Types</h2>
                  <p class="mt-0 mb-3 line-height-3">Add more RNA types (tRNA, rRNA).</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">RNA Processing</h2>
                  <p class="mt-0 mb-3 line-height-3">Integrate RNA processing.</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
              </div>
              <div class="flex-1 flex gap-3 flex-col">
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Data Download</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Provide GUI and API for customizable downloads.
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Genome Browser</h2>
                  <p class="mt-0 mb-3 line-height-3">Database visualization locally.</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
              </div>
            </div>
            <!-- INFRASTRUCTURE ------------------ -->
            <div class="flex flex-col gap-3">
              <div class="flex gap-3 border-1 pb-3">
                <div
                  class="flex shrink-0 p-3 bg-gb-4 text-white border-solid rounded-md font-bold text-lg items-center justify-center w-56 dark:text-surface-900"
                >
                  Infrastructure
                </div>
                <div class="flex-1 flex gap-3 flex-col"></div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gb-4 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">REST API</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      Extend and validate API (data management and more).
                    </p>
                    <div class="border-2 border-solid border-gb-4 rounded">
                      <div
                        class="border-2 border-solid border-gb-4 rounded"
                        style="width: 15%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gb-4 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Data Management</h2>
                    <p class="mt-0 mb-3 leading-tight">File storage (formats).</p>
                    <div class="border-2 border-solid border-gb-4 rounded">
                      <div
                        class="border-2 border-solid border-gb-4 rounded"
                        style="width: 15%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gb-4 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Database mirroring</h2>
                    <p class="mt-0 mb-3 line-height-3">Develop infrastructure for mirroring.</p>
                    <div class="border-2 border-solid border-gb-4 rounded">
                      <div
                        class="border-2 border-solid border-gb-4 rounded"
                        style="width: 0%"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- DESIGN ------------------ -->
            <div class="flex flex-col gap-3">
              <div class="flex gap-3 border-1 pb-3">
                <div
                  class="flex shrink-0 p-3 bg-gg-2 text-white border-solid rounded-md font-bold text-lg items-center justify-center w-56 dark:text-surface-900"
                >
                  Design
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-2 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Theme update</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      UI components, design, general improvements.
                    </p>
                    <div class="border-2 border-solid border-gg-2 rounded">
                      <div
                        class="border-2 border-solid border-gg-2 rounded"
                        style="width: 15%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col"></div>
                <div class="flex-1 flex gap-3 flex-col"></div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-2 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Responsive Design</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      Harmonize responsive design (smartphone, tablets, ...)
                    </p>
                    <div class="border-2 border-solid border-gg-2 rounded">
                      <div
                        class="border-2 border-solid border-gg-2 rounded"
                        style="width: 5%"
                      ></div>
                    </div>
                  </div>
                  <div class="p-3 border-l-4 border-solid border-gg-2 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Web Accessibility</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      Improve accessibility (navigation, color, screen reader, ...)
                    </p>
                    <div class="border-2 border-solid border-gg-2 rounded">
                      <div
                        class="border-2 border-solid border-gg-2 rounded"
                        style="width: 0%"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- SHOWCASE ------------------ -->
            <div class="flex flex-col gap-3">
              <div class="flex gap-3 border-1 pb-3">
                <div
                  class="flex shrink-0 p-3 bg-gg-1 text-white border-solid rounded-md font-bold text-lg items-center justify-center w-56 dark:text-surface-900"
                >
                  Community
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-1 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">bedRMod</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      bedRMod specs and tools community development (euf-specs).
                    </p>
                    <div class="border-2 border-solid border-gg-1 rounded">
                      <div
                        class="border-2 border-solid border-gg-1 rounded"
                        style="width: 20%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-1 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Modomics</h2>
                    <p class="mt-0 mb-3 line-height-3">Integration with Modomics (RNome project)</p>
                    <div class="border-2 border-solid border-gg-1 rounded">
                      <div
                        class="border-2 border-solid border-gg-1 rounded"
                        style="width: 0%"
                      ></div>
                    </div>
                  </div>
                </div>
                <!-- <div class="flex-1 flex gap-3 flex-col"></div> -->
                <div class="flex-1 flex gap-3 flex-col"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </SectionLayout>
</template>
