<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${BACKGROUND_IMAGE})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="10" lg="8" class="pa-4">
        
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <div class="d-flex align-center justify-space-between mb-4">
            <v-btn 
              variant="tonal" 
              icon
              color="indigo-darken-1" 
              class="rounded-lg d-flex align-center justify-center"
              @click="$router.push({ name: 'public' })"
            >
              <img :src="exit_svg" alt="Volver" width="24" height="24" style="opacity: 0.8;" />
            </v-btn>
            <h2 class="text-h5 font-weight-bold text-slate-dark text-center flex-grow-1">
              Propuestas Registradas
            </h2>
            <div style="width: 48px;"></div>
          </div>

          <div v-if="loadingCall" class="d-flex flex-column align-center justify-center my-8 flex-grow-1">
            <v-progress-circular indeterminate color="indigo-darken-1" size="50"></v-progress-circular>
            <span class="text-caption text-slate-medium mt-2">Cargando datos de la convocatoria...</span>
          </div>

          <template v-else>
            <v-card v-if="callData" variant="flat" class="bg-slate-light pa-4 rounded-xl mb-6 shadow-sm border-light">
              <div class="d-flex align-center mb-2">
                <h3 class="text-h6 font-weight-bold text-slate-dark">{{ callData.title }}</h3>
              </div>
              <p class="text-body-2 text-slate-medium italic-description mb-3">
                {{ callData.description }}
              </p>
              <v-divider class="mb-3"></v-divider>
              
              <div v-if="callData.domain" class="d-flex align-center gap-1 mb-2 text-caption text-slate-medium">
                <strong>Dominio:</strong>
                <span class="text-mono font-weight-bold text-indigo-darken-2">{{ callData.domain }}</span>
                <v-btn
                  icon="mdi-content-copy"
                  variant="text"
                  density="compact"
                  color="indigo-darken-1"
                  title="Copiar Dominio"
                  @click="copyToClipboard(callData.domain)"
                ></v-btn>
              </div>

              <div class="d-flex flex-column gap-2 mb-3 text-caption text-slate-medium">
                <!-- Creador -->
                <div v-if="creatorDomain" class="d-flex align-center gap-1">
                  <strong>Creador:</strong>
                  <span class="text-mono font-weight-bold text-teal-darken-3">{{ creatorDomain }}</span>
                  <v-btn
                    icon="mdi-content-copy"
                    variant="text"
                    density="compact"
                    color="teal-darken-3"
                    title="Copiar Creador"
                    @click="copyToClipboard(creatorDomain)"
                  ></v-btn>
                </div>

                <!-- Garantía Requerida-->
                <div class="d-flex align-center gap-1">
                  <strong>Garantía Requerida:</strong>
                  <span 
                    class="font-weight-bold" 
                    :class="guaranteeAmount > 0 ? 'text-amber-darken-4' : 'text-slate-dark'"
                  >
                    {{ guaranteeAmount > 0 ? `${formatTokenAmount(guaranteeAmount)} BEN` : 'Sin Garantía' }}
                  </span>
                </div>
              </div>

              <div class="d-flex justify-space-between align-center flex-wrap gap-2">
                <div class="text-caption text-slate-medium d-flex align-center gap-1">
                  <strong>Call ID:</strong> 
                  <span class="text-mono">{{ callId }}</span>
                  <v-btn
                    icon="mdi-content-copy"
                    variant="text"
                    density="compact"
                    color="slate-medium"
                    title="Copiar ID"
                    class="ms-1"
                    @click="copyToClipboard(callId)"
                  ></v-btn>
                </div>
                <v-chip :color="isCallClosed ? 'grey-darken-1' : 'error'" size="small" variant="flat" class="font-weight-bold rounded-lg">
                    {{ isCallClosed ? 'Cerrado' : 'Cierre' }}: {{ formatTimestamp(closingTimeISO) }}
                </v-chip>
              </div>
            </v-card>

            <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-3">
              <h4 class="text-subtitle-1 font-weight-bold text-slate-dark">
                Listado de Postulaciones ({{ proposals.length }})
              </h4>
              
              <div class="d-flex align-center gap-3 flex-wrap">
                <!-- Botón de autorización de garantía en la cabecera -->
                <template v-if="!isCallClosed && !hasRestrictedRole && guaranteeAmount > 0">
                  <v-btn
                    v-if="hasAllowance"
                    color="success"
                    variant="flat"
                    class="rounded-lg font-weight-bold text-white cursor-default"
                    readonly
                  >
                    <v-icon icon="mdi-check-circle" class="me-1" size="18"></v-icon>
                    Garantía Autorizada
                  </v-btn>

                  <v-btn
                    v-else
                    color="amber-darken-3"
                    variant="flat"
                    class="rounded-lg font-weight-bold text-white shadow-sm"
                    :loading="approvingGuarantee"
                    :disabled="!walletStore.account"
                    @click="handleApproveGuarantee"
                  >
                    Autorizar Retiro de Garantía ({{ formatTokenAmount(guaranteeAmount) }} BEN)
                  </v-btn>
                </template>

                <!-- Botón Añadir Propuesta -->
                <v-btn
                  v-if="!isCallClosed && !hasRestrictedRole"
                  color="indigo-darken-1"
                  variant="flat"
                  class="rounded-lg font-weight-bold text-white px-4 shadow-sm ms-3"
                  :disabled="guaranteeAmount > 0 && !hasAllowance"
                  @click="resetFormAndOpen"
                >
                  Añadir Propuesta
                </v-btn>
                <v-chip v-else-if="isCallClosed" color="amber-darken-2" variant="tonal" class="font-weight-bold rounded-lg">
                  Convocatoria Finalizada
                </v-chip>
                <v-chip v-else color="grey-darken-2" variant="tonal" class="font-weight-bold rounded-lg">
                  Modo Consulta
                </v-chip>
              </div>
            </div>

            <div v-if="loadingProposals" class="d-flex justify-center my-8 flex-grow-1 align-center">
              <v-progress-circular indeterminate color="indigo-darken-1"></v-progress-circular>
            </div>

            <v-alert 
              v-else-if="proposals.length === 0" 
              type="info" 
              variant="tonal" 
              class="rounded-xl d-flex align-center justify-center my-auto flex-grow-1"
              max-height="120"
            >
              Aún no se han registrado propuestas para esta convocatoria.
            </v-alert>

            <v-scrollbar v-else class="proposals-scroll-containerpe pe-1">
              <v-expansion-panels variant="accordion">
                <v-expansion-panel
                  v-for="proposal in proposals"
                  :key="proposal.proposalId"
                  class="proposal-row mb-3 rounded-xl overflow-hidden"
                  elevation="1"
                >
                  <v-expansion-panel-title class="font-weight-bold text-slate-dark py-4">
                    <div class="d-flex align-center justify-space-between w-100 pr-4">
                      <div class="d-flex align-center">
                        <span>{{ proposal.title }}</span>
                      </div>
                      
                      <v-chip
                        :color="matchState(proposal.state, 'delivered') ? 'success' : (matchState(proposal.state, 'pending') ? 'grey-darken-1' : 'warning')"
                        size="small"
                        variant="flat"
                        class="font-weight-bold rounded-lg"
                      >
                        {{ matchState(proposal.state, 'delivered') ? 'Archivos Recibidos' : (matchState(proposal.state, 'pending') ? 'Pendiente' : 'Registrada') }}
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>

                  <v-expansion-panel-text class="text-slate-medium pt-3 bg-slate-light-flat">
                    <div class="mb-3">
                      <strong>Descripción del Oferente:</strong>
                      <p class="text-body-2 mt-1 text-slate-dark">{{ proposal.description }}</p>
                    </div>
                    
                    <div class="mb-2 text-caption">
                      <strong>Raíz de Merkle (Proposal ID):</strong> 
                      <span class="text-mono text-indigo-darken-1 d-block text-truncate">{{ proposal.proposalId }}</span>
                    </div>

                    <div v-if="proposal.blockchainEvidence?.registrationTx" class="mb-2 text-caption">
                      <strong>Tx Registro:</strong> 
                      <span class="text-mono text-slate-dark d-block text-truncate">{{ proposal.blockchainEvidence.registrationTx }}</span>
                    </div>

                    <div class="d-flex justify-end gap-2 border-top pt-3">
                      
                      <template v-if="matchState(proposal.state, 'delivered')">
                        <v-btn
                          color="indigo-darken-1"
                          variant="flat"
                          class="rounded-lg font-weight-bold text-white shadow-sm"
                          :loading="downloadingZipId === proposal.proposalId"
                          @click="downloadPhysicalFiles(proposal.proposalId)"
                        >
                          Descargar ZIP
                        </v-btn>

                        <v-btn
                          color="success"
                          variant="outlined"
                          class="rounded-lg font-weight-bold"
                          :loading="downloadingReceiptId === proposal.proposalId"
                          @click="downloadFinalReceipt(proposal.proposalId)"
                        >
                          Recibo Post-Cierre
                        </v-btn>
                      </template>

                      <template v-else-if="hasRestrictedRole">
                        <span class="text-caption text-slate-medium my-auto italic">Vista de solo lectura para administradores/creadores</span>
                      </template>

                      <template v-else-if="isCallClosed && (matchState(proposal.state, 'created') || matchState(proposal.state, 'initial') || !proposal.state)">
                        <v-btn
                          color="warning"
                          variant="flat"
                          class="rounded-lg font-weight-bold text-white shadow-sm"
                          @click="openPostClosingModal(proposal)"
                        >
                          Entrega Post-Cierre
                        </v-btn>
                      </template>

                      <template v-else-if="matchState(proposal.state, 'created') || matchState(proposal.state, 'initial') || !proposal.state">

                        <!-- Mostrar botón de Registro SOLO si NO se ha confirmado en la blockchain -->
                        <v-btn
                          v-if="!chainStatusMap[proposal.proposalId]"
                          color="teal-darken-1"
                          variant="flat"
                          class="rounded-lg font-weight-bold text-white shadow-sm d-flex align-center"
                          :loading="submittingChainId === proposal.proposalId"
                          :disabled="!walletStore.account || (guaranteeAmount > 0 && !hasAllowance)"
                          @click="submitProposalBlockchainFromList(proposal)"
                        >
                          <img src="/metamask-icon.svg" alt="MetaMask" width="22" height="22" class="me-2" />
                          Registrar en Blockchain
                        </v-btn>

                        <!-- Mostrar Recibos SOLO si YA está en la blockchain -->
                        <template v-else>
                          <v-btn
                            color="indigo-darken-1"
                            variant="outlined"
                            class="rounded-lg font-weight-bold"
                            @click="openVerifyReceiptModal(proposal)"
                          >
                            Verificar con Recibo
                          </v-btn>

                          <v-btn
                            color="secondary"
                            variant="outlined"
                            class="rounded-lg font-weight-bold border-light text-slate-dark"
                            @click="downloadReceipt(proposal.proposalId)"
                          >
                            Descargar Recibo Inicial
                          </v-btn>
                        </template>

                      </template>

                      <template v-else-if="matchState(proposal.state, 'pending')">
                        <span class="text-caption text-slate-medium my-auto italic">Procesando entrega en blockchain...</span>
                      </template>

                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-scrollbar>
          </template>

        </v-card>
      </v-col>
    </v-row>

    <!-- Modal Nueva Propuesta -->
    <v-dialog v-model="dialogOpen" max-width="600px" persistent>
      <v-card class="rounded-xl pa-4 bg-white panel-modal shadow-lg">
        <v-card-title class="d-flex align-center justify-space-between text-slate-dark font-weight-bold text-h6">
          <div class="d-flex align-center">
            Nueva Propuesta
          </div>
          <v-btn variant="text" icon="mdi-close" color="slate-medium" @click="dialogOpen = false" :disabled="submitting"></v-btn>
        </v-card-title>
        <v-divider class="my-2"></v-divider>
        <v-card-text class="pa-2">


          <v-alert
            v-if="guaranteeAmount > 0 && (!walletStore.account || !userDomain)"
            type="warning"
            variant="tonal"
            class="rounded-xl mb-4 text-caption font-weight-bold"
          >
            Debes tener activa una cuenta de MetaMask y un dominio para registrar propuestas en este llamado.
          </v-alert>


          <v-form ref="formRef" v-model="isFormValid" lazy-validation>
            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Título de la propuesta *</div>
            <v-text-field
              v-model="formProposal.title"
              :rules="[v => !!v || 'El título es obligatorio', v => v.length <= 150 || 'El título no puede superar los 150 caracteres']"
              placeholder="Ej: Desarrollo de Infraestructura Descentralizada"
              variant="outlined"
              color="indigo-darken-1"
              class="rounded-lg mb-2"
              density="comfortable"
              :disabled="submitting"
            ></v-text-field>

            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Descripción Corta *</div>
            <v-textarea
              v-model="formProposal.description"
              :rules="[v => !!v || 'La descripción es obligatoria', v => v.length <= 1000 || 'La descripción no puede superar los 1000 caracteres']"
              placeholder="Detalla los alcances técnicos resumidos de tu postulación..."
              variant="outlined"
              color="indigo-darken-1"
              class="rounded-lg mb-4"
              rows="3"
              auto-grow
              density="comfortable"
              :disabled="submitting"
            ></v-textarea>

            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Archivos Comprobatorios *</div>
            <input type="file" ref="fileInputRef" multiple style="display: none" @change="onFilesSelected" accept=".pdf,.zip,.docx" />
            <div 
              class="drag-drop-zone d-flex flex-column align-center justify-center pa-6 rounded-xl text-center mb-2"
              @dragover.prevent
              @drop.prevent="onFilesDropped"
              :class="{ 'disabled-zone': submitting }"
              style="border: 2px dashed #cbd5e1; cursor: pointer; transition: background 0.2s;"
              @click="$refs.fileInputRef.click()"
            >
              <div class="text-body-2 font-weight-bold text-slate-dark mb-1">Arrastra tus archivos aquí o haz clic para buscar</div>
              <div class="text-caption text-slate-medium mb-3">Formatos permitidos: PDF, ZIP, DOCX (Máx. 10MB c/u)</div>
            </div>

            <div v-if="selectedFilesList.length > 0" class="mb-2">
              <div class="text-caption font-weight-bold text-slate-dark mb-1">Archivos seleccionados ({{ selectedFilesList.length }}):</div>
              <v-sheet max-height="120" class="overflow-y-auto pa-2 border rounded-lg bg-slate-light-flat">
                <div v-for="(fileItem, index) in selectedFilesList" :key="index" class="d-flex align-center justify-space-between text-caption border-bottom py-1">
                  <div class="d-flex align-center text-truncate max-w-70">
                    <span class="text-truncate">{{ fileItem.name }}</span>
                  </div>
                  <div class="d-flex align-center">
                    <span v-if="fileItem.hashing" class="text-orange font-weight-bold me-2 text-xxs">Calculando hash...</span>
                    <span v-else class="text-success font-weight-bold me-2 text-mono text-xxs">✓ {{ fileItem.hash.substring(0,10) }}...</span>
                    <v-btn variant="text" density="compact" color="error" @click.stop="removeFile(index)" :disabled="submitting"></v-btn>
                  </div>
                </div>
              </v-sheet>
            </div>

            <v-alert v-if="localProposalId" type="success" variant="tonal" class="rounded-xl mt-3 pa-2" icon="mdi-shield-check-outline">
              <div class="text-caption font-weight-bold">Proposal ID Calculado Localmente:</div>
              <div class="text-mono text-truncate text-xxs">{{ localProposalId }}</div>
            </v-alert>
            <div v-if="fileError" class="text-caption text-error mb-2 font-weight-bold">{{ fileError }}</div>

          </v-form>
        </v-card-text>


        <v-card-actions class="justify-end pa-2 border-top mt-4 gap-2">
          <v-btn variant="text" color="slate-medium" class="rounded-lg font-weight-bold px-4" @click="dialogOpen = false" :disabled="submitting">
            Cancelar
          </v-btn>

          <!-- Flujo A: Sin costo / Sin garantía (Mantiene comportamiento habitual) -->
          <template v-if="guaranteeAmount === 0">
            <v-btn 
              color="indigo-darken-1" 
              variant="flat" 
              class="rounded-lg font-weight-bold px-6 text-white shadow-sm" 
              @click="submitProposalStandard" 
              :loading="submitting" 
              :disabled="selectedFilesList.length === 0 || hashingInProgress"
            >
              Enviar Propuesta
            </v-btn>
          </template>

          <!-- Con Garantía (Dos Etapas: Registro API y Registro Blockchain) -->
          <template v-else>
            <!-- Paso 1: Registro en API -->
            <v-btn
              v-if="!apiRegistered"
              color="indigo-darken-1"
              variant="flat"
              class="rounded-lg font-weight-bold text-white shadow-sm"
              @click="submitProposalApiOnly"
              :loading="submitting"
              :disabled="isGuaranteeFormDisabled"
            >
              Registrar en API
            </v-btn>

            <!--Registro en Blockchain -->
            <v-btn
              v-if="apiRegistered && !chainRegistered"
              color="teal-darken-1"
              variant="flat"
              class="rounded-lg font-weight-bold text-white shadow-sm d-flex align-center"
              @click="submitProposalBlockchainOnly"
              :loading="submittingChain"
              :disabled="isGuaranteeFormDisabled"
            >
              <img src="/metamask-icon.svg" alt="MetaMask" width="22" height="22" class="me-2" />
              Registrar en Blockchain
            </v-btn>
          </template>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Modal Entrega Post-Cierre -->
    <v-dialog v-model="postClosingDialogOpen" max-width="600px" persistent>
      <v-card class="rounded-xl pa-4 bg-white panel-modal shadow-lg">
        <v-card-title class="d-flex align-center justify-space-between text-slate-dark font-weight-bold text-h6">
          <div class="d-flex align-center">
            Entrega Post-Cierre
          </div>
          <v-btn variant="text" icon="mdi-close" color="slate-medium" @click="postClosingDialogOpen = false" :disabled="submittingPostClosing"></v-btn>
        </v-card-title>
        <v-divider class="my-2"></v-divider>
        <v-card-text class="pa-2">
          <div class="text-caption text-slate-medium mb-4">La convocatoria ha cerrado. Para consolidar la entrega, debes adjuntar el archivo JSON de tu recibo junto con los archivos originales correspondientes.</div>
          <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">1. Seleccionar Recibo Original (.json) *</div>
          <v-file-input label="Buscar archivo de recibo" accept=".json" variant="outlined" density="comfortable" color="indigo-darken-1" prepend-icon="mdi-script-text-outline" :disabled="submittingPostClosing" @change="onReceiptFileChanged"></v-file-input>
          <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">2. Cargar Archivos Físicos Originales *</div>
          <v-file-input label="Buscar archivos de la propuesta" multiple accept=".pdf,.zip,.docx" variant="outlined" density="comfortable" color="indigo-darken-1" prepend-icon="mdi-paperclip" :disabled="submittingPostClosing" @change="onPostClosingFilesChanged"></v-file-input>
          <v-alert v-if="postClosingError" type="error" variant="tonal" class="rounded-xl mt-3 pa-2 text-caption font-weight-bold">{{ postClosingError }}</v-alert>
        </v-card-text>
        <v-card-actions class="justify-end pa-2 border-top mt-4">
          <v-btn variant="text" color="slate-medium" class="rounded-lg font-weight-bold px-4" @click="postClosingDialogOpen = false" :disabled="submittingPostClosing">Cancelar</v-btn>
          <v-btn color="warning" variant="flat" class="rounded-lg font-weight-bold px-6 text-white shadow-sm" @click="submitPostClosingData" :loading="submittingPostClosing" :disabled="!postClosingReceiptFile || postClosingFilesList.length === 0">Enviar Archivos</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Modal Verificar Recibo -->
    <v-dialog v-model="verifyReceiptDialogOpen" max-width="600px" persistent>
      <v-card class="rounded-xl pa-4 bg-white panel-modal shadow-lg">
        <v-card-title class="d-flex align-center justify-space-between text-slate-dark font-weight-bold text-h6">
          <div>Verificar Propuesta con Recibo</div>
          <v-btn variant="text" icon="mdi-close" color="slate-medium" @click="closeVerifyReceiptModal" :disabled="verifyingReceiptLoading"></v-btn>
        </v-card-title>
        <v-divider class="my-2"></v-divider>
        
        <v-card-text class="pa-2">
          <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-1">
            1. Cargar Archivo de Recibo (.json) <span class="text-error">*</span>
          </div>
          <p class="text-caption text-slate-medium mb-3">Sube el recibo criptográfico en formato JSON que descargaste al registrar la propuesta.</p>
          <v-file-input
            label="Selecciona tu recibo JSON"
            accept=".json"
            variant="outlined"
            density="comfortable"
            color="indigo-darken-1"
            prepend-icon="mdi-file-document-outline"
            :disabled="verifyingReceiptLoading"
            @change="onVerificationReceiptSelected"
            clearable
          ></v-file-input>

          <v-divider class="my-4"></v-divider>
          <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-1">
            2. Validar Archivo Original (Opcional)
          </div>
          <p class="text-caption text-slate-medium mb-3">Si deseas confirmar si un archivo físico que posees es íntegro y pertenece a este recibo, cárgalo aquí para validar su firma criptográfica localmente.</p>
          
          <input type="file" ref="verifyFileInputRef" style="display: none" @change="onVerifyFilesSelected" accept=".pdf,.zip,.docx" />
          <div 
            class="drag-drop-zone d-flex flex-column align-center justify-center pa-5 rounded-xl text-center mb-2"
            @dragover.prevent
            @drop.prevent="onVerifyFilesDropped"
            :class="{ 'disabled-zone': verifyingReceiptLoading }"
            style="border: 2px dashed #cbd5e1; cursor: pointer; transition: background 0.2s;"
            @click="$refs.verifyFileInputRef.click()"
          >
            <div class="text-body-2 font-weight-bold text-slate-dark mb-1">Arrastra el archivo de prueba aquí o haz clic</div>
            <div class="text-caption text-slate-medium">Formatos permitidos: PDF, ZIP, DOCX (Máx. 10MB)</div>
          </div>

          <div v-if="verifyFileList.length > 0" class="mt-2">
            <v-sheet class="pa-3 border rounded-lg bg-slate-light-flat">
              <div v-for="(fileItem, index) in verifyFileList" :key="index" class="d-flex align-center justify-space-between text-caption">
                <div class="text-truncate max-w-70">
                  <span class="font-weight-bold text-slate-dark">{{ fileItem.name }}</span>
                </div>
                <div class="d-flex align-center">
                  <span v-if="fileItem.hashing" class="text-orange font-weight-bold me-2 text-xxs">Calculando Hash...</span>
                  <span v-else class="text-success font-weight-bold text-mono text-xxs">✓ {{ fileItem.hash.substring(0, 16) }}...</span>
                  <v-btn icon="mdi-close" variant="text" size="small" color="error" class="ms-1" @click="removeVerifyFile(index)" :disabled="verifyingReceiptLoading"></v-btn>
                </div>
              </div>
            </v-sheet>
          </div>

          <v-alert v-if="verifyReceiptError" type="error" variant="tonal" class="rounded-xl mt-4 pa-2 text-caption font-weight-bold">
            {{ verifyReceiptError }}
          </v-alert>
        </v-card-text>

        <v-card-actions class="justify-end pa-2 border-top mt-4">
          <v-btn variant="text" color="slate-medium" class="rounded-lg font-weight-bold px-4" @click="closeVerifyReceiptModal" :disabled="verifyingReceiptLoading">Cancelar</v-btn>
          <v-btn 
            color="indigo-darken-1" 
            variant="flat" 
            class="rounded-lg font-weight-bold px-6 text-white shadow-sm" 
            @click="executeReceiptVerification" 
            :loading="verifyingReceiptLoading" 
            :disabled="!selectedVerifyReceiptJson || verifyReceiptHashingInProgress"
          >
            Verificar Recibo
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog Resultado -->
    <v-dialog v-model="verificationDialog.open" max-width="500px">
      <v-card class="rounded-xl pa-4 bg-white text-center">
        <v-card-title class="justify-center d-flex flex-column align-center">
          <v-icon :icon="verificationDialog.success ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline'" :color="verificationDialog.success ? 'success' : 'error'" size="64" class="mb-2"></v-icon>
          <span class="font-weight-bold text-slate-dark text-h6">Resultado del Proceso</span>
        </v-card-title>
        <v-card-text class="text-body-1 text-slate-medium pa-2">
          {{ verificationDialog.message }}

          <div v-if="verificationDialog.filesVerification && Object.keys(verificationDialog.filesVerification).length > 0" class="mt-4 text-left">
            <v-divider class="mb-3"></v-divider>
            <div class="text-caption font-weight-bold text-slate-dark mb-2">Comprobación de Archivos Físicos:</div>
            <v-sheet v-for="(info, filename) in verificationDialog.filesVerification" :key="filename" class="pa-2 border rounded-lg bg-slate-light-flat text-caption mb-2">
              <div class="d-flex align-start justify-space-between">
                <span class="text-truncate max-w-70 font-weight-bold text-mono">{{ filename.substring(0, 16) }}...</span>
                <v-chip :color="info.verified ? 'success' : 'error'" size="x-small" variant="flat" class="font-weight-bold rounded">
                  {{ info.verified ? 'Válido' : 'Inválido' }}
                </v-chip>
              </div>
              <p class="text-xxs text-slate-medium mt-1">{{ info.message || info.reason }}</p>
            </v-sheet>
          </div>
        </v-card-text>
        <v-card-actions class="justify-center mt-4">
          <v-btn color="indigo-darken-1" variant="flat" class="rounded-lg font-weight-bold px-6 text-white" @click="verificationDialog.open = false">Entendido</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { keccak256 } from 'js-sha3'
