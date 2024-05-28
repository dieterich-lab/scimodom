<template>
  <SectionLayout :secondary="true">
    <div>
      <div class="px-4 py-8 md:px-6 lg:px-8 text-center">
        <h1 class="font-ham text-4xl font-semibold m-auto p-4 dark:text-white/80">
          <span>Roadmap</span>
        </h1>
        <p class="text-xl font-medium text-gray-600 p-4 dark:text-surface-400">
          We are working hard to improve Sci-ModoM, and we want to share our ideas for 2024. These
          are planned to be implemented in parallel to any regular maintenance work involving review
          of issues, PRs and support to RMaP members and the wider community.
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
              Q1
            </div>
            <div
              class="flex-1 bg-slate-400 text-white font-bold text-center p-3 text-xl border-solid rounded-md dark:text-surface-900"
            >
              Q2
            </div>
            <div
              class="flex-1 bg-slate-400 text-white font-bold text-center p-3 text-xl border-solid rounded-md dark:text-surface-900"
            >
              Q3
            </div>
            <div
              class="flex-1 bg-slate-400 text-white font-bold text-center p-3 text-xl border-solid rounded-md dark:text-surface-900"
            >
              Q4
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
                  <h2 class="text-lg font-bold mt-0 mb-2">Data Model & Query Optimization</h2>
                  <p class="mt-0 mb-3 leading-tight">Provide fast sort and filter options.</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div
                      class="border-2 border-solid border-gb-2 rounded"
                      style="width: 100%"
                    ></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Advanced Queries</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Allow to filter by genomic annotation (feature, biotype), evidence per site
                    across techniques, dataset, ...
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div
                      class="border-2 border-solid border-gb-2 rounded"
                      style="width: 100%"
                    ></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Data Annotation</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Update model, provide advanced and faster records annotation.
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div
                      class="border-2 border-solid border-gb-2 rounded"
                      style="width: 100%"
                    ></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">DB Assembly Version</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Add version management and services: data cleaning, liftover, ...
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div
                      class="border-2 border-solid border-gb-2 rounded"
                      style="width: 100%"
                    ></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Data Upload</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Harmonize upload services, data validation, setup for Q2.
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div
                      class="border-2 border-solid border-gb-2 rounded"
                      style="width: 100%"
                    ></div>
                  </div>
                </div>
              </div>
              <div class="flex-1 flex gap-3 flex-col">
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Authentication & Autorization</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Add A&A, user account, data sharing and management, ...
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div
                      class="border-2 border-solid border-gb-2 rounded"
                      style="width: 100%"
                    ></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Data Upload</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Add public API, integration with A&A, data access management.
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div
                      class="border-2 border-solid border-gb-2 rounded"
                      style="width: 100%"
                    ></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Data Download</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Provide DB dumps and customizable downloads.
                  </p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 80%"></div>
                  </div>
                </div>
              </div>
              <div class="flex-1 flex gap-3 flex-col">
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">First release</h2>
                  <p class="mt-0 mb-3 line-height-3">Add data, release version.</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 25%"></div>
                  </div>
                </div>
              </div>
              <div class="flex-1 flex gap-3 flex-col">
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Additional Annotation</h2>
                  <p class="mt-0 mb-3 line-height-3">Add RBPs, SNPs, miRNA targets, ...</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Analysis & Visualization</h2>
                  <p class="mt-0 mb-3 line-height-3">DB visualization, online data analysis.</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">Genome Browser</h2>
                  <p class="mt-0 mb-3 line-height-3">Add a genome browser to visualize data.</p>
                  <div class="border-2 border-solid border-gb-2 rounded">
                    <div class="border-2 border-solid border-gb-2 rounded" style="width: 0%"></div>
                  </div>
                </div>
                <div class="p-3 border-l-4 border-solid border-gb-2 rounded-l dark:text-white/80">
                  <h2 class="text-lg font-bold mt-0 mb-2">RNA Processing</h2>
                  <p class="mt-0 mb-3 line-height-3">
                    Think tank: integrate RNA processing (bedRMod, Sci-ModoM).
                  </p>
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
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gb-4 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Online App</h2>
                    <p class="mt-0 mb-3 leading-tight">Public API.</p>
                    <div class="border-2 border-solid border-gb-4 rounded">
                      <div
                        class="border-2 border-solid border-gb-4 rounded"
                        style="width: 100%"
                      ></div>
                    </div>
                  </div>
                  <div class="p-3 border-l-4 border-solid border-gb-4 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Data Management</h2>
                    <p class="mt-0 mb-3 leading-tight">Temporary and permanent data management.</p>
                    <div class="border-2 border-solid border-gb-4 rounded">
                      <div
                        class="border-2 border-solid border-gb-4 rounded"
                        style="width: 100%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gb-4 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Authentication & Authorization</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      Build infrastructure to support A&A, secure data storage, backup.
                    </p>
                    <div class="border-2 border-solid border-gb-4 rounded">
                      <div
                        class="border-2 border-solid border-gb-4 rounded"
                        style="width: 100%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col"></div>
                <div class="flex-1 flex gap-3 flex-col"></div>
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
                    <h2 class="text-lg font-bold mt-0 mb-2">Tables Display</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      Re-design, update layout (+intuitive, +control)
                    </p>
                    <div class="border-2 border-solid border-gg-2 rounded">
                      <div
                        class="border-2 border-solid border-gg-2 rounded"
                        style="width: 100%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-2 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Theme Update</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      UI components, design, dark theme (web browser), ...
                    </p>
                    <div class="border-2 border-solid border-gg-2 rounded">
                      <div
                        class="border-2 border-solid border-gg-2 rounded"
                        style="width: 75%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-2 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Responsive Design</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      Harmonize responsive design (smartphone, tablets, ...)
                    </p>
                    <div class="border-2 border-solid border-gg-2 rounded">
                      <div
                        class="border-2 border-solid border-gg-2 rounded"
                        style="width: 15%"
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
                <div class="flex-1 flex gap-3 flex-col"></div>
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
                    <h2 class="text-lg font-bold mt-0 mb-2">Documentation</h2>
                    <p class="mt-0 mb-3 line-height-3">Add documentation.</p>
                    <div class="border-2 border-solid border-gg-1 rounded">
                      <div
                        class="border-2 border-solid border-gg-1 rounded"
                        style="width: 75%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-1 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Feedback</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      A&A functionalities, user upload, roll up, update roadmap, ...
                    </p>
                    <div class="border-2 border-solid border-gg-1 rounded">
                      <div
                        class="border-2 border-solid border-gg-1 rounded"
                        style="width: 25%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col">
                  <div class="p-3 border-l-4 border-solid border-gg-1 rounded-l dark:text-white/80">
                    <h2 class="text-lg font-bold mt-0 mb-2">Modomics</h2>
                    <p class="mt-0 mb-3 line-height-3">
                      Link with Sci-ModoM (functionality), synchronize efforts.
                    </p>
                    <div class="border-2 border-solid border-gg-1 rounded">
                      <div
                        class="border-2 border-solid border-gg-1 rounded"
                        style="width: 10%"
                      ></div>
                    </div>
                  </div>
                </div>
                <div class="flex-1 flex gap-3 flex-col"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </SectionLayout>
</template>
