<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${BACKGROUND_IMAGE})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="10" lg="8" class="pa-4">
        
        <v-card class="main-panel pa-4 rounded-xl mx-auto" elevation="4">
          
          <div class="d-flex align-center justify-space-between mb-4">
            <v-btn 
              variant="tonal" 
              icon
              color="indigo-darken-1" 
              class="rounded-lg d-flex align-center justify-center"
              @click="$router.go(-1)"
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
            <v-card v-if="callData" variant="flat" class="bg-slate-light pa-3 rounded-xl mb-3 shadow-sm border-light flex-shrink-0">
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
                <div 
                  v-if="callData && isCallClosed && walletStore.account?.toLowerCase() === callData.creator?.toLowerCase()" 
                  class="mt-3 text-right"
                >
                  <v-btn
                    color="error"
                    variant="flat"
                    class="rounded-lg font-weight-bold text-white shadow-sm"
                    :disabled="!isFileSubmissionOpen"
                    :loading="closingFileSubmission"
                    @click="handleCloseFileSubmission"
                  >
                    <v-icon icon="mdi-lock-outline" class="me-1" size="18"></v-icon>
                    {{ isFileSubmissionOpen ? 'Cerrar Entrega de Archivos' : 'Entrega de Archivos Cerrada' }}
                  </v-btn>
                </div>
              </div>
            </v-card>
            <v-alert
              v-if="Number(guaranteeAmount) > 0"
              type="warning"
              variant="tonal"
              class="rounded-xl mb-3 flex-shrink-0 border-light w-100"
              icon="mdi-shield-alert-outline"
            >
              <div class="d-flex align-center justify-space-between w-100 gap-2">
                <span class="text-body-2 font-weight-bold text-slate-dark text-truncate">
                  Este es un llamado que exige pago de garantía.
                </span>
                <v-btn
                  color="amber-darken-4"
                  variant="text"
                  density="compact"
                  class="font-weight-bold text-none pa-0 flex-shrink-0"
                  @click="guaranteeDetailsDialogOpen = true"
                >
                  Más detalles
                </v-btn>
              </div>
            </v-alert>

            <!-- Diálogo / Modal "Más detalles de la Garantía" -->
            <v-dialog v-model="guaranteeDetailsDialogOpen" max-width="500px">
              <v-card class="rounded-xl pa-5 bg-white shadow-lg">
                <v-card-title class="d-flex align-center justify-space-between text-slate-dark font-weight-bold text-h6 pa-0 mb-3">
                  <div class="d-flex align-center gap-2">
                    <v-icon color="amber-darken-3" icon="mdi-information-outline"></v-icon>
                    Requisitos de Garantía
                  </div>
                  <v-btn 
                    variant="text" 
                    icon="mdi-close" 
                    color="slate-medium" 
                    density="compact"
                    @click="guaranteeDetailsDialogOpen = false"
                  ></v-btn>
                </v-card-title>
                
                <v-divider class="mb-4"></v-divider>

                <v-card-text class="pa-0 text-slate-dark">
                  <p class="text-body-2 mb-3">
                    Este es un llamado de pago de garantía. Para poder cargar propuestas, deberás tener:
                  </p>

                  <v-list density="compact" class="bg-transparent pa-0 mb-3">
                    <v-list-item class="px-0 py-1">
                      <template v-slot:prepend>
                        <v-icon color="indigo-darken-1" icon="mdi-check-circle" class="me-2" size="20"></v-icon>
                      </template>
                      <v-list-item-title class="text-body-2 font-weight-medium text-wrap">
                        Tu cuenta de MetaMask abierta.
                      </v-list-item-title>
                    </v-list-item>

                    <v-list-item class="px-0 py-1">
                      <template v-slot:prepend>
                        <v-icon color="indigo-darken-1" icon="mdi-check-circle" class="me-2" size="20"></v-icon>
                      </template>
                      <v-list-item-title class="text-body-2 font-weight-medium text-wrap">
                        Un dominio ENS vinculado a tu cuenta.
                      </v-list-item-title>
                    </v-list-item>

                    <v-list-item class="px-0 py-1">
                      <template v-slot:prepend>
                        <v-icon color="indigo-darken-1" icon="mdi-check-circle" class="me-2" size="20"></v-icon>
                      </template>
                      <v-list-item-title class="text-body-2 font-weight-medium text-wrap">
                        Luego autorizar al contrato para la extracción de tus tokens por un valor igual a la garantía.
                      </v-list-item-title>
                    </v-list-item>
                  </v-list>

                  <v-alert type="info" variant="tonal" class="rounded-lg text-caption pa-3 mt-2">
                    <strong>Nota importante:</strong> En caso de que quieras registrar más propuestas, deberás autorizar al contrato a extraer de nuevo.
                  </v-alert>
                </v-card-text>

                <v-card-actions class="justify-end pa-0 mt-5">
                  <v-btn 
                    color="indigo-darken-1" 
                    variant="flat" 
                    class="rounded-lg font-weight-bold px-5 text-white"
                    @click="guaranteeDetailsDialogOpen = false"
                  >
                    Entendido
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
            <v-card
              v-if="showEvaluatingNotice"
              color="amber-lighten-5"
              variant="flat"
              class="pa-6 rounded-xl border-amber text-center mb-4 border-light shadow-sm"
            >
              <v-icon icon="mdi-clock-check-outline" color="amber-darken-3" size="48" class="mb-2"></v-icon>
              <h3 class="text-h6 font-weight-bold text-slate-dark mb-1">
                Convocatoria Finalizada
              </h3>
              <p class="text-body-2 text-slate-medium mb-0">
                El período de recepción de propuestas ha terminado. El creador del llamado se encuentra evaluando las postulaciones recibidas.
                Si cargaste tus archivos en tiempo y forma, el creador te proporcionara un metodo para recuperar la garantía.
              </p>
              <!-- Botón Retirar Garantía (Se habilita solo si canWithdrawGuarantee es true) -->
              <v-btn
                v-if="canWithdrawGuarantee"
                color="teal-darken-2"
                variant="flat"
                class="rounded-lg font-weight-bold text-white shadow-sm m-3"
                :loading="withdrawingGuarantee"
                @click="handleWithdrawGuarantee"
              >
                <v-icon icon="mdi-cash-refund" class="me-1" size="20"></v-icon>
                Retirar Garantía ({{ formatTokenAmount(guaranteeAmount) }} BEN)
              </v-btn>
            </v-card>
            <div v-if="!showEvaluatingNotice">
              <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-3 flex-shrink-0">
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
              <div v-else class="proposals-scroll-container pe-1">
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
                          :color="matchState(proposal.state, 'delivered') ? 'success' : (matchState(proposal.state, 'pending') ? 'grey-darken-1' : (guaranteeAmount == 0 || chainStatusMap[proposal.proposalId] ? 'success' : 'warning'))"
                          size="small"
                          variant="flat"
                          class="font-weight-bold rounded-lg"
                        >
                          {{ 
                            matchState(proposal.state, 'delivered') 
                              ? 'Archivos Recibidos' 
                              : (matchState(proposal.state, 'pending') 
                                  ? 'Pendiente' 
                                  : (guaranteeAmount == 0 
                                      ? 'Registrada por API' 
                                      : (chainStatusMap[proposal.proposalId] ? 'Registrada en Blockchain' : 'Registrada en API'))) 
                          }}
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

                        <!-- Control de Autorización de Garantía (Visible solo tras cerrar la entrega de archivos y para el Administrador/Creador) -->
                        <template v-if="!isFileSubmissionOpen && Number(guaranteeAmount) > 0 && walletStore.account?.toLowerCase() === callData?.creator?.toLowerCase()">
                          <!-- Opción 1: Si ya está autorizado -->
                          <v-btn
                            v-if="authorizedWithdrawMap[proposal.proposalId]"
                            color="teal-darken-2"
                            variant="tonal"
                            class="rounded-lg font-weight-bold cursor-default"
                            readonly
                          >
                            <v-icon icon="mdi-shield-check" class="me-1" size="18"></v-icon>
                            Autorizado a retirar fondos
                          </v-btn>

                          <!-- Opción 2: Si aún no está autorizado -->
                          <v-btn
                            v-else
                            color="amber-darken-3"
                            variant="flat"
                            class="rounded-lg font-weight-bold text-white shadow-sm"
                            :loading="authorizingMap[proposal.proposalId]"
                            :disabled="!proposalOwnersMap[proposal.proposalId]"
                            @click="handleAuthorizeGuarantee(proposal.proposalId)"
                          >
                            <v-icon icon="mdi-lock-open-outline" class="me-1" size="18"></v-icon>
                            Autorizar Retiro de Garantía
                          </v-btn>
                        </template>
                        
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
                          <span class="text-caption text-slate-medium my-auto italic">Vista de solo lectura para creadores</span>
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

                      <template v-else-if="matchState(proposal.state, 'created') || !proposal.state">

                          <template v-if="Number(guaranteeAmount) === 0 || isProposalOwner(proposal)">
                            
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
              </div>
            </div>
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
            <v-btn 
              variant="text" 
              color="slate-medium" 
              class="rounded-lg font-weight-bold px-4" 
              @click="dialogOpen = false" 
              :disabled="submitting"
            >
              Cancelar
            </v-btn>

            <!-- Botón Único Unificado -->
            <v-btn
              color="indigo-darken-1"
              variant="flat"
              class="rounded-lg font-weight-bold px-6 text-white shadow-sm d-flex align-center"
              @click="submitProposalSystem"
              :loading="submitting"
              :disabled="selectedFilesList.length === 0 || hashingInProgress || (Number(guaranteeAmount) > 0 && isGuaranteeFormDisabled)"
            >
              <img 
                v-if="Number(guaranteeAmount) > 0" 
                src="/metamask-icon.svg" 
                alt="MetaMask" 
                width="20" 
                height="20" 
                class="me-2" 
              />
              Registrar en el Sistema
            </v-btn>
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