import { ethers } from 'ethers'
import { useWalletStore } from '../stores/wallet'
import { 
  getCallById, 
  getProposalsByCall, 
  getProposalReceipt, 
  getClosingTime, 
  registerProposal as apiRegisterProposal,
  verifyProposalReceipt,
  submitPostClosing,
  downloadProposalFiles,
  getProposalReceiptPostClosing,
  getCallContractAddress
} from '../services/api'
import { ASSETS } from '../config/constants'

import { reverseResolveAddress } from '../services/ens'
import { cfpService } from '../services/cfp'
import { tokenService } from '../services/token'

const route = useRoute()
const walletStore = useWalletStore()
const callId = ref(route.params.callId)
const exit_svg = ASSETS.exitIcon
const BACKGROUND_IMAGE = ASSETS.callsProposalsBg

const formRef = ref(null)
const fileInputRef = ref(null)
const verifyFileInputRef = ref(null)

const dialogOpen = ref(false)
const loadingCall = ref(true)
const loadingProposals = ref(true)
const submitting = ref(false)
const submittingChain = ref(false)
const isFormValid = ref(false)

const downloadingZipId = ref(null)
const downloadingReceiptId = ref(null)

const callData = ref(null)
const proposals = ref([])
const closingTimeISO = ref(null)

