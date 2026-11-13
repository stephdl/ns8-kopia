<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("status.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getStatus">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-status')"
          :description="error.getStatus"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getHealth">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-health')"
          :description="error.getHealth"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.listClients">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.list-clients')"
          :description="error.listClients"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.listBackupRepositories">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.list-backup-repositories')"
          :description="error.listBackupRepositories"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.listBackups">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.list-backups')"
          :description="error.listBackups"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="isDiskAlmostFull">
      <cv-column>
        <NsInlineNotification
          kind="warning"
          :title="$t('status.disk_almost_full_title')"
          :description="
            $t('status.disk_almost_full_description', {
              percent: health.disk.percent,
            })
          "
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="isCertificateNear">
      <cv-column>
        <NsInlineNotification
          kind="warning"
          :title="$t('status.certificate_near_title')"
          :description="$t('status.certificate_near_description')"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="health.verify && health.verify.unfinished">
      <cv-column>
        <NsInlineNotification
          kind="warning"
          :title="$t('status.verify_unfinished_title')"
          :description="$t('status.verify_unfinished_description')"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-else-if="health.verify && !health.verify.ok">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('status.verify_failed_title')"
          :description="$t('status.verify_failed_description')"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <div
          class="card-grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 3xl:grid-cols-4"
        >
          <NsInfoCard
            light
            :title="$t('status.admin_web_ui')"
            :description="host ? host : $t('status.not_configured')"
            :icon="Wikis32"
            :loading="loading.getConfiguration"
            :isErrorShown="!!error.getConfiguration"
            :errorTitle="$t('error.cannot_retrieve_configuration')"
            :errorDescription="error.getConfiguration"
            class="min-height-card"
          >
            <template slot="content">
              <div v-if="host" class="card-rows">
                <div class="card-row">
                  <NsButton
                    kind="ghost"
                    :icon="Launch20"
                    :disabled="loading.getConfiguration"
                    @click="goToWebapp"
                  >
                    {{ $t("status.open_webapp") }}
                  </NsButton>
                </div>
                <div class="card-row">{{ $t("status.admin_user_note") }}</div>
              </div>
              <NsButton
                v-else
                kind="ghost"
                :disabled="loading.getConfiguration"
                :icon="ArrowRight20"
                @click="goToAppPage(instanceName, 'settings')"
              >
                {{ $t("status.configure") }}
              </NsButton>
            </template>
          </NsInfoCard>
          <NsInfoCard
            light
            :title="status.instance || '-'"
            :description="$t('status.app_instance')"
            :icon="Application32"
            :loading="loading.getStatus"
            class="min-height-card"
          >
            <template slot="content">
              <div class="card-rows">
                <div class="card-row">
                  <NsButton
                    kind="ghost"
                    :icon="Restart20"
                    :disabled="loading.getStatus || !status.node"
                    @click="isShownRestartModuleModal = true"
                  >
                    {{ core.$t("apps_status.restart_application") }}
                  </NsButton>
                </div>
              </div>
            </template>
          </NsInfoCard>
          <NsInfoCard
            light
            :title="installationNodeTitle"
            :titleTooltip="installationNodeTitleTooltip"
            :description="$t('status.installation_node')"
            :icon="Chip32"
            :loading="loading.getStatus"
            class="min-height-card"
          >
            <template slot="content">
              <div class="card-rows">
                <div class="card-row">
                  <NsButton
                    kind="ghost"
                    :icon="ArrowRight20"
                    :disabled="loading.getStatus || !status.node"
                    @click="goToNodeDetails"
                  >
                    {{ core.$t("apps_status.go_to_node_details") }}
                  </NsButton>
                </div>
              </div>
            </template>
          </NsInfoCard>
          <NsInfoCard
            v-if="isConfigured"
            light
            :title="diskTitle"
            :description="$t('status.disk')"
            :icon="DataBase32"
            :loading="loading.getHealth"
            class="min-height-card"
          >
            <!-- NsInfoCard checks the slot once, so the wrapper must exist from the first render -->
            <template slot="content">
              <div>
                <span v-if="health.disk">
                  {{
                    $t("status.disk_detail", {
                      used: byteFormat(health.disk.used),
                      total: byteFormat(health.disk.total),
                    })
                  }}
                </span>
              </div>
            </template>
          </NsInfoCard>
          <NsInfoCard
            v-if="isConfigured"
            light
            :title="certificateTitle"
            :description="$t('status.certificate')"
            :icon="Certificate32"
            :loading="loading.getHealth"
            class="min-height-card"
          >
            <template slot="content">
              <div class="card-rows">
                <div v-if="health.certificate">
                  {{ $t("status.certificate_expires") }}
                  {{ formatDateTime(health.certificate.expires) }}
                </div>
                <div class="mg-top-sm">
                  {{ $t("status.certificate_note") }}
                </div>
              </div>
            </template>
          </NsInfoCard>
          <NsInfoCard
            v-if="isConfigured"
            light
            :title="verifyTitle"
            :description="$t('status.verify')"
            :icon="Checkmark32"
            :loading="loading.getHealth"
            class="min-height-card"
          >
            <template slot="content">
              <div>
                <div v-if="health.verify" class="card-rows">
                  <div>{{ formatDateTime(health.verify.finished) }}</div>
                  <div v-if="verifyDuration" class="mg-top-sm">
                    {{
                      $t("status.verify_duration", { duration: verifyDuration })
                    }}
                  </div>
                  <div
                    v-if="Number.isInteger(health.verify.percent)"
                    class="mg-top-sm"
                  >
                    {{
                      $t("status.verify_percent", {
                        percent: health.verify.percent,
                      })
                    }}
                  </div>
                </div>
                <pre
                  v-if="
                    health.verify &&
                    !health.verify.ok &&
                    !health.verify.unfinished
                  "
                  class="verify-details"
                  >{{ health.verify.details }}</pre
                >
              </div>
            </template>
          </NsInfoCard>
          <NsInfoCard
            v-if="isConfigured"
            light
            :title="
              $tc('status.machines_count', clients.length, {
                count: clients.length,
              })
            "
            :description="$t('status.machines')"
            :icon="Devices32"
            :loading="loading.listClients"
            class="min-height-card"
          >
            <template slot="content">
              <div class="card-rows">
                <div class="card-row machine-tags">
                  <NsTag
                    v-for="state in clientStates"
                    :key="state"
                    :label="
                      $t('clients.state_' + state) + ': ' + stateCount[state]
                    "
                    :kind="stateKind(state)"
                    :class="{ 'tag-late': state === 'late' }"
                    size="sm"
                  />
                </div>
                <div class="card-row">
                  <NsButton
                    kind="ghost"
                    :icon="ArrowRight20"
                    @click="goToAppPage(instanceName, 'clients')"
                  >
                    {{ $t("status.go_to_clients") }}
                  </NsButton>
                </div>
              </div>
            </template>
          </NsInfoCard>
          <NsBackupCard
            :title="core.$t('backup.title')"
            :noBackupMessage="core.$t('backup.no_backup_configured')"
            :goToBackupLabel="core.$t('backup.go_to_backup')"
            :repositoryLabel="core.$t('backup.repository')"
            :statusLabel="core.$t('common.status')"
            :statusSuccessLabel="core.$t('common.success')"
            :statusNotRunLabel="core.$t('backup.backup_has_not_run_yet')"
            :statusErrorLabel="core.$t('error.error')"
            :completedLabel="core.$t('backup.completed')"
            :durationLabel="core.$t('backup.duration')"
            :totalSizeLabel="core.$t('backup.total_size')"
            :totalFileCountLabel="core.$t('backup.total_file_count')"
            :backupDisabledLabel="core.$t('common.disabled')"
            :showMoreLabel="core.$t('common.show_more')"
            :multipleUncertainStatusLabel="
              core.$t('backup.some_backups_failed_or_are_pending')
            "
            :moduleId="instanceName"
            :moduleUiName="instanceLabel"
            :repositories="backupRepositories"
            :backups="backups"
            :loading="loading.listBackupRepositories || loading.listBackups"
            :coreContext="core"
            light
          />
          <NsSystemLogsCard
            :title="core.$t('system_logs.card_title')"
            :description="
              core.$t('system_logs.card_description', {
                name: instanceLabel || instanceName,
              })
            "
            :buttonLabel="core.$t('system_logs.card_button_label')"
            :router="core.$router"
            context="module"
            :moduleId="instanceName"
            light
          />
        </div>
      </cv-column>
    </cv-row>
    <!-- services -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $t("status.failed_services") }}</h4>
      </cv-column>
    </cv-row>
    <cv-row v-if="!loading.getStatus">
      <cv-column v-if="!status.services.length">
        <cv-tile light>
          <NsEmptyState :title="$t('status.no_services')"> </NsEmptyState>
        </cv-tile>
      </cv-column>
      <cv-column v-else-if="!failedServices.length">
        <cv-tile light>
          <NsEmptyState :title="$t('status.all_services_running')">
            <template #pictogram>
              <CircleCheckPictogram />
            </template>
          </NsEmptyState>
        </cv-tile>
      </cv-column>
      <cv-column v-else>
        <div
          class="card-grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 3xl:grid-cols-4"
        >
          <NsSystemdServiceCard
            v-for="service in failedServices"
            :key="service.name"
            light
            class="min-height-card"
            :serviceName="service.name"
            :active="service.active"
            :failed="service.failed"
            :enabled="service.enabled"
            :icon="Cube32"
          />
        </div>
      </cv-column>
    </cv-row>
    <cv-row v-else>
      <cv-column :md="4" :max="4">
        <cv-tile light>
          <cv-skeleton-text
            :paragraph="true"
            :line-count="4"
          ></cv-skeleton-text>
        </cv-tile>
      </cv-column>
    </cv-row>
    <!-- images -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $tc("status.app_images", 2) }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div v-if="!loading.getStatus">
            <NsEmptyState
              v-if="!status.images.length"
              :title="$t('status.no_images')"
            >
            </NsEmptyState>
            <NsDataTable
              v-else
              :allRows="status.images"
              :columns="i18nImagesTableColumns"
              :rawColumns="imagesTableColumns"
              :sortable="true"
              :pageSizes="[5, 10, 25, 50, 100]"
              :overflow-menu="false"
              isSearchable
              :searchPlaceholder="$t('status.search_images')"
              :searchClearLabel="core.$t('common.clear_search')"
              :noSearchResultsLabel="core.$t('common.no_search_results')"
              :noSearchResultsDescription="
                core.$t('common.no_search_results_description')
              "
              :itemsPerPageLabel="core.$t('pagination.items_per_page')"
              :rangeOfTotalItemsLabel="
                core.$t('pagination.range_of_total_items')
              "
              :ofTotalPagesLabel="core.$t('pagination.of_total_pages')"
              :backwardText="core.$t('pagination.previous_page')"
              :forwardText="core.$t('pagination.next_page')"
              :pageNumberLabel="core.$t('pagination.page_number')"
              @updatePage="imagesTablePage = $event"
            >
              <template slot="data">
                <cv-data-table-row
                  v-for="(row, rowIndex) in imagesTablePage"
                  :key="`${rowIndex}`"
                  :value="`${rowIndex}`"
                >
                  <cv-data-table-cell>
                    <span>
                      {{ row.name }}
                    </span>
                  </cv-data-table-cell>
                  <cv-data-table-cell>
                    <span>{{ row.size }}</span>
                  </cv-data-table-cell>
                  <cv-data-table-cell>
                    <span>{{ row.created }}</span>
                  </cv-data-table-cell>
                </cv-data-table-row>
              </template>
            </NsDataTable>
          </div>
          <cv-skeleton-text
            v-else
            :paragraph="true"
            :line-count="5"
          ></cv-skeleton-text>
        </cv-tile>
      </cv-column>
    </cv-row>
    <!-- volumes -->
    <cv-row>
      <cv-column class="page-subtitle">
        <h4>{{ $tc("status.app_volumes", 2) }}</h4>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div v-if="!loading.getStatus">
            <NsEmptyState
              v-if="!status.volumes.length"
              :title="$t('status.no_volumes')"
            >
            </NsEmptyState>
            <NsDataTable
              v-else
              :allRows="status.volumes"
              :columns="i18nVolumesTableColumns"
              :rawColumns="volumesTableColumns"
              :sortable="true"
              :pageSizes="[5, 10, 25, 50, 100]"
              :overflow-menu="false"
              isSearchable
              :searchPlaceholder="$t('status.search_volumes')"
              :searchClearLabel="core.$t('common.clear_search')"
              :noSearchResultsLabel="core.$t('common.no_search_results')"
              :noSearchResultsDescription="
                core.$t('common.no_search_results_description')
              "
              :itemsPerPageLabel="core.$t('pagination.items_per_page')"
              :rangeOfTotalItemsLabel="
                core.$t('pagination.range_of_total_items')
              "
              :ofTotalPagesLabel="core.$t('pagination.of_total_pages')"
              :backwardText="core.$t('pagination.previous_page')"
              :forwardText="core.$t('pagination.next_page')"
              :pageNumberLabel="core.$t('pagination.page_number')"
              @updatePage="volumesTablePage = $event"
            >
              <template slot="data">
                <cv-data-table-row
                  v-for="(row, rowIndex) in volumesTablePage"
                  :key="`${rowIndex}`"
                  :value="`${rowIndex}`"
                >
                  <cv-data-table-cell>
                    <span>
                      {{ row.name }}
                    </span>
                  </cv-data-table-cell>
                  <cv-data-table-cell>
                    <span>{{ row.mount }}</span>
                  </cv-data-table-cell>
                  <cv-data-table-cell>
                    <span>{{ row.created }}</span>
                  </cv-data-table-cell>
                </cv-data-table-row>
              </template>
            </NsDataTable>
          </div>
          <cv-skeleton-text
            v-else
            :paragraph="true"
            :line-count="10"
          ></cv-skeleton-text>
        </cv-tile>
      </cv-column>
    </cv-row>
    <RestartModuleModal
      :visible="isShownRestartModuleModal"
      :node="status.node"
      @hide="isShownRestartModuleModal = false"
    />
  </cv-grid>
