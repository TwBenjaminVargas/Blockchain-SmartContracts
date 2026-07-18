<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="10" lg="8" class="pa-4">
        
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <div class="d-flex justify-center mb-6 toggle-wrapper">
            <v-btn-toggle
              v-model="currentTab"
              mandatory
              color="indigo-darken-1"
              variant="text"
              class="custom-toggle"
            >
              <v-btn value="creators" class="font-weight-bold">Creadores</v-btn>
              <v-btn value="users" class="font-weight-bold">Usuarios</v-btn>
              <v-btn value="requests" class="font-weight-bold">
                Solicitudes
                <v-badge v-if="totalRequests > 0" :content="totalRequests" color="error" inline class="ms-1"></v-badge>
              </v-btn>
              <v-btn value="calls" class="font-weight-bold">Llamados</v-btn>
            </v-btn-toggle>
          </div>

          <h2 class="text-h4 font-weight-bold text-center text-slate-dark mb-4">
            {{ panelTitle }}
          </h2>

          <v-card variant="flat" class="bg-slate-light pa-4 rounded-lg mb-4 search-box">
            <v-row dense align="center">
              <v-col cols="12" :sm="currentTab === 'calls' ? '6' : '12'" :md="currentTab === 'calls' ? '3' : '12'">
                <v-text-field
                  v-model="searchQuery"
                  clearable
                  density="compact"
                  variant="outlined"
                  bg-color="white"
                  color="indigo-darken-1"
                  hide-details
                  prepend-inner-icon="mdi-magnify"
                  :label="currentTab === 'calls' ? 'Buscar por título o ID...' : 'Buscar por nombre o dirección (0x...)'"
                ></v-text-field>
              </v-col>

              <template v-if="currentTab === 'calls'">
                <v-col cols="12" sm="6" md="3">
                  <v-text-field
                    v-model="searchCreator"
                    clearable
                    density="compact"
                    variant="outlined"
                    bg-color="white"
                    color="indigo-darken-1"
                    hide-details
                    prepend-inner-icon="mdi-account-search-outline"
                    label="Dirección del creador (0x...)"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-select
                    v-model="filterState"
                    :items="stateOptions"
                    label="Filtrar por Estado"
                    density="compact"
                    variant="outlined"
                    bg-color="white"
                    color="indigo-darken-1"
                    hide-details
                    clearable
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-select
                    v-model="filterTimeline"
                    :items="timelineOptions"
                    label="Fecha de Cierre"
                    density="compact"
                    variant="outlined"
                    bg-color="white"
                    color="indigo-darken-1"
                    hide-details
                    clearable
                  ></v-select>
                </v-col>
              </template>
            </v-row>
          </v-card>
          <div v-if="currentTab === 'creators'" class="scrollable-containerpe">
            <div v-if="filteredCreators.registered.length === 0 && filteredCreators.external.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No se encontraron creadores que coincidan con la búsqueda</p>
            </div>
              <v-expansion-panels v-else variant="accordion" class="custom-panels">
                <!-- Creadores Registrados -->
                <v-expansion-panel 
                  v-for="(creator, index) in filteredCreators.registered" 
                  :key="creator.address" 
                  :class="['creator-row mb-3 rounded-lg overflow-hidden', creator.state === 'pending' ? 'archived-row' : '']" 
                  elevation="1"
                >
                  <v-expansion-panel-title class="py-4">
                    <v-avatar :color="creator.state === 'pending' ? 'grey' : getRandomColor(index)" size="48" class="me-4 shadow-sm text-white font-weight-bold">
                      {{ creator.name.charAt(0).toUpperCase() }}
                    </v-avatar>
                    <div class="text-left w-100 d-flex justify-space-between align-center pe-4">
                      <div>
                        <div class="text-subtitle-1 font-weight-bold text-slate-dark">
                          {{ creator.name }}
                          <span v-if="isCurrentUser(creator.address)" class="text-caption text-indigo font-weight-bold ms-1">(Tú)</span>
                        </div>
                        <!-- NUEVO: Dominio debajo del nombre -->
                        <div class="text-caption text-indigo-darken-1 font-weight-bold d-flex align-center mt-0.5">
                          <v-icon icon="mdi-dns-outline" size="12" class="me-1"></v-icon>
                          {{ creator.domain || 'sin-dominio.eth' }}
                        </div>
                      </div>
                      <v-chip v-if="creator.state === 'pending'" color="grey" size="small" variant="flat" class="font-weight-bold text-uppercase">
                        Archivado
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>

                  <v-expansion-panel-text class="text-left pt-2 text-slate-medium bg-slate-lighten-5">
                    <div class="technical-details d-flex flex-column gap-3 text-body-2 text-grey-darken-3 mb-2">
                      
                      <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                        <div class="text-truncate pr-2">
                          <v-icon icon="mdi-account-circle" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                          <strong>Address del Creador:</strong>  
                          <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ creator.address }}</span>
                        </div>
                        <v-btn 
                          icon="mdi-content-copy" 
                          variant="text" 
                          size="x-small" 
                          color="indigo-darken-1"
                          title="Copiar Address"
                          @click="copyToClipboard(creator.address, 'Address del Creador')"
                        ></v-btn>
                      </div>

                      <div class="bg-white pa-3 rounded-lg border">
                        <strong class="text-slate-dark">Descripción:</strong> 
                        <p class="text-body-2 text-slate-medium mt-1 mb-0 italic-text">{{ creator.description || 'Sin descripción provista' }}</p>
                      </div>
                      
                      <div class="d-flex align-center bg-white pa-2 rounded-lg border text-caption">
                        <v-icon icon="mdi-counter" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Nonce:</strong>
                        <span class="text-mono ms-2 bg-grey-lighten-3 px-2 py-0.5 rounded">{{ creator.nonce }}</span>
                      </div>
                    </div>

                    <div class="text-right mt-3">
                      <v-chip v-if="isCurrentUser(creator.address)" color="indigo-lighten-4" text-color="indigo-darken-4" size="small" class="font-weight-bold">
                        Administrador Activo
                      </v-chip>
                      <v-chip v-else-if="creator.state === 'pending'" color="grey-darken-1" variant="tonal" size="small" class="font-weight-bold">
                        Acciones deshabilitadas (Creador Archivado)
                      </v-chip>
                      <v-btn 
                        v-else
                        color="error" 
                        variant="tonal" 
                        size="small" 
                        class="font-weight-bold" 
                        :loading="isActionLoading === creator.address" 
                        @click="handleAction('unauthorize', creator.address)"
                      > 
                        Desautorizar
                      </v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Creadores Externos -->
                <v-expansion-panel v-for="address in filteredCreators.external" :key="address" class="creator-row external-row mb-3 rounded-lg overflow-hidden" elevation="1">
                  <v-expansion-panel-title class="py-4">
                    <v-avatar color="grey-lighten-2" size="48" class="me-4 border-dashed text-grey-darken-2">
                      <v-icon icon="mdi-help-outline" size="24"></v-icon>
                    </v-avatar>
                    <div class="text-left">
                      <div class="text-subtitle-1 font-weight-bold text-grey-darken-3">
                        Creador Externo
                        <span v-if="isCurrentUser(address)" class="text-caption text-indigo font-weight-bold ms-1">(Tú)</span>
                      </div>
                      <div class="text-caption text-grey-darken-1 italic-text">Sin dominio disponible</div>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text class="text-left pt-2 text-grey-darken-2 bg-slate-lighten-5">
                    <div class="technical-details d-flex flex-column gap-3 text-body-2 mb-2">
                      <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                        <div class="text-truncate pr-2">
                          <v-icon icon="mdi-account-alert-outline" size="16" class="me-2 text-amber-darken-2"></v-icon>
                          <strong>Address (Wallet Externa):</strong>  
                          <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ address }}</span>
                        </div>
                        <v-btn 
                          icon="mdi-content-copy" 
                          variant="text" 
                          size="x-small" 
                          color="amber-darken-3"
                          title="Copiar Address"
                          @click="copyToClipboard(address, 'Address Externa')"
                        ></v-btn>
                      </div>
                      <p class="italic-text mb-0 pa-2 bg-white rounded-lg border text-caption">Este creador se ha registrado por otros medios y no se posee información al respecto.</p>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>      
          </div>

          <div v-else-if="currentTab === 'users'" class="scrollable-containerpe">
            <div v-if="searchedUsers.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No hay usuarios activos que coincidan.</p>
            </div>

              <v-expansion-panels v-else variant="accordion" class="custom-panels">
                <v-expansion-panel
                  v-for="(user, index) in searchedUsers"
                  :key="user.address"
                  class="creator-row mb-3 rounded-lg overflow-hidden"
                  elevation="1"
                >
                  <v-expansion-panel-title class="py-4">
                    <v-avatar :color="getRandomColor(index)" size="48" class="me-4 text-white font-weight-bold">
                      {{ user.name.charAt(0).toUpperCase() }}
                    </v-avatar>
                    <div class="text-left w-100 d-flex justify-space-between align-center pe-4">
                      <div>
                        <div class="text-subtitle-1 font-weight-bold text-slate-dark">
                          {{ user.name }}
                          <span v-if="isCurrentUser(user.address)" class="text-caption text-indigo font-weight-bold ms-1">(Tú)</span>
                        </div>
                        <div class="text-caption text-indigo-darken-1 font-weight-bold d-flex align-center mt-0.5">
                          <v-icon icon="mdi-dns-outline" size="12" class="me-1"></v-icon>
                          {{ user.domain || 'sin-dominio.eth' }}
                        </div>
                      </div>
                      <v-chip color="success" size="small" variant="flat" class="font-weight-bold text-uppercase">
                        {{ user.state }}
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>
                  
                  <v-expansion-panel-text class="text-left pt-2 text-slate-medium bg-slate-lighten-5">
                    <div class="technical-details d-flex flex-column gap-3 text-body-2 text-grey-darken-3 mb-2">
                      
                      <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                        <div class="text-truncate pr-2">
                          <v-icon icon="mdi-wallet" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                          <strong>Address del Usuario:</strong>  
                          <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ user.address }}</span>
                        </div>
                        <v-btn 
                          icon="mdi-content-copy" 
                          variant="text" 
                          size="x-small" 
                          color="indigo-darken-1"
                          title="Copiar Address"
                          @click="copyToClipboard(user.address, 'Address del Usuario')"
                        ></v-btn>
                      </div>

                      <div class="bg-white pa-3 rounded-lg border">
                        <strong class="text-slate-dark">Descripción:</strong> 
                        <p class="text-body-2 text-slate-medium mt-1 mb-0 italic-text">{{ user.description || 'Sin descripción provista' }}</p>
                      </div>
                      
                      <div class="d-flex align-center bg-white pa-2 rounded-lg border text-caption">
                        <v-icon icon="mdi-counter" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Nonce:</strong>
                        <span class="text-mono ms-2 bg-grey-lighten-3 px-2 py-0.5 rounded">{{ user.nonce }}</span>
                      </div>
                    </div>
                    
                    <div class="text-right mt-3">
                      <v-chip v-if="isCurrentUser(user.address)" color="indigo-lighten-4" text-color="indigo-darken-4" size="small" class="font-weight-bold">
                        Administrador Activo (Tú)
                      </v-chip>
                      <v-btn 
                        v-else
                        color="error" 
                        variant="tonal" 
                        size="small" 
                        class="font-weight-bold" 
                        :loading="isActionLoading === user.address" 
                        @click="handleAction('unauthorize', user.address)"
                      > 
                        Desautorizar
                      </v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
          </div>

          <div v-else-if="currentTab === 'requests'" class="scrollable-containerpe">
            <div v-if="filteredRequests.local.length === 0 && filteredRequests.external.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No hay solicitudes de autorización que coincidan.</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              <!-- Solicitudes Locales -->
              <v-expansion-panel v-for="(req, index) in filteredRequests.local" :key="req.address" class="creator-row mb-3 rounded-lg overflow-hidden" elevation="1">
                <v-expansion-panel-title class="py-4">
                  <v-avatar :color="getRandomColor(index)" size="48" class="me-4 text-white font-weight-bold">
                    {{ req.name.charAt(0).toUpperCase() }}
                  </v-avatar>
                  <div class="text-left w-100 d-flex justify-space-between align-center pe-4">
                    <div>
                      <div class="text-subtitle-1 font-weight-bold text-slate-dark">{{ req.name }}</div>
                      <div class="text-caption text-indigo-darken-1 font-weight-bold d-flex align-center mt-0.5">
                        <v-icon icon="mdi-dns-outline" size="12" class="me-1"></v-icon>
                        {{ req.domain || 'sin-dominio.eth' }}
                      </div>
                    </div>
                    <v-chip 
                      :color="req.state === 'pending' ? 'warning' : req.state === 'registered' ? 'success' : 'grey'" 
                      variant="flat" 
                      size="small" 
                      class="font-weight-bold text-uppercase"
                    >
                      {{ req.state }}
                    </v-chip>
                  </div>
                </v-expansion-panel-title>
                
                <v-expansion-panel-text class="text-left pt-2 text-slate-medium bg-slate-lighten-5">
                  <div class="technical-details d-flex flex-column gap-3 text-body-2 text-grey-darken-3 mb-2">
                    
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-account-arrow-left" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Address a Autorizar:</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ req.address }}</span>
                      </div>
                      <v-btn 
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="indigo-darken-1"
                        title="Copiar Address"
                        @click="copyToClipboard(req.address, 'Address del Solicitante')"
                      ></v-btn>
                    </div>

                    <div class="bg-white pa-3 rounded-lg border">
                      <strong class="text-slate-dark">Descripción de Motivo:</strong> 
                      <p class="text-body-2 text-slate-medium mt-1 mb-0 italic-text">{{ req.description || 'Sin descripción provista' }}</p>
                    </div>
                  </div>

                  <div class="d-flex justify-end gap-2 mt-3">
                    <v-btn color="error" variant="text" class="font-weight-bold" :disabled="isActionLoading === req.address" @click="handleAction('unauthorize', req.address)">Rechazar</v-btn>
                    <v-btn color="success" variant="flat" class="font-weight-bold" :loading="isActionLoading === req.address" @click="handleAction('authorize', req.address)">Autorizar</v-btn>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- Solicitudes Externas -->
              <v-expansion-panel v-for="address in filteredRequests.external" :key="address" class="creator-row external-row mb-3 rounded-lg overflow-hidden" elevation="1">
                <v-expansion-panel-title class="py-4">
                  <v-avatar color="grey-lighten-2" size="48" class="me-4 border-dashed text-grey-darken-2">
                    <v-icon icon="mdi-help-network-outline" size="24"></v-icon>
                  </v-avatar>
                  <div class="text-left">
                    <div class="text-subtitle-1 font-weight-bold text-grey-darken-3">Solicitud Externa</div>
                    <div class="text-caption text-grey-darken-1 italic-text">Sin dominio disponible</div>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="text-left pt-2 text-grey-darken-2 bg-slate-lighten-5">
                  <div class="technical-details d-flex flex-column gap-3 text-body-2 mb-2">
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-account-alert-outline" size="16" class="me-2 text-amber-darken-2"></v-icon>
                        <strong>Address Solicitante Onchain:</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ address }}</span>
                      </div>
                      <v-btn 
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="amber-darken-3"
                        title="Copiar Address"
                        @click="copyToClipboard(address, 'Address Externa')"
                      ></v-btn>
                    </div>
                    <div class="pa-2 bg-white rounded-lg border text-caption italic-text">
                      Este usuario se ha registrado Onchain pero no se ha registrado en el sistema local todavía.
                    </div>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div v-else class="scrollable-containerpe">
            <div v-if="loadingCalls" class="d-flex flex-column align-center justify-center py-12">
              <v-progress-circular indeterminate color="indigo-darken-1" size="50" width="4" class="mb-4"></v-progress-circular>
              <p class="text-body-1 text-grey-darken-1 font-weight-medium">Sincronizando catálogo de llamados globales...</p>
            </div>

            <div v-else-if="searchedGlobalCalls.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No se encontraron llamados que coincidan con los filtros aplicados</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              <v-expansion-panel 
                v-for="call in searchedGlobalCalls" 
                :key="call.callId" 
                :class="['creator-row mb-3 rounded-lg overflow-hidden', !call.isInternal ? 'external-row' : '']" 
                elevation="1"
              >
                <v-expansion-panel-title class="py-4">
                  <v-row no-gutters class="align-center w-100 min-w-0">
                    <v-col cols="12" md="7" class="d-flex flex-column text-left min-w-0 pr-4">
                      <div class="d-flex align-center flex-wrap gap-2 mb-2">
                        <!-- Badge de Dominio ENS del llamado (Solo lectura) -->
                        <span v-if="call.domain" class="text-mono text-body-2 font-weight-bold text-indigo-darken-1 bg-indigo-lighten-5 px-2 py-0.5 rounded d-inline-flex align-center">
                          <v-icon icon="mdi-dns" size="14" class="me-1"></v-icon>
                          {{ call.domain }}
                        </span>
                        <v-chip
                          v-if="call.domain"
                          size="small"
                          :color="domainLinkedStatus[call.callId] ? 'success' : 'error'"
                          variant="tonal"
                          class="font-weight-bold text-caption"
                        >
                          <v-icon :icon="domainLinkedStatus[call.callId] ? 'mdi-cloud-check' : 'mdi-cloud-alert'" size="14" class="me-1"></v-icon>
                          {{ domainLinkedStatus[call.callId] ? 'ENS Vinculado' : 'ENS No Vinculado' }}
                        </v-chip>
                        
                        <v-chip v-if="call.isInternal" size="small" color="success" variant="flat" class="font-weight-bold text-caption">
                          Sincronizado
                        </v-chip>
                        <v-chip v-else size="small" color="amber-darken-2" variant="flat" class="font-weight-bold text-caption">
                          Blockchain Pura
                        </v-chip>

                        <v-chip v-if="call.isInternal && call.state" size="small" color="indigo-lighten-1" variant="outlined" class="font-weight-bold text-caption">
                          {{ call.state }}
                        </v-chip>
                      </div>

                      <div class="text-subtitle-1 font-weight-bold text-slate-dark text-truncate w-100">
                        {{ call.title || 'Convocatoria Externa (Sin metadatos)' }}
                      </div>
                    </v-col>

                    <v-col cols="12" md="5" class="text-md-right mt-2 mt-md-0 text-body-2">
                      <template v-if="isCallExpired(call.closingTime)">
                        <span class="text-error font-weight-bold">
                          <v-icon icon="mdi-clock-alert-outline" size="16" class="me-1 text-error"></v-icon>
                          Cerró el: {{ formatUnixTimestamp(call.closingTime) }}
                        </span>
                      </template>
                      <template v-else>
                        <span class="text-success font-weight-medium">
                          <v-icon icon="mdi-clock-outline" size="16" class="me-1 text-success"></v-icon>
                          Cierra el: <strong class="text-slate-dark">{{ formatUnixTimestamp(call.closingTime) }}</strong>
                        </span>
                      </template>
                    </v-col>
                  </v-row>
                </v-expansion-panel-title>

                <v-expansion-panel-text class="text-left pt-2 text-slate-medium bg-slate-lighten-5">
                  <h4 class="text-subtitle-1 font-weight-bold text-slate-dark mb-1">
                    {{ call.title || 'Convocatoria Externa' }}
                  </h4>
                  <p class="text-body-2 text-slate-medium mb-3">
                    {{ call.description || 'Este llamado reside únicamente en los nodos de la Blockchain y no cuenta con metadatos extendidos guardados en la base de datos de la API.' }}
                  </p>
                  
                  <v-divider class="mb-3"></v-divider>

                  <div class="technical-details d-flex flex-column gap-3 text-body-2 text-grey-darken-3 mb-4">
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-file-sign" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Contract Address:</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ call.contractAddress || call.address || '0x0000000000000000000000000000000000000000' }}</span>
                      </div>
                      <v-btn 
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="indigo-darken-1"
                        title="Copiar Contract Address"
                        @click="copyToClipboard(call.contractAddress || call.address || '0x0000000000000000000000000000000000000000', 'Contract Address')"
                      ></v-btn>
                    </div>
                  
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-account-circle" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Creador (Wallet):</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ call.creator }}</span>
                      </div>
                      <v-btn 
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="indigo-darken-1"
                        title="Copiar Creador"
                        @click="copyToClipboard(call.creator, 'Wallet del Creador')"
                      ></v-btn>
                    </div>
                  
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-identifier" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Call ID:</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ call.callId }}</span>
                      </div>
                      <v-btn 
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="indigo-darken-1"
                        title="Copiar Call ID"
                        @click="copyToClipboard(call.callId, 'Call ID')"
                      ></v-btn>
                    </div>
                  </div>

                  <!-- BOTÓN ÚNICO DE NAVEGACIÓN -->
                  <div class="d-flex justify-end mt-4 pt-2 border-top">
                      <v-btn
                        color="indigo-darken-1"
                        variant="elevated"
                        class="rounded-lg font-weight-bold"
                        @click="$router.push({ name: 'call-proposals', params: { callId: call.callId } })"
                      >
                        Ver propuestas
                      </v-btn>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

        </v-card>
      </v-col>
    </v-row>

   <v-snackbar 
      v-model="snackbar.show" 
      :color="snackbar.color || 'success'" 
      elevation="4" 
      location="top right" 
      :timeout="4000"
    >
      <div class="d-flex align-center">
        <v-icon 
          :icon="snackbar.color === 'error' ? 'mdi-alert-circle-outline' : 'mdi-check-circle-outline'" 
          class="me-3" 
          size="22"
        ></v-icon>
        <span class="font-weight-medium text-body-2">{{ snackbar.message }}</span>
      </div>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ethers } from 'ethers'