const creatorDomain = ref('')
const userDomain = ref('')
const guaranteeAmount = ref('0')
const cfpContractAddress = ref('')
const hasAllowance = ref(false)
const approvingGuarantee = ref(false)

const apiRegistered = ref(false)
const chainRegistered = ref(false)

const currentTime = ref(new Date())
let clockInterval = null

const formProposal = ref({ title: '', description: '' })
const selectedFilesList = ref([])
const fileError = ref(null)

const verificationDialog = ref({ open: false, success: false, message: '', filesVerification: null })

const verifyReceiptDialogOpen = ref(false)
const verifyingReceiptLoading = ref(false)
const selectedVerifyReceiptJson = ref(null)
const verifyFileList = ref([])
const verifyReceiptError = ref(null)

const verifyReceiptHashingInProgress = computed(() => verifyFileList.value.some(f => f.hashing))
const hashingInProgress = computed(() => selectedFilesList.value.some(f => f.hashing))

const postClosingDialogOpen = ref(false)
const submittingPostClosing = ref(false)
const postClosingReceiptFile = ref(null)
const postClosingFilesList = ref([])
const postClosingError = ref(null)
const selectedProposal = ref(null)

const submittingChainId = ref(null)

const userBalance = ref(BigInt(0))

const chainStatusMap = ref({})


