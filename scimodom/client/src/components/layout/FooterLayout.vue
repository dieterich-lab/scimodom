<script setup>
import Logo from '@/assets/images/rmap-logo.svg'
</script>

<template>
<footer class="bg-ctransparent opacity-90">
    <div class="mx-auto w-full max-w-screen-2xl p-2 py-6 lg:py-8">
        <div class="md:flex md:justify-between">
          <div class="mb-6 md:mb-0">
            <a href="https://www.trr319-rmap.de/" class="flex items-center">
                  <Logo class="h-auto mr-6" alt="RMaP Logo" />
                  <!-- <span class="self-center text-2xl font-medium whitespace-nowrap">TRR 319 RMaP</span> -->
              </a>
          </div>
          <div class="grid grid-cols-2 gap-8 sm:gap-6 sm:grid-cols-3">
              <div>
                  <h2 class="mb-6 text-base font-medium text-gray-900e">About</h2>
                  <ul class="text-gray-600 font-medium">
                    <li class="mb-4">
                      <a href="https://www.trr319-rmap.de/" class="hover:underline">TRR 319 RMaP</a>
                    </li>
                    <!-- TODO: add contact form -->
                    <li>
                      <a href="mailto:boileau@uni-heidelbergd.de" class="hover:underline">Contact us</a>
                    </li>
                  </ul>
              </div>
              <div>
                  <h2 class="mb-6 text-base font-medium text-gray-900">Resources</h2>
                  <ul class="text-gray-600 font-medium">
                    <li class="mb-4">
                    <!-- TODO: add release page or link to Github -->
                      <a href="https://noroute" class="hover:underline ">Releases</a>
                    </li>
                    <li class="mb-4">
                      <RouterLink :to="{ name: 'documentation'}">
                        <span class="hover:underline">Documentation</span>
                      </RouterLink>
                    </li>
                    <li>
                      <a href="https://genesilico.pl/modomics/" class="hover:underline">Modomics</a>
                    </li>
                  </ul>
              </div>
          </div>
      </div>
      <hr class="my-6 border-gray-200 sm:mx-auto lg:my-8" />
      <div class="sm:flex sm:items-center sm:justify-between">
        <span class="text-sm text-gray-500 sm:text-center">
          GNU Affero General Public License v3.0
        </span>
        <div class="flex mt-4 space-x-6 sm:justify-center sm:mt-0">
          <a class="text-gray-500 hover:text-gray-900"
            aria-label="GitHub"
            href="//github.com/dieterich-lab/scimodom"
            rel="noopener noreferrer"
            target="_blank"
          >
            <i class="pi pi-github text-xl" />
          </a>
          <a class="text-gray-500 hover:text-gray-900"
            aria-label="Twitter"
            href="//twitter.com/ItsRMaP1"
            rel="noopener noreferrer"
            target="_blank"
          >
            <i class="pi pi-twitter text-xl" />
          </a>
        </div>
      </div>
    </div>
</footer>
</template>