import { ASSETS } from '../config/constants'
import { useWalletStore } from '../stores/wallet'
import { 
  getCreators, 
  getUsers, 
  getAuthorizationRequests, 
  authorizeUser, 
  unauthorizeUser, 
  getContractAddress, 
  getAdminNonce,
  getGlobalCalls
} from '../services/api' 

import {resolveDomain } from '../services/ens'
const walletStore = useWalletStore()

const backgroundImage = ASSETS.adminBg
const currentTab = ref('creators')
const isActionLoading = ref(null)
const loadingCalls = ref(false)

const question_svg = ASSETS.questionIcon

const snackbar = ref({
  show: false,
  message: ''
})

// Variables de Búsqueda y Filtrado Extendido
const searchQuery = ref('')
const searchCreator = ref('')
const filterState = ref(null)
const filterTimeline = ref(null)

const stateOptions = [
  { title: 'Todos los estados', value: null },
  { title: 'Sincronizados (Base Local)', value: 'internal' },
  { title: 'Blockchain Pura', value: 'external' },
  { title: 'Estado: CREATED', value: 'CREATED' },
  { title: 'Estado: PENDING', value: 'PENDING' }
]

const timelineOptions = [
  { title: 'Cualquier fecha', value: null },
  { title: 'Vigentes / Abiertos', value: 'open' },
  { title: 'Expirados / Cerrados', value: 'expired' }
]