const isCallClosed = computed(() => {
  if (!closingTimeISO.value) return false
  return currentTime.value > new Date(closingTimeISO.value)
})


const hasRestrictedRole = computed(() => {
  const userAddr = walletStore.account?.toLowerCase()
  const role = walletStore.userRole?.toLowerCase()

  //Si es Administrador
  if (role === 'admin') return true

  //Si es Creador, solo tiene modo consulta si es el creador de ESTE llamado
  if (role === 'creator' && callData.value?.creator) {
    return callData.value.creator.toLowerCase() === userAddr
  }

  return false
})

// Regla de deshabilitación para envíos con garantía
const isGuaranteeFormDisabled = computed(() => {
  if (guaranteeAmount.value > 0) {
    if (!walletStore.account || !userDomain.value || !hasAllowance.value) return true
  }
  return selectedFilesList.value.length === 0 || hashingInProgress.value
})

const matchState = (currentStatus, targetStatus) => {
  if (currentStatus === undefined || currentStatus === null) return false
  return currentStatus.toString().trim().toLowerCase() === targetStatus.trim().toLowerCase()
}

const checkProposalsOnChainStatus = async () => {
  if (!proposals.value || proposals.value.length === 0) return

  const checks = proposals.value.map(async (prop) => {
    if (!prop.proposalId) return
    try {
      const chainData = await cfpService.getProposalData(callId.value, prop.proposalId)
      // Actualiza el mapa indicando si la propuesta existe on-chain
      chainStatusMap.value[prop.proposalId] = chainData.exists
    } catch (err) {
      console.error(`Error verificando proposal ${prop.proposalId} on-chain:`, err)
      chainStatusMap.value[prop.proposalId] = false
    }
  })

  await Promise.all(checks)
}