</template>

<script>
import to from "await-to-js";
import moduleTask from "@/mixins/moduleTask";
import { mapState } from "vuex";
import RestartModuleModal from "@/components/RestartModuleModal.vue";
// Not in IconService.
import Restart20 from "@carbon/icons-vue/es/restart/20";
import Devices32 from "@carbon/icons-vue/es/devices/32";
import Checkmark32 from "@carbon/icons-vue/es/checkmark/32";
import {
  QueryParamService,
  TaskService,
  IconService,
  UtilService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

const LONG_RUNNING_SERVICES = ["kopia", "kopia-server"];
const CERTIFICATE_WARNING_DAYS = 30;
const DISK_WARNING_PERCENT = 85;
const CLIENT_STATES = ["ok", "late", "late_admin", "never_seen", "unknown"];

export default {
  name: "Status",
  components: { RestartModuleModal },
  mixins: [
    moduleTask,
    TaskService,
    QueryParamService,
    IconService,
    UtilService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("status.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "status",
      },
      urlCheckInterval: null,
      host: "",
      status: {
        instance: "",
        services: [],
        images: [],
        volumes: [],
      },
      imagesTablePage: [],
      imagesTableColumns: ["name", "size", "created"],
      volumesTablePage: [],
      volumesTableColumns: ["name", "mount", "created"],
      health: {
        server: "",
        disk: null,
        certificate: null,
        verify: null,
      },
      clients: [],
      clientStates: CLIENT_STATES,
      backupRepositories: [],
      backups: [],
      isShownRestartModuleModal: false,
      Restart20,
      Devices32,
      Checkmark32,
      loading: {
        getConfiguration: false,
        getStatus: false,
        getHealth: false,
        listClients: false,
        listBackupRepositories: false,
        listBackups: false,
      },
      error: {
        getConfiguration: "",
        getStatus: "",
        getHealth: "",
        listClients: "",
        listBackupRepositories: "",
        listBackups: "",
      },
    };
  },
  computed: {
    verifyDuration() {
      const verify = this.health.verify;
      if (!verify || !verify.started || !verify.finished) {
        return "";
      }
      const seconds = Math.round(
        (new Date(verify.finished) - new Date(verify.started)) / 1000
      );
      return isNaN(seconds) || seconds < 0 ? "" : this.formatDuration(seconds);
    },
    failedServices() {
      // A stopped server is not "failed" for systemd, but it must run. The check and verify
      // services are one-shot jobs, inactive between two runs.
      return (this.status.services || []).filter(
        (service) =>
          service.failed ||
          (LONG_RUNNING_SERVICES.includes(service.name) && !service.active)
      );
    },
    i18nImagesTableColumns() {
      return this.imagesTableColumns.map((col) => this.$t(`status.${col}`));
    },
    i18nVolumesTableColumns() {
      return this.volumesTableColumns.map((col) => this.$t(`status.${col}`));
    },
    ...mapState(["instanceName", "instanceLabel", "core", "appName"]),
    isConfigured() {
      return this.host !== "";
    },
    installationNodeTitle() {
      if (this.status && this.status.node) {
        if (this.status.node_ui_name) {
          return this.status.node_ui_name;
        } else {
          return this.$t("status.node") + " " + this.status.node;
        }
      } else {
        return "-";
      }
    },
    installationNodeTitleTooltip() {
      if (this.status && this.status.node_ui_name) {
        return this.$t("status.node") + " " + this.status.node;
      } else {
        return "";
      }
    },
    isDiskAlmostFull() {
      return (
        !!this.health.disk && this.health.disk.percent >= DISK_WARNING_PERCENT
      );
    },
    isCertificateNear() {
      return (
        !!this.health.certificate &&
        this.health.certificate.days_left <= CERTIFICATE_WARNING_DAYS
      );
    },
    diskTitle() {
      return this.health.disk
        ? this.$t("status.disk_used", { percent: this.health.disk.percent })
        : "-";
    },
    certificateTitle() {
      if (!this.health.certificate) {
        return "-";
      }
      return this.$tc("status.days_left", this.health.certificate.days_left, {
        count: this.health.certificate.days_left,
      });
    },
    verifyTitle() {
      if (!this.health.verify) {
        return this.$t("status.verify_never");
      }
      if (this.health.verify.unfinished) {
        return this.$t("status.verify_unfinished");
      }
      return this.health.verify.ok
        ? this.$t("status.verify_ok")
        : this.$t("status.verify_failed");
    },
    stateCount() {
      const count = {};
      for (const state of CLIENT_STATES) {
        count[state] = this.clients.filter((c) => c.state === state).length;
      }
      return count;
    },
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.watchQueryData(vm);
      vm.urlCheckInterval = vm.initUrlBindingForApp(vm, vm.q.page);
    });
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.urlCheckInterval);
    next();
  },
  created() {
    this.getStatus();
    this.getConfiguration();
    this.listBackupRepositories();
  },
  methods: {
    byteFormat(value) {
      return this.$options.filters.byteFormat(value);
    },
    formatDuration(seconds) {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      if (hours) {
        return `${hours} h ${minutes} min`;
      }
      if (minutes) {
        return `${minutes} min`;
      }
      return `${seconds} s`;
    },
    formatDateTime(value) {
      if (!value) {
        return "-";
      }
      const date = new Date(value);
      return isNaN(date.getTime()) ? value : date.toLocaleString();
    },
    stateKind(state) {
      if (state === "ok") return "green";
      // Carbon has no yellow tag, the tag-late class paints it
      if (state === "late") return "gray";
      if (state === "late_admin") return "red";
      return "gray";
    },
    goToNodeDetails() {
      if (this.status && this.status.node) {
        this.core.$router.push(`/nodes/${this.status.node}`);
      }
    },
    goToWebapp() {
      window.open(`https://${this.host}/`, "_blank", "noopener");
    },
    getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      const fail = (message) => {
        this.error.getConfiguration = message;
        this.loading.getConfiguration = false;
      };
      this.runModuleTask({
        action: "get-configuration",
        completed: (output) => {
          this.host = output.host;
          this.loading.getConfiguration = false;
          // Before the first configuration there is no server to ask
          if (this.isConfigured) {
            this.getHealth();
            this.listClients();
          }
        },
        aborted: fail,
        failed: fail,
      });
    },
    getHealth() {
      this.loading.getHealth = true;
      this.error.getHealth = "";
      const fail = (message) => {
        this.error.getHealth = message;
        this.loading.getHealth = false;
      };
      this.runModuleTask({
        action: "get-health",
        completed: (output) => {
          this.health = output;
          this.loading.getHealth = false;
        },
        aborted: fail,
        failed: fail,
      });
    },
    listClients() {
      this.loading.listClients = true;
      this.error.listClients = "";
      const fail = (message) => {
        this.error.listClients = message;
        this.loading.listClients = false;
      };
      this.runModuleTask({
        action: "list-clients",
        completed: (output) => {
          this.clients = output.clients;
          this.loading.listClients = false;
        },
        aborted: fail,
        failed: fail,
      });
    },
    getStatus() {
      this.loading.getStatus = true;
      this.error.getStatus = "";
      const fail = (message) => {
        this.error.getStatus = message;
        this.loading.getStatus = false;
      };
      this.runModuleTask({
        action: "get-status",
        completed: (output) => {
          this.status = output;
          this.loading.getStatus = false;
        },
        aborted: fail,
        failed: fail,
      });
    },
    async listBackupRepositories() {
      this.loading.listBackupRepositories = true;
      this.error.listBackupRepositories = "";
      const taskAction = "list-backup-repositories";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.listBackupRepositoriesAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.listBackupRepositoriesCompleted
      );

      const res = await to(
        this.createClusterTaskForApp({
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.listBackupRepositories = this.getErrorMessage(err);
        this.loading.listBackupRepositories = false;
        return;
      }
    },
    listBackupRepositoriesAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.listBackupRepositories = this.$t("error.generic_error");
      this.loading.listBackupRepositories = false;
    },
    listBackupRepositoriesCompleted(taskContext, taskResult) {
      let backupRepositories = taskResult.output.repositories.sort(
        this.sortByProperty("name")
      );
      this.backupRepositories = backupRepositories;
      this.loading.listBackupRepositories = false;
      this.listBackups();
    },
    async listBackups() {
      this.loading.listBackups = true;
      this.error.listBackups = "";
      const taskAction = "list-backups";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.listBackupsAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.listBackupsCompleted
      );

      const res = await to(
        this.createClusterTaskForApp({
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.listBackups = this.getErrorMessage(err);
        this.loading.listBackups = false;
        return;
      }
    },
    listBackupsAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.listBackups = this.$t("error.generic_error");
      this.loading.listBackups = false;
    },
    listBackupsCompleted(taskContext, taskResult) {
      let backups = taskResult.output.backups;
      backups.sort(this.sortByProperty("name"));

      // get repository name
      for (const backup of backups) {
        const repo = this.backupRepositories.find(
          (r) => r.id == backup.repository
        );

        if (repo) {
          backup.repoName = repo.name;
        }
      }
      this.backups = backups;
      this.loading.listBackups = false;
    },
  },
};
</script>

<style scoped lang="scss">
.card-rows {
  text-align: center;
}

@import "../styles/carbon-utils";

.break-word {
  word-wrap: break-word;
  overflow-wrap: anywhere;
}

.mg-top-sm {
  margin-top: $spacing-03;
}

.machine-tags {
  display: flex;
  flex-wrap: wrap;
}

.tag-late {
  background-color: #f1c21b;
  color: #161616;
}

.verify-details {
  max-height: 8rem;
  overflow: auto;
  font-size: 0.75rem;
  white-space: pre-wrap;
}
</style>