const registeredCreators = ref([])
const externalCreators = ref([])
const allUsers = ref([])
const localRequests = ref([])
const externalRequests = ref([])

const internalGlobalCalls = ref([])
const externalGlobalCalls = ref([])
const domainLinkedStatus = ref({})
const totalRequests = computed(() => localRequests.value.length + externalRequests.value.length)

const panelTitle = computed(() => {
  if (currentTab.value === 'creators') return 'Listado de Creadores'
  if (currentTab.value === 'users') return 'Gestión de Usuarios'
  if (currentTab.value === 'requests') return 'Solicitudes de Autorización'
  return 'Catálogo Global de Convocatorias'
})

// Al cambiar de pestaña limpiamos la barra de filtros para mantener coherencia
watch(currentTab, () => {
  searchQuery.value = ''
  searchCreator.value = ''
  filterState.value = null
  filterTimeline.value = null
  loadAllData()
})

// Evaluar expiración del Unix Timestamp (en segundos) comparado al tiempo local real
function isCallExpired(closingTime) {
  if (!closingTime) return false
  const currentUnixTime = Math.floor(Date.now() / 1000)
  return Number(closingTime) < currentUnixTime
}

// FILTRADO DINÁMICO: PESTAÑA CREADORES
const filteredCreators = computed(() => {
  const query = searchQuery.value?.toLowerCase().trim() || ''
  
  const regFiltered = registeredCreators.value.filter(c => 
    c.name.toLowerCase().includes(query) || c.address.toLowerCase().includes(query)
  )
  const extFiltered = externalCreators.value.filter(addr => 
    addr.toLowerCase().includes(query)
  )

  return { registered: regFiltered, external: extFiltered }
})