// Calcular la raíz de Merkle localmente
const localProposalId = computed(() => {
  if (!formProposal.value.title || !formProposal.value.description || selectedFilesList.value.length === 0 || hashingInProgress.value) {
    return ''
  }
  try {
    const leavesHex = [
      callId.value.toLowerCase().replace('0x', ''),
      keccak256(formProposal.value.title),
      keccak256(formProposal.value.description),
      ...selectedFilesList.value.map(f => f.hash.toLowerCase().replace('0x', ''))
    ]
    
    leavesHex.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
    
    const hexToBytes = (hex) => {
      const arr = new Uint8Array(hex.length / 2)
      for (let i = 0; i < arr.length; i++) {
        arr[i] = parseInt(hex.substr(i * 2, 2), 16)
      }
      return arr
    }

    let currentLevel = leavesHex.map(h => hexToBytes(h))

    while (currentLevel.length > 1) {
      const nextLevel = []
      for (let i = 0; i < currentLevel.length; i += 2) {
        const leftBytes = currentLevel[i]
        const rightBytes = (i + 1 < currentLevel.length) ? currentLevel[i + 1] : leftBytes

        let isLeftSmaller = true
        for (let j = 0; j < Math.min(leftBytes.length, rightBytes.length); j++) {
          if (leftBytes[j] !== rightBytes[j]) {
            isLeftSmaller = leftBytes[j] < rightBytes[j]
            break
          }
        }

        const combinedBytes = new Uint8Array(leftBytes.length + rightBytes.length)
        if (isLeftSmaller) {
          combinedBytes.set(leftBytes, 0)
          combinedBytes.set(rightBytes, leftBytes.length)
        } else {
          combinedBytes.set(rightBytes, 0)
          combinedBytes.set(leftBytes, rightBytes.length)
        }

        const parentHashHex = keccak256(combinedBytes)
        nextLevel.push(hexToBytes(parentHashHex))
      }
      currentLevel = nextLevel
    }

    const rootHex = Array.from(currentLevel[0])
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')

    return '0x' + rootHex.toLowerCase()
  } catch (err) {
    console.error('Error calculando Merkle Root local:', err)
    return ''
  }
})