const guaranteeDetailsDialogOpen = ref(false)

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

const authorizedWithdrawMap = ref({})

const authorizingMap = ref({})

const proposalOwnersMap = ref({})

const submittingChainId = ref(null)

const userBalance = ref(BigInt(0))

const chainStatusMap = ref({})

const isFileSubmissionOpen = ref(true)


const canWithdrawGuarantee = ref(false)
const withdrawingGuarantee = ref(false)

const closingFileSubmission = ref(false)

const isCallClosed = computed(() => {
  if (!closingTimeISO.value) return false
  return currentTime.value > new Date(closingTimeISO.value)
})

const checkIsFileSubmissionOpen = async () => {
  if (!callId.value) return
  try {
    const isOpen = await cfpService.isFileSubmissionOpen(callId.value)
    isFileSubmissionOpen.value = Boolean(isOpen)
  } catch (err) {
    console.error("Error al consultar el estado de isFileSubmissionOpen:", err)
    // Por defecto, si falla la lectura asumimos que sigue abierto
    isFileSubmissionOpen.value = true
  }
}

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

const showEvaluatingNotice = computed(() => {
  if (isFileSubmissionOpen.value) return false

  const userAddr = walletStore.account?.toLowerCase()
  const creatorAddr = callData.value?.creator?.toLowerCase()

  // Si no hay cuenta conectada o si la cuenta no pertenece al creador, se muestra el aviso
  if (!userAddr || userAddr !== creatorAddr) {
    return true
  }

  // Si es el creador, la alerta se oculta
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

/**
 * Consulta en la Blockchain el owner/proposer real de cada propuesta
 */
const checkProposalsOnChainStatus = async () => {
  if (!proposals.value || proposals.value.length === 0) return

  const checks = proposals.value.map(async (prop) => {
    if (!prop.proposalId) return
    try {
      const chainData = await cfpService.getProposalData(callId.value, prop.proposalId)
      chainStatusMap.value[prop.proposalId] = chainData.exists

      const ownerOnChain = chainData.sender
      if (ownerOnChain) {
        proposalOwnersMap.value[prop.proposalId] = ownerOnChain.toString().toLowerCase()
      }
    } catch (err) {
      console.error(`Error verificando proposal ${prop.proposalId} on-chain:`, err)
      chainStatusMap.value[prop.proposalId] = false
    }
  })

  await Promise.all(checks)
  // Revisa el estado de autorizaciones de retiro
  await checkAuthorizedWithdrawals()
}
/*
* Consulta en el Smart Contract si el usuario actual tiene saldo de garantía disponible para retirar
 */
const checkWithdrawableGuarantee = async () => {
  if (!walletStore.account || !callId.value) {
    canWithdrawGuarantee.value = false
    return
  }
  try {
    const isAuthorized = await cfpService.isAuthorizedToWithdrawGuarantee(callId.value, walletStore.account)
    canWithdrawGuarantee.value = Boolean(isAuthorized)
  } catch (err) {
    console.error("Error al consultar autorización de retiro de garantía:", err)
    canWithdrawGuarantee.value = false
  }
}

/**
 * Consulta en el Smart Contract si el usuario dueño de la propuesta está autorizado a retirar garantía
 */
const checkAuthorizedWithdrawals = async () => {
  if (!proposals.value || proposals.value.length === 0) return

  const checks = proposals.value.map(async (prop) => {
    const ownerAddress = proposalOwnersMap.value[prop.proposalId]
    if (!ownerAddress) return

    try {
      const isAuthorized = await cfpService.isAuthorizedToWithdrawGuarantee(callId.value, ownerAddress)
      authorizedWithdrawMap.value[prop.proposalId] = Boolean(isAuthorized)
    } catch (err) {
      console.error(`Error verificando autorización para ${ownerAddress}:`, err)
      authorizedWithdrawMap.value[prop.proposalId] = false
    }
  })

  await Promise.all(checks)
}

/**
 * Autoriza el retiro de garantía a un usuario utilizando la dirección vinculada a su propuesta
 */
const handleAuthorizeGuarantee = async (proposalId) => {
  const userAddress = proposalOwnersMap.value[proposalId]
  if (!userAddress) {
    verificationDialog.value = {
      open: true,
      success: false,
      message: 'No se pudo determinar la dirección Ethereum asociada a esta propuesta.',
      filesVerification: null
    }
    return
  }

  try {
    authorizingMap.value[proposalId] = true

    // Invocar el contrato pasándole la dirección del usuario
    await cfpService.authorizeGuaranteeWithdraw(callId.value, userAddress)

    // Notificación de éxito
    verificationDialog.value = {
      open: true,
      success: true,
      message: `Se ha autorizado con éxito el retiro de garantía para ${userAddress}.`,
      filesVerification: null
    }

    // Actualiza el mapa de estado para cambiar el botón
    authorizedWithdrawMap.value[proposalId] = true
  } catch (err) {
    console.error("Error al autorizar retiro de garantía:", err)
    verificationDialog.value = {
      open: true,
      success: false,
      message: err.code === 4001 || err.message?.includes('user rejected')
        ? 'Transacción cancelada por el usuario en MetaMask.'
        : `Error en la red: ${err.message || 'No se pudo completar la autorización.'}`,
      filesVerification: null
    }
  } finally {
    authorizingMap.value[proposalId] = false
  }
}


/**
 * Ejecuta la transferencia de los tokens autorizados desde la dirección
 * del contrato hacia la billetera del usuario conectado.
 */
const handleWithdrawGuarantee = async () => {
  if (!walletStore.account || !canWithdrawGuarantee.value || !cfpContractAddress.value) return

  try {
    withdrawingGuarantee.value = true

    // Transferir tokens desde el contrato del llamado hacia la cuenta del usuario
    await tokenService.transferFrom(
      cfpContractAddress.value, // Origen: Dirección del contrato del llamado
      walletStore.account,      // Destino: Billetera del usuario
      guaranteeAmount.value     // Monto de la garantía
    )

    // Notificación de éxito
    verificationDialog.value = {
      open: true,
      success: true,
      message: `¡Garantía de ${formatTokenAmount(guaranteeAmount.value)} BEN transferida con éxito a tu billetera!`,
      filesVerification: null
    }

    // Actualizar estados
    await checkWithdrawableGuarantee()
    await checkAllowanceAndGuarantee()

  } catch (err) {
    console.error("Error al transferir la garantía:", err)
    verificationDialog.value = {
      open: true,
      success: false,
      message: err.message?.includes('user rejected') 
        ? "Transacción cancelada por el usuario en MetaMask." 
        : `Error en la transferencia: ${err.message || "No se pudo transferir la garantía desde la cuenta del contrato."}`,
      filesVerification: null
    }
  } finally {
    withdrawingGuarantee.value = false
  }
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

const submitProposalSystem = async () => {
  if (!formRef.value || hasRestrictedRole.value) return
  const { valid } = await formRef.value.validate()
  if (!valid) return

  if (selectedFilesList.value.length === 0) {
    fileError.value = 'Debes incluir al menos un archivo comprobatorio.'
    return
  }

  try {
    submitting.value = true
    fileError.value = null

    // Si requiere garantía, registrar primero en Blockchain
    if (Number(guaranteeAmount.value) > 0) {
      if (!localProposalId.value) {
        fileError.value = 'No se pudo generar el ID local de la propuesta.'
        submitting.value = false
        return
      }

      // Llama al Smart Contract (MetaMask)
      await cfpService.registerProposal(callId.value, localProposalId.value)
    }

    // Una vez confirmada la blockchain (o si no requiere garantía), registrar en API
    const payload = {
      callId: callId.value,
      title: formProposal.value.title,
      description: formProposal.value.description,
      files: selectedFilesList.value.map(file => file.hash),
      blockchain: !(Number(guaranteeAmount.value) > 0) // Flag según si requería o no garantía
    }

    await apiRegisterProposal(payload)

    // Éxito total: cerrar modal y recargar
    dialogOpen.value = false
    await loadProposals()

  } catch (error) {
    console.error("Error en el registro del sistema:", error)
    
    if (error.code === 4001 || error.message?.includes('user rejected')) {
      fileError.value = 'Transacción rechazada por el usuario en MetaMask.'
    } else {
      fileError.value = `Error procesando el registro: ${error.response?.data?.message || error.message || 'Error de conexión.'}`
    }
  } finally {
    submitting.value = false
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



/**
 * Verifica si el usuario actualmente conectado es el creador de una propuesta específica
 */
const isProposalOwner = (proposal) => {
  if (!walletStore.account || !proposal || !proposal.proposalId) return false

  const currentAccount = walletStore.account.toLowerCase().trim()
  const ownerOnChain = proposalOwnersMap.value[proposal.proposalId]

  return ownerOnChain === currentAccount
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

/**
 * Función para llamar al método closeFileSubmission() del contrato
 */
const handleCloseFileSubmission = async () => {
  if (!callId.value) return
  try {
    closingFileSubmission.value = true
    
    // Llamada a la blockchain
    await cfpService.closeFileSubmission(callId.value)

    // Notificación de éxito
    verificationDialog.value = {
      open: true,
      success: true,
      message: 'Se ha cerrado correctamente la entrega de archivos en el Smart Contract.',
      filesVerification: null
    }

    //consultar el estado para refrescar los controles de la UI
    await checkIsFileSubmissionOpen()
  } catch (err) {
    console.error("Error al cerrar la entrega de archivos:", err)
    verificationDialog.value = {
      open: true,
      success: false,
      message: err.code === 4001 || err.message?.includes('user rejected')
        ? 'Transacción cancelada por el usuario en MetaMask.'
        : `Error al cerrar la entrega de archivos: ${err.message || 'Ocurrió un problema en la red.'}`,
      filesVerification: null
    }
  } finally {
    closingFileSubmission.value = false
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
  } catch (err) {
    console.error('Error al intentar copiar al portapapeles:', err)
  }
}
watch(() => walletStore.account, () => {
  checkWithdrawableGuarantee()
})

onMounted(() => {
  if (callId.value) { loadCallDetails(); loadProposals(); checkWithdrawableGuarantee(); checkIsFileSubmissionOpen();}
  clockInterval = setInterval(() => { currentTime.value = new Date() }, 1000)
})
onBeforeUnmount(() => { if (clockInterval) clearInterval(clockInterval) })
</script>

<style scoped>
.bg-container { min-height: 100vh; overflow: hidden; }
.blur-background { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-size: cover; background-position: center; filter: blur(10px) brightness(0.85); transform: scale(1.05); z-index: 0; }
.z-index-1 { z-index: 1; }
.bg-slate-light { background-color: #ffffff !important; border: 1px solid #e2e8f0; }
.bg-slate-light-flat { background-color: #f8fafc !important; }
.border-light { border: 1px solid #e2e8f0 !important; }
.italic-description { font-style: italic; word-wrap: break-word; white-space: normal; }
.text-slate-dark { color: #0f172a !important; }
.text-slate-medium { color: #475569 !important; }
.text-mono { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
.text-xxs { font-size: 0.7rem; }
.max-w-70 { max-width: 70%; }
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
.gap-1 { gap: 4px; }
.cursor-default { cursor: default !important; }
main-panel { 
  background-color: rgba(248, 250, 252, 0.92) !important; 
  backdrop-filter: blur(12px); 
  border: 1px solid rgba(255, 255, 255, 0.6); 

  height: 90vh; 
  max-height: 90vh; 
  display: flex; 
  flex-direction: column; 
  overflow: hidden; 
}


.proposals-scroll-container { 
  overflow-y: auto !important; 
  flex: 1 1 auto; 
  min-height: 0;  
  padding-right: 4px;
}


:deep(.v-expansion-panel-text__wrapper) {

  padding: 12px 16px !important;
}
</style>