// FILTRADO DINÁMICO: PESTAÑA USUARIOS
const searchedUsers = computed(() => {
  const query = searchQuery.value?.toLowerCase().trim() || ''
  const active = allUsers.value.filter(u => u.state !== 'pending' && u.state !== 'registered')
  
  return active.filter(u => 
    u.name.toLowerCase().includes(query) || u.address.toLowerCase().includes(query)
  )
})

// FILTRADO DINÁMICO: PESTAÑA SOLICITUDES
const filteredRequests = computed(() => {
  const query = searchQuery.value?.toLowerCase().trim() || ''

  const localFiltered = localRequests.value.filter(r => 
    r.name.toLowerCase().includes(query) || r.address.toLowerCase().includes(query)
  )
  const extFiltered = externalRequests.value.filter(addr => 
    addr.toLowerCase().includes(query)
  )

  return { local: localFiltered, external: extFiltered }
})

// UNIFICADOR REACTIVO Y MULTI-FILTRO: PESTAÑA LLAMADOS
const searchedGlobalCalls = computed(() => {
  const internals = internalGlobalCalls.value.map(c => ({ ...c, isInternal: true }))
  const externals = externalGlobalCalls.value.map(c => ({ ...c, isInternal: false }))
  let unified = [...internals, ...externals]

  // 1. Filtrar por barra de texto (Título, Dirección del contrato, CallID)
  const query = searchQuery.value?.toLowerCase().trim() || ''
  if (query) {
    unified = unified.filter(call => {
      const titleMatch = call.title?.toLowerCase().includes(query) || false
      const idMatch = call.callId?.toLowerCase().includes(query) || false
      const addressMatch = (call.contractAddress || call.address)?.toLowerCase().includes(query) || false
      return titleMatch || idMatch || addressMatch
    })
  }

  // 2. Filtrar específicamente por Dirección de Creador (Wallet)
  const creatorQuery = searchCreator.value?.toLowerCase().trim() || ''
  if (creatorQuery) {
    unified = unified.filter(call => 
      call.creator?.toLowerCase().includes(creatorQuery) || false
    )
  }

  // 3. Filtrar por Estado (Sincronizado, Blockchain Pura o estados de ciclo de vida local)
  if (filterState.value) {
    if (filterState.value === 'internal') {
      unified = unified.filter(c => c.isInternal)
    } else if (filterState.value === 'external') {
      unified = unified.filter(c => !c.isInternal)
    } else {
      unified = unified.filter(c => c.state === filterState.value)
    }
  }

  // 4. Filtrar por línea de tiempo (Vigentes vs Expirados)
  if (filterTimeline.value) {
    const isExpiredTarget = filterTimeline.value === 'expired'
    unified = unified.filter(c => isCallExpired(c.closingTime) === isExpiredTarget)
  }

  return unified
})