const submitProposalBlockchainFromList = async (proposal) => {
  if (!proposal || !proposal.proposalId) return
  
  try {
    submittingChainId.value = proposal.proposalId
    
    // Ejecuta el registro en el Smart Contract
    await cfpService.registerProposal(callId.value, proposal.proposalId)
    
    // Marca la propuesta como registrada On-Chain de inmediato
    chainStatusMap.value[proposal.proposalId] = true
    
    // Vuelve a cargar las propuestas
    await loadProposals()
    
  } catch (error) {
    console.error("Error al registrar propuesta desde la lista en blockchain:", error)
  } finally {
    submittingChainId.value = null
  }
}

const formatTokenAmount = (amount) => {
  if (!amount || amount === 0) return '0'
  try {
    return ethers.formatEther(amount.toString())
  } catch (e) {
    return amount
  }
}

// Watcher para reevaluar la propuesta actual en API / Blockchain al cambiar el ID local
watch(localProposalId, async (newVal) => {
  if (newVal) {
    await checkProposalProgress(newVal)
  } else {
    apiRegistered.value = false
    chainRegistered.value = false
  }
})

/**
 * Resuelve el dominio ENS del Creador y del Usuario Conectado
 */
const fetchDomains = async () => {
  if (callData.value?.creator) {
    try {
      creatorDomain.value = await reverseResolveAddress(callData.value.creator)
    } catch (e) {
      console.error("Error al resolver dominio del creador:", e)
    }
  }

  if (walletStore.account) {
    try {
      userDomain.value = await reverseResolveAddress(walletStore.account)
    } catch (e) {
      console.error("Error al resolver dominio del usuario:", e)
    }
  }
}

/**
 * Carga el Contrato del Llamado y verifica si el usuario ya otorgó Allowance
 */
const checkAllowanceAndGuarantee = async () => {
  if (!callId.value) return
  try {
    const resp = await getCallContractAddress(callId.value)
    cfpContractAddress.value = typeof resp === 'string' ? resp : resp.address

    if (walletStore.account && cfpContractAddress.value && guaranteeAmount.value > 0) {
      const currentAllowance = await tokenService.allowance(walletStore.account, cfpContractAddress.value)
      
      const requiredWei = BigInt(guaranteeAmount.value.toString())
      hasAllowance.value = BigInt(currentAllowance) >= requiredWei
    }
  } catch (err) {
    console.error("Error comprobando contrato / allowance:", err)
  }
}

/**
 * Ejecuta el Approve ERC-20 del token BENCOIN
 */
const handleApproveGuarantee = async () => {
  if (!cfpContractAddress.value || guaranteeAmount.value <= 0 || !walletStore.account) return

  try {
    approvingGuarantee.value = true
    
    // Tomar el valor directo en Wei (BigInt)
    const requiredWei = BigInt(guaranteeAmount.value.toString())

    // Consultar el balance del usuario (debe retornar Wei en BigInt o String Hex)
    const userBalanceHex = await tokenService.balanceOf(walletStore.account)
    const userBalance = BigInt(userBalanceHex)

    // Validar si los fondos en Wei son suficientes
    if (userBalance < requiredWei) {
      verificationDialog.value = {
        open: true,
        success: false,
        message: `Fondos insuficientes. Requieres ${formatTokenAmount(requiredWei)} BEN para la garantía pero tu saldo actual es de ${formatTokenAmount(userBalance)} BEN.`,
        filesVerification: null
      }
      return
    }

    // Se envía a la blockchain la cantidad exacta en Wei
    await tokenService.approve(cfpContractAddress.value, requiredWei.toString())
    hasAllowance.value = true

  } catch (err) {
    console.error("Error aprobando la garantía:", err)
    verificationDialog.value = {
      open: true,
      success: false,
      message: "Ocurrió un error al autorizar el retiro de garantía en la red.",
      filesVerification: null
    }
  } finally {
    approvingGuarantee.value = false
  }
}

/**
 * Verifica en qué etapa (API / Blockchain) se encuentra la propuesta local
 */
const checkProposalProgress = async (proposalHash) => {
  if (!proposalHash) return

  // 1. Verificar si está en la lista de propuestas del backend
  const inApi = proposals.value.some(p => p.proposalId?.toLowerCase() === proposalHash.toLowerCase())
  apiRegistered.value = inApi

  // 2. Verificar directamente On-Chain con cfpService.getProposalData
  try {
    const chainData = await cfpService.getProposalData(callId.value, proposalHash)
    chainRegistered.value = chainData.exists
  } catch (err) {
    console.error("Error verificando registro on-chain:", err)
    chainRegistered.value = false
  }
}