function isCurrentUser(targetAddress) {
  if (!walletStore.account || !targetAddress) return false
  return walletStore.account.toLowerCase() === targetAddress.toLowerCase()
}

function getRandomColor(index) {
  return avatarColors[index % avatarColors.length]
}

const avatarColors = [
  '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', 
  '#ec4899', '#8b5cf6', '#3b82f6', '#f43f5e'
]

function formatUnixTimestamp(timestamp) {
  if (!timestamp) return 'No definido'
  const date = new Date(Number(timestamp) * 1000)
  return date.toLocaleString(navigator.language, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function verifyDomainResolutions() {
  const calls = [...internalGlobalCalls.value, ...externalGlobalCalls.value]
  if (!window.ethereum || calls.length === 0) return
  
  try {
    await Promise.all(calls.map(async (call) => {
      if (!call.domain) return
      try {
        const resolvedAddress = await resolveDomain(call.domain)
        if (resolvedAddress && call.address && 
            resolvedAddress.toLowerCase() === call.address.toLowerCase()) {
          domainLinkedStatus.value[call.callId] = true
        } else {
          domainLinkedStatus.value[call.callId] = false
        }
      } catch (err) {
        console.warn(`No se pudo resolver el dominio ${call.domain}:`, err)
        domainLinkedStatus.value[call.callId] = false
      }
    }))
  } catch (error) {
    console.error("Error en la verificación masiva de dominios ENS:", error)
  }
}

async function loadAllData() {
  try {
    if (currentTab.value === 'calls') {
      await loadGlobalCallsData()
      return
    }

    const creatorsData = await getCreators()
    registeredCreators.value = creatorsData.registered_creators || []
    externalCreators.value = creatorsData.external_creators || []

    const usersData = await getUsers()
    allUsers.value = usersData.users || []

    const requestsData = await getAuthorizationRequests()
    localRequests.value = requestsData.local_requests || []
    externalRequests.value = requestsData.external_requests || []
  } catch (error) {
    console.error("Error al cargar los datos del panel:", error)
  }
}

async function loadGlobalCallsData() {
  try {
    loadingCalls.value = true
    const callsCatalog = await getGlobalCalls()
    if (callsCatalog) {
      internalGlobalCalls.value = callsCatalog.internal || []
      externalGlobalCalls.value = callsCatalog.external || []
      await verifyDomainResolutions()
    }
  } catch (error) {
    console.error("Error al recuperar llamados globales:", error)
    snackbar.value = {
      show: true,
      message: "No se pudo sincronizar el catálogo global con la Blockchain."
    }
  } finally {
    loadingCalls.value = false
  }
}

function showSnackbar(message, color = 'error') {
  snackbar.value = { show: true, message, color }
}

async function copyToClipboard(text, label) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    showSnackbar(`¡${label} copiado al portapapeles!`, 'success')
  } catch (err) {
    console.error('Error al copiar:', err)
    showSnackbar('No se pudo copiar el elemento.')
  }
}

async function handleAction(actionType, targetAddress) {
  try {
    if (isCurrentUser(targetAddress) && actionType === 'unauthorize') {
      throw new Error('Operación abortada: No puedes desautorizar tu propia cuenta de administrador.')
    }

    const targetUser = allUsers.value.find(u => u.address.toLowerCase() === targetAddress.toLowerCase())
    // if (targetUser && targetUser.state === 'archived') {
    //   throw new Error('Operación abortada: No se pueden realizar acciones sobre usuarios archivados.')
    // }

    isActionLoading.value = targetAddress

    if (!window.ethereum) throw new Error('MetaMask no está disponible en este navegador.')

    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    const chainId = parseInt(network.chainId.toString(), 10)

    const factoryAddressResult = await getContractAddress()
    const factoryAddress = typeof factoryAddressResult === 'string' ? factoryAddressResult : factoryAddressResult.address
    
    if (!factoryAddress) throw new Error('No se pudo mapear la dirección del contrato.')

    const checksumContractAddress = ethers.getAddress(factoryAddress.trim())
    const checksumTargetAddress = ethers.getAddress(targetAddress.trim())

    const adminNonce = await getAdminNonce()

    const domain = {
      name: "CFP API",
      version: "1",
      chainId: chainId,
      verifyingContract: checksumContractAddress
    }

    const types = {
      AdminActionRequest: [
        { name: "operation", type: "string" },
        { name: "contract", type: "address" },
        { name: "nonce", type: "uint256" },
        { name: "target", type: "address" }
      ]
    }

    const operationString = actionType === 'authorize' ? 'authorize' : 'unauthorize'

    const message = {
      operation: operationString,
      contract: checksumContractAddress,
      nonce: adminNonce,
      target: checksumTargetAddress
    }

    const signature = await signer.signTypedData(domain, types, message)
    const payload = { signature }

    if (actionType === 'authorize') {
      await authorizeUser(targetAddress, payload)
    } else {
      await unauthorizeUser(targetAddress, payload)
    }

    await loadAllData()

  } catch (error) {
    console.error(`Error al ejecutar la acción ${actionType} para ${targetAddress}:`, error)
    let alertMsg = error.message || 'Error al procesar la firma.'
    snackbar.value = { show: true, message: alertMsg }
  } finally {
    isActionLoading.value = null
  }
}

onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.bg-container {
  overflow: hidden;
  min-height: 100vh;
}

.blur-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  filter: blur(12px) brightness(0.9);
  transform: scale(1.05);
}

.z-index-1 {
  position: relative;
  z-index: 1;
}

.main-panel {
  background-color: rgba(248, 250, 252, 0.92) !important;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  height: 85vh; 
  display: flex;
  flex-direction: column;
}

.scrollable-containerpe {
  overflow-y: auto;
  flex-grow: 1;
  padding-right: 8px;
}

.bg-slate-light {
  background-color: #f1f5f9 !important;
  border: 1px solid #e2e8f0;
}

.search-box {
  flex-shrink: 0;
}

.toggle-wrapper {
  overflow-x: auto;
  width: 100%;
  flex-shrink: 0;
  padding-bottom: 4px;
}

.toggle-wrapper::-webkit-scrollbar {
  height: 0px;
  background: transparent;
}

.custom-toggle {
  border: 1px solid #e2e8f0;
  background-color: rgba(255, 255, 255, 0.7);
  border-radius: 99px !important;
  padding: 4px;
  display: flex !important;
  flex-wrap: nowrap !important;
  height: auto !important;
}

.custom-toggle :deep(.v-btn) {
  border-radius: 99px !important;
  text-transform: none;
  letter-spacing: 0;
  flex-shrink: 0 !important;
  min-width: max-content !important;
  white-space: nowrap !important;
  height: 40px !important;
}