// Sin costo / Garantía = 0 (Usa endpoint backend original con blockchain=true)
const submitProposalStandard = async () => {
  if (!formRef.value || hasRestrictedRole.value) return
  const { valid } = await formRef.value.validate()
  if (!valid) return
  if (selectedFilesList.value.length === 0) {
    fileError.value = 'Debes incluir al menos un archivo comprobatorio.'
    return
  }

  try {
    submitting.value = true
    const payload = {
      callId: callId.value,
      title: formProposal.value.title,
      description: formProposal.value.description,
      files: selectedFilesList.value.map(file => file.hash),
      blockchain: true // Mantiene el comportamiento por defecto
    }
    await apiRegisterProposal(payload)
    dialogOpen.value = false
    await loadProposals()
  } catch (error) {
    fileError.value = `Error en el servidor: ${error.response?.data?.message || 'Error interno.'}`
  } finally {
    submitting.value = false
  }
}

// Registro Exclusivo en API (blockchain = false)
const submitProposalApiOnly = async () => {
  if (!formRef.value || hasRestrictedRole.value) return
  const { valid } = await formRef.value.validate()
  if (!valid) return

  try {
    submitting.value = true
    const payload = {
      callId: callId.value,
      title: formProposal.value.title,
      description: formProposal.value.description,
      files: selectedFilesList.value.map(file => file.hash),
      blockchain: false // Flag explícito en false para la API
    }
    await apiRegisterProposal(payload)
    apiRegistered.value = true
    await loadProposals()
  } catch (error) {
    fileError.value = `Error registrando en API: ${error.response?.data?.message || 'Error de conexión.'}`
  } finally {
    submitting.value = false
  }
}

// Registro Exclusivo On-Chain mediante Contrato Inteligente
const submitProposalBlockchainOnly = async () => {
  if (!localProposalId.value) return
  try {
    submittingChain.value = true
    // Ejecuta registerProposal(bytes32) en el Smart Contract (El contrato descuenta la garantía)
    await cfpService.registerProposal(callId.value, localProposalId.value)
    chainRegistered.value = true
    dialogOpen.value = false
    await loadProposals()
  } catch (error) {
    console.error("Error al registrar propuesta en blockchain:", error)
    fileError.value = "Error en la transacción MetaMask o fallo en la blockchain."
  } finally {
    submittingChain.value = false
  }
}

// Métodos auxiliares originales
const downloadPhysicalFiles = async (proposalId) => {
  try {
    downloadingZipId.value = proposalId
    await downloadProposalFiles(proposalId)
  } catch (error) {
    console.error(error)
  } finally {
    downloadingZipId.value = null
  }
}