.text-slate-dark {
  color: #0f172a !important;
}

.text-slate-medium {
  color: #334155 !important;
}

.text-mono {
  font-family: 'Courier New', Courier, monospace;
  font-weight: bold;
}

.creator-row {
  background-color: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  transition: all 0.2s ease-in-out;
}

.creator-row :deep(.v-expansion-panel-title) {
  background-color: #ffffff !important;
}

.creator-row :deep(.v-expansion-panel-title--active) {
  background-color: #f1f5f9 !important;
}

.external-row {
  border: 1px dashed #d97706 !important;
  background-color: rgba(255, 251, 235, 0.3) !important;
}

.archived-row {
  opacity: 0.65;
  filter: grayscale(80%);
}

.border-dashed {
  border: 2px dashed #94a3b8 !important;
}

.italic-text {
  font-style: italic;
}

.gap-1 {
  gap: 4px;
}

.gap-2 {
  gap: 8px;
}

.select-all {
  user-select: all;
}

.scrollable-containerpe::-webkit-scrollbar {
  width: 6px;
}
.scrollable-containerpe::-webkit-scrollbar-track {
  background: transparent;
}
.scrollable-containerpe::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
.scrollable-containerpe::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
.bg-slate-lighten-5 {
  background-color: #f8fafc !important;
}
.gap-3 {
  gap: 12px;
}
.technical-details {
  display: flex;
  flex-direction: column;
}
</style>