const downloadFinalReceipt = async (proposalId) => {
  try {
    downloadingReceiptId.value = proposalId
    const fullReceiptData = await getProposalReceiptPostClosing(proposalId)
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(fullReceiptData, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", dataStr)
    downloadAnchor.setAttribute("download", `recibo_definitivo_${proposalId.substring(0, 10)}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  } catch (error) {
    console.error(error)
  } finally {
    downloadingReceiptId.value = null
  }
}

const formatTimestamp = (value) => {
  if (!value) return 'Sin fecha'
  const date = typeof value === 'string' ? new Date(value) : new Date(value * 1000)
  if (isNaN(date.getTime())) return 'Fecha inválida'
  return date.toLocaleString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const loadCallDetails = async () => {
  try {
    loadingCall.value = true
    const [callResponse, closingTimeResponse] = await Promise.all([
      getCallById(callId.value),
      getClosingTime(callId.value)
    ])
    callData.value = callResponse
    closingTimeISO.value = closingTimeResponse.closingTime 
    
    // Obtener la garantía requerida
    const rawGuarantee = callResponse.guarantee ?? callResponse.guaranteeAmount ?? '0'
    guaranteeAmount.value = rawGuarantee.toString()

    await fetchDomains()
    await checkAllowanceAndGuarantee()
  } catch (error) {
    console.error("Error al cargar detalles de la convocatoria:", error)
  } finally {
    loadingCall.value = false
  }
}

const loadProposals = async () => {
  try {
    loadingProposals.value = true
    const list = await getProposalsByCall(callId.value)
    proposals.value = list
    
    // Verificar en la Blockchain la existencia de cada propuesta
    await checkProposalsOnChainStatus()
  } catch (error) {
    console.error("Error al cargar las propuestas:", error)
  } finally {
    loadingProposals.value = false
  }
}

const calculateFileHash = async (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const arrayBuffer = e.target.result
      const hashResult = keccak256(arrayBuffer)
      resolve(`0x${hashResult}`.toLowerCase())
    }
    reader.readAsArrayBuffer(file)
  })
}

const processIncomingFiles = async (files) => {
  fileError.value = null
  const maxSize = 10 * 1024 * 1024
  for (let file of files) {
    if (file.size > maxSize) {
      fileError.value = `El archivo "${file.name}" supera el límite de 10MB.`
      continue
    }
    const fileIdx = selectedFilesList.value.length
    selectedFilesList.value.push({ name: file.name, size: file.size, hash: '', hashing: true })
    const hashResult = await calculateFileHash(file)
    selectedFilesList.value[fileIdx].hash = hashResult
    selectedFilesList.value[fileIdx].hashing = false
  }
}

const onFilesSelected = (e) => { if (e.target.files) processIncomingFiles(e.target.files) }
const onFilesDropped = (e) => { if (!submitting.value && e.dataTransfer?.files) processIncomingFiles(e.dataTransfer.files) }
const removeFile = (index) => { selectedFilesList.value.splice(index, 1) }

const openVerifyReceiptModal = (proposal) => {
  selectedProposal.value = proposal
  selectedVerifyReceiptJson.value = null
  verifyFileList.value = []
  verifyReceiptError.value = null
  verifyReceiptDialogOpen.value = true
}

const closeVerifyReceiptModal = () => {
  if (verifyingReceiptLoading.value) return
  verifyReceiptDialogOpen.value = false
}

const onVerificationReceiptSelected = (e) => {
  const files = e.target.files
  if (!files || files.length === 0) {
    selectedVerifyReceiptJson.value = null
    return
  }
  const file = files[0]
  const reader = new FileReader()
  reader.onload = (event) => {
    try {
      selectedVerifyReceiptJson.value = JSON.parse(event.target.result)
      verifyReceiptError.value = null
    } catch (err) {
      selectedVerifyReceiptJson.value = null
      verifyReceiptError.value = "El archivo cargado no es un JSON válido."
    }
  }
  reader.readAsText(file)
}

const processVerifyFiles = async (files) => {
  verifyReceiptError.value = null
  const maxSize = 10 * 1024 * 1024
  for (let file of files) {
    if (file.size > maxSize) {
      verifyReceiptError.value = `El archivo "${file.name}" supera el límite de 10MB.`
      continue
    }
    const fileIdx = verifyFileList.value.length
    verifyFileList.value.push({ name: file.name, size: file.size, hash: '', hashing: true })
    const hashResult = await calculateFileHash(file)
    verifyFileList.value[fileIdx].hash = hashResult
    verifyFileList.value[fileIdx].hashing = false
  }
}

const onVerifyFilesSelected = (e) => { if (e.target.files) processVerifyFiles(e.target.files) }
const onVerifyFilesDropped = (e) => { if (!verifyingReceiptLoading.value && e.dataTransfer?.files) processVerifyFiles(e.dataTransfer.files) }
const removeVerifyFile = (index) => { verifyFileList.value.splice(index, 1) }

const executeReceiptVerification = async () => {
  if (!selectedVerifyReceiptJson.value) {
    verifyReceiptError.value = "Es obligatorio cargar un archivo de recibo (.json)"
    return
  }

  try {
    verifyingReceiptLoading.value = true
    verifyReceiptError.value = null

    const payload = {
      ...selectedVerifyReceiptJson.value,
      fileHashesToVerify: verifyFileList.value.length > 0 
        ? verifyFileList.value.map(f => f.hash) 
        : null
    }

    const result = await verifyProposalReceipt(payload)

    verificationDialog.value = {
      open: true,
      success: result.valid,
      message: result.message || result.reason || 'Proceso finalizado.',
      filesVerification: result.filesVerification || null
    }

    verifyReceiptDialogOpen.value = false

  } catch (err) {
    verifyReceiptError.value = err.response?.data?.message || "Fallo en el servidor al intentar verificar el recibo."
  } finally {
    verifyingReceiptLoading.value = false
  }
}

const resetFormAndOpen = () => {
  if (hasRestrictedRole.value) return
  formProposal.value.title = ''
  formProposal.value.description = ''
  selectedFilesList.value = []
  fileError.value = null
  apiRegistered.value = false
  chainRegistered.value = false
  if (formRef.value) formRef.value.resetValidation()
  dialogOpen.value = true
}

const downloadReceipt = async (proposalId) => {
  try {
    const receiptData = await getProposalReceipt(proposalId)
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(receiptData, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", dataStr)
    downloadAnchor.setAttribute("download", `recibo_inicial_${proposalId.substring(0, 10)}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  } catch (error) {
  }
}

const openPostClosingModal = (proposal) => {
  if (hasRestrictedRole.value) return
  selectedProposal.value = proposal
  postClosingReceiptFile.value = null
  postClosingFilesList.value = []
  postClosingError.value = null
  postClosingDialogOpen.value = true
}

const onReceiptFileChanged = (e) => {
  const files = e.target.files || e.dataTransfer?.files
  if (files && files.length > 0) postClosingReceiptFile.value = files[0]
}
const onPostClosingFilesChanged = (e) => {
  const files = e.target.files || e.dataTransfer?.files
  if (files) postClosingFilesList.value = Array.from(files)
}

const submitPostClosingData = async () => {
  if (!postClosingReceiptFile.value || postClosingFilesList.value.length === 0 || hasRestrictedRole.value) return
  const reader = new FileReader()
  submittingPostClosing.value = true
  reader.onload = async (e) => {
    try {
      const formData = new FormData()
      formData.append('receipt_data', e.target.result)
      postClosingFilesList.value.forEach(file => formData.append('uploaded_files', file))
      await submitPostClosing(formData)
      postClosingDialogOpen.value = false
      verificationDialog.value = { open: true, success: true, message: 'Entrega post-cierre procesada.' }
      await loadProposals()
    } catch (error) {
      postClosingError.value = `Fallo: ${error.response?.data?.message || 'Error crítico.'}`
    } finally {
      submittingPostClosing.value = false
    }
  }
  reader.readAsText(postClosingReceiptFile.value)
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
  } catch (err) {
    console.error('Error al intentar copiar al portapapeles:', err)
  }
}

onMounted(() => {
  if (callId.value) { loadCallDetails(); loadProposals(); }
  clockInterval = setInterval(() => { currentTime.value = new Date() }, 1000)
})
onBeforeUnmount(() => { if (clockInterval) clearInterval(clockInterval) })
</script>

<style scoped>
.bg-container { min-height: 100vh; overflow: hidden; }
.blur-background { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-size: cover; background-position: center; filter: blur(10px) brightness(0.85); transform: scale(1.05); z-index: 0; }
.z-index-1 { z-index: 1; }
.main-panel { background-color: rgba(248, 250, 252, 0.92) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.6); height: 85vh; display: flex; flex-direction: column; }
.bg-slate-light { background-color: #ffffff !important; border: 1px solid #e2e8f0; }
.bg-slate-light-flat { background-color: #f8fafc !important; }
.border-light { border: 1px solid #e2e8f0 !important; }
.italic-description { font-style: italic; word-wrap: break-word; white-space: normal; }
.text-slate-dark { color: #0f172a !important; }
.text-slate-medium { color: #475569 !important; }
.text-mono { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
.proposals-scroll-containerpe { overflow-y: auto; flex-grow: 1; }
.proposal-row { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; transition: all 0.2s ease-in-out; }
.proposal-row :deep(.v-expansion-panel-title--active) { background-color: #f1f5f9 !important; }
.text-xxs { font-size: 0.7rem; }
.max-w-70 { max-width: 70%; }
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
.gap-1 { gap: 4px; }
.cursor-default { cursor: default !important; }
</style>