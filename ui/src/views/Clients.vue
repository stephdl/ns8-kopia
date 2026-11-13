<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("clients.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.removeClient">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.remove-client')"
          :description="error.removeClient"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="error.resetClient && !isShownResetModal">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.reset-client-password')"
          :description="error.resetClient"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <div class="toolbar">
            <NsButton
              kind="primary"
              :icon="Add20"
              :disabled="!configured || loading.getConfiguration"
              @click="showAddModal"
              >{{ $t("clients.add_machine") }}</NsButton
            >
            <NsButton
              kind="secondary"
              :icon="Restart20"
              :loading="loading.listClients"
              :disabled="loading.listClients || !configured"
              @click="listClients"
              >{{ $t("clients.refresh") }}</NsButton
            >
          </div>
          <NsDataTable
            :allRows="clients"
            :columns="i18nTableColumns"
            :rawColumns="tableColumns"
            :sortable="true"
            :pageSizes="[10, 25, 50, 100]"
            :overflow-menu="true"
            isSearchable
            :searchPlaceholder="$t('clients.search_machines')"
            :searchClearLabel="core.$t('common.clear_search')"
            :noSearchResultsLabel="core.$t('common.no_search_results')"
            :noSearchResultsDescription="
              core.$t('common.no_search_results_description')
            "
            :isLoading="loading.getConfiguration || loading.listClients"
            :skeletonRows="3"
            :isErrorShown="!!error.listClients"
            :errorTitle="$t('action.list-clients')"
            :errorDescription="error.listClients"
            :itemsPerPageLabel="core.$t('pagination.items_per_page')"
            :rangeOfTotalItemsLabel="core.$t('pagination.range_of_total_items')"
            :ofTotalPagesLabel="core.$t('pagination.of_total_pages')"
            :backwardText="core.$t('pagination.previous_page')"
            :forwardText="core.$t('pagination.next_page')"
            :pageNumberLabel="core.$t('pagination.page_number')"
            @updatePage="tablePage = $event"
          >
            <template slot="empty-state">
              <NsEmptyState
                v-if="!configured"
                :title="$t('status.not_configured')"
              >
                <template #description>
                  <div class="mg-bottom">
                    {{ $t("clients.not_configured_description") }}
                  </div>
                  <NsButton
                    kind="ghost"
                    :icon="ArrowRight20"
                    @click="goToAppPage(instanceName, 'settings')"
                    >{{ $t("status.configure") }}</NsButton
                  >
                </template>
              </NsEmptyState>
              <NsEmptyState v-else :title="$t('clients.no_machines')">
                <template #description>
                  <div class="mg-bottom">
                    {{ $t("clients.no_machines_description") }}
                  </div>
                  <NsButton
                    kind="primary"
                    :icon="Add20"
                    @click="showAddModal"
                    >{{ $t("clients.add_machine") }}</NsButton
                  >
                </template>
              </NsEmptyState>
            </template>
            <template slot="data">
              <cv-data-table-row
                v-for="(row, rowIndex) in tablePage"
                :key="`${rowIndex}`"
                :value="`${rowIndex}`"
              >
                <cv-data-table-cell class="break-word">{{
                  row.name
                }}</cv-data-table-cell>
                <cv-data-table-cell class="break-word">{{
                  row.owner_email || "-"
                }}</cv-data-table-cell>
                <cv-data-table-cell>
                  <template v-if="row.last_backup">
                    <div>{{ formatRelative(row.last_backup) }}</div>
                    <div class="absolute-date">
                      {{ formatDateTime(row.last_backup) }}
                    </div>
                  </template>
                  <template v-else>-</template>
                </cv-data-table-cell>
                <cv-data-table-cell>
                  <NsTag
                    :label="$t('clients.state_' + row.state)"
                    :kind="stateKind(row.state)"
                    :class="{ 'tag-late': row.state === 'late' }"
                  />
                </cv-data-table-cell>
                <cv-data-table-cell class="table-overflow-menu-cell">
                  <cv-overflow-menu flip-menu class="table-overflow-menu">
                    <cv-overflow-menu-item @click="showEnrollment(row)">
                      <NsMenuItem
                        :icon="Document20"
                        :label="$t('clients.show_enrollment')"
                      />
                    </cv-overflow-menu-item>
                    <cv-overflow-menu-item @click="showFoldersModal(row)">
                      <NsMenuItem
                        :icon="Folder20"
                        :label="$t('clients.folders')"
                      />
                    </cv-overflow-menu-item>
                    <cv-overflow-menu-item @click="showResetModal(row)">
                      <NsMenuItem
                        :icon="Reset20"
                        :label="$t('clients.reset_password')"
                      />
                    </cv-overflow-menu-item>
                    <NsMenuDivider />
                    <cv-overflow-menu-item danger @click="showRemoveModal(row)">
                      <NsMenuItem
                        :icon="TrashCan20"
                        :label="$t('clients.remove')"
                      />
                    </cv-overflow-menu-item>
                  </cv-overflow-menu>
                </cv-data-table-cell>
              </cv-data-table-row>
            </template>
          </NsDataTable>
        </cv-tile>
      </cv-column>
    </cv-row>
    <!-- add -->
    <NsModal
      size="default"
      :visible="isShownAddModal"
      :primary-button-disabled="loading.addClient || loading.countSnapshots"
      :isLoading="loading.addClient || loading.countSnapshots"
      @modal-hidden="isShownAddModal = false"
      @primary-click="verifyOrAddClient"
    >
      <template slot="title">{{ $t("clients.add_machine") }}</template>
      <template slot="content">
        <p class="mg-bottom">{{ $t("clients.add_description") }}</p>
        <cv-form @submit.prevent="verifyOrAddClient">
          <NsTextInput
            v-model.trim="newUsername"
            :label="$t('clients.username')"
            :helper-text="$t('clients.username_helper')"
            placeholder="accounting"
            :invalid-message="$t(error.username)"
            :disabled="loading.addClient"
            class="mg-bottom"
            ref="username"
          />
          <NsTextInput
            v-model.trim="newHostname"
            :label="$t('clients.hostname')"
            :helper-text="$t('clients.hostname_helper')"
            placeholder="pc-accounting-01"
            :invalid-message="$t(error.hostname)"
            :disabled="loading.addClient"
            class="mg-bottom"
            ref="hostname"
          />
          <NsTextInput
            v-model.trim="newOwnerEmail"
            type="email"
            :label="$t('clients.owner_email')"
            :helper-text="$t('clients.owner_email_helper')"
            placeholder="anna@example.org"
            :invalid-message="$t(error.owner_email)"
            :disabled="loading.addClient"
            class="mg-bottom"
            ref="owner_email"
          />
          <NsInlineNotification
            v-if="existingSnapshots"
            kind="warning"
            :title="$t('clients.existing_snapshots_title')"
            :description="
              $t('clients.existing_snapshots_description', {
                count: existingSnapshots.count,
                first: formatDateTime(existingSnapshots.first),
                last: formatDateTime(existingSnapshots.last),
              })
            "
            :showCloseButton="false"
          />
          <NsInlineNotification
            v-if="error.countSnapshots"
            kind="error"
            :title="$t('action.count-snapshots')"
            :description="error.countSnapshots"
            :showCloseButton="false"
          />
          <NsInlineNotification
            v-if="error.addClient"
            kind="error"
            :title="$t('action.add-client')"
            :description="error.addClient"
            :showCloseButton="false"
          />
        </cv-form>
      </template>
      <template slot="secondary-button">{{
        core.$t("common.cancel")
      }}</template>
      <template slot="primary-button">{{
        verifiedName ? $t("clients.save") : $t("clients.verify")
      }}</template>
    </NsModal>
    <!-- enrollment -->
    <NsModal
      size="large"
      :visible="isShownEnrollmentModal"
      @modal-hidden="hideEnrollmentModal"
    >
      <template slot="title">{{
        $t("clients.enrollment_title", { name: enrollmentName })
      }}</template>
      <template slot="content">
        <cv-skeleton-text
          v-if="loading.getEnrollment"
          :paragraph="true"
          :line-count="5"
        />
        <NsInlineNotification
          v-if="error.getEnrollment"
          kind="error"
          :title="$t('action.get-client-enrollment')"
          :description="error.getEnrollment"
          :showCloseButton="false"
        />
        <template v-if="enrollment">
          <NsInlineNotification
            v-if="enrollment.password"
            kind="warning"
            :title="$t('clients.enrollment_once_title')"
            :description="$t('clients.enrollment_once_description')"
            :showCloseButton="false"
          />
          <NsInlineNotification
            v-else
            kind="info"
            :title="$t('clients.enrollment_hidden_title')"
            :description="$t('clients.enrollment_hidden_description')"
            :actionLabel="$t('clients.reset_password')"
            @action="resetFromEnrollment"
            :showCloseButton="false"
          />
          <p class="mg-bottom">
            {{
              enrollment.password
                ? $t("clients.enrollment_intro")
                : $t("clients.enrollment_details_intro")
            }}
          </p>
          <NsInlineNotification
            v-if="enrollment.password"
            kind="warning"
            :title="$t('clients.enrollment_user_title')"
            :description="$t('clients.enrollment_user_description')"
            :showCloseButton="false"
          />
          <NsInlineNotification
            v-if="enrollment.password"
            kind="warning"
            :title="$t('clients.enrollment_secret_title')"
            :description="$t('clients.enrollment_secret_description')"
            :showCloseButton="false"
          />
          <div class="enrollment-facts mg-bottom">
            <div>
              <span class="fact-label">{{ $t("clients.url") }}</span>
              <code class="break-word">{{ enrollment.url }}</code>
            </div>
            <div>
              <span class="fact-label">{{ $t("clients.fingerprint") }}</span>
              <code class="break-word">{{ enrollment.fingerprint }}</code>
            </div>
            <div>
              <span class="fact-label">{{ $t("clients.identity") }}</span>
              <code class="break-word"
                >{{ enrollment.username }}@{{ enrollment.hostname }}</code
              >
            </div>
          </div>
          <NsTabs
            v-if="enrollment.password"
            :container="false"
            :aria-label="$t('clients.script_tabs')"
          >
            <cv-tab
              v-for="(tab, index) in scriptTabs"
              :key="tab.id"
              :id="tab.id"
              :label="$t(tab.label)"
              :selected="index === 0"
            >
              <NsCodeSnippet
                :copyTooltip="$t('clients.copy')"
                :copyFeedback="$t('clients.copied')"
                :feedbackAriaLabel="$t('clients.copied')"
                :expanded="true"
                :hideExpandButton="true"
                :wrapText="true"
                >{{ enrollment[tab.script] }}</NsCodeSnippet
              >
            </cv-tab>
          </NsTabs>
        </template>
      </template>
      <template slot="secondary-button">{{ core.$t("common.close") }}</template>
    </NsModal>
    <!-- reset password -->
    <NsModal
      size="default"
      kind="danger"
      :visible="isShownResetModal"
      :primary-button-disabled="loading.resetClient"
      :isLoading="loading.resetClient"
      @modal-hidden="hideResetModal"
      @primary-click="resetClient"
    >
      <template slot="title">{{
        $t("clients.reset_title", {
          name: clientToReset ? clientToReset.name : "",
        })
      }}</template>
      <template slot="content">
        <p class="mg-bottom">{{ $t("clients.reset_warning") }}</p>
        <NsInlineNotification
          v-if="error.resetClient"
          kind="error"
          :title="$t('action.reset-client-password')"
          :description="error.resetClient"
          :showCloseButton="false"
        />
      </template>
      <template slot="secondary-button">{{
        core.$t("common.cancel")
      }}</template>
      <template slot="primary-button">{{
        $t("clients.reset_password")
      }}</template>
    </NsModal>
    <!-- remove -->
    <NsModal
      size="default"
      :visible="isShownFoldersModal"
      @modal-hidden="isShownFoldersModal = false"
    >
      <template slot="title">{{
        $t("clients.folders_title", { name: foldersClient })
      }}</template>
      <template slot="content">
        <div class="folders-header">
          <span class="folders-label">{{ $t("clients.folders") }}</span>
          <NsButton
            kind="ghost"
            size="small"
            :icon="Restart20"
            :loading="loading.listFolders"
            :disabled="loading.listFolders"
            @click="listFolders"
            >{{ $t("clients.refresh") }}</NsButton
          >
        </div>
        <NsInlineNotification
          v-if="error.listFolders"
          kind="error"
          :title="$t('action.list-client-folders')"
          :description="error.listFolders"
          :showCloseButton="false"
        />
        <cv-skeleton-text
          v-else-if="loading.listFolders"
          :paragraph="true"
          :line-count="3"
        />
        <template v-else>
          <p v-if="!folders.length" class="mg-bottom">
            {{ $t("clients.no_folders") }}
          </p>
          <div v-else class="folder-list mg-bottom">
            <div
              v-for="folder in folders"
              :key="folder.path"
              class="folder-row"
            >
              <div class="folder-path">{{ folder.path }}</div>
              <div class="folder-date">
                {{
                  folder.last_backup
                    ? formatDateTime(folder.last_backup)
                    : $t("clients.folder_never")
                }}
              </div>
              <NsButton
                kind="ghost"
                size="small"
                :icon="Launch20"
                @click="openFolderPolicy(folder.path)"
                >{{ $t("clients.folder_open") }}</NsButton
              >
            </div>
          </div>
        </template>
        <cv-form @submit.prevent="addFolder" class="add-folder">
          <cv-text-input
            v-model.trim="newFolder"
            :label="$t('clients.add_folder')"
            :placeholder="$t('clients.folder_placeholder')"
            :helper-text="$t('clients.folder_helper')"
            :invalid-message="error.newFolder ? $t(error.newFolder) : ''"
            ref="newFolder"
            class="add-folder-input"
          />
          <NsButton
            kind="primary"
            size="field"
            :icon="Launch20"
            type="submit"
            class="add-folder-button"
            >{{ $t("clients.folder_add_open") }}</NsButton
          >
        </cv-form>
      </template>
      <template slot="secondary-button">{{ core.$t("common.close") }}</template>
    </NsModal>
    <NsModal
      size="default"
      kind="danger"
      :visible="isShownRemoveModal"
      :primary-button-disabled="loading.removeClient"
      :isLoading="loading.removeClient"
      @modal-hidden="hideRemoveModal"
      @primary-click="removeClient"
    >
      <template slot="title">{{
        $t("clients.remove_title", {
          name: clientToRemove ? clientToRemove.name : "",
        })
      }}</template>
      <template slot="content">
        <p class="mg-bottom">{{ $t("clients.remove_warning") }}</p>
        <cv-checkbox
          v-model="deleteSnapshots"
          value="deleteSnapshots"
          :label="$t('clients.delete_snapshots')"
          :disabled="loading.removeClient"
          class="mg-bottom"
        />
        <p v-if="deleteSnapshots">
          {{ $t("clients.delete_snapshots_warning") }}
        </p>
        <p v-else>{{ $t("clients.remove_snapshots") }}</p>
      </template>
      <template slot="secondary-button">{{
        core.$t("common.cancel")
      }}</template>
      <template slot="primary-button">{{ $t("clients.remove") }}</template>
    </NsModal>
  </cv-grid>
</template>

<script>
import { mapState } from "vuex";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
  DateTimeService,
} from "@nethserver/ns8-ui-lib";
import ModuleTask from "@/mixins/moduleTask";

// Kopia compares paths as text: a Windows path keeps its backslashes and drive letter
const FOLDER_PATTERNS = [/^\/./, /^[A-Za-z]:\\/, /^\\\\[^\\]+\\[^\\]+/];

// Same rule as the backend
const NAME_PATTERN = /^[a-z0-9]([a-z0-9._-]{0,62}[a-z0-9])?$/;

export default {
  name: "Clients",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
    DateTimeService,
    ModuleTask,
  ],
  pageTitle() {
    return this.$t("clients.title") + " - " + this.appName;
  },
  data() {
    return {
      scriptTabs: [
        {
          id: "tab-windows",
          label: "clients.tab_windows",
          script: "powershell",
        },
        { id: "tab-linux", label: "clients.tab_linux", script: "shell" },
        {
          id: "tab-linux-server",
          label: "clients.tab_linux_server",
          script: "server",
        },
      ],
      q: {
        page: "clients",
      },
      urlCheckInterval: null,
      clients: [],
      tablePage: [],
      tableColumns: ["name", "owner_email", "last_backup", "state"],
      // Before the first configuration there is no server to ask
      configured: true,
      isShownAddModal: false,
      newUsername: "",
      newHostname: "",
      newOwnerEmail: "",
      // Name already checked for old snapshots: the next click saves
      verifiedName: "",
      existingSnapshots: null,
      deleteSnapshots: false,
      isShownEnrollmentModal: false,
      enrollmentName: "",
      enrollment: null,
      isShownResetModal: false,
      clientToReset: null,
      isShownRemoveModal: false,
      clientToRemove: null,
      isShownFoldersModal: false,
      foldersClient: "",
      folders: [],
      newFolder: "",
      host: "",
      loading: {
        getConfiguration: false,
        listClients: false,
        addClient: false,
        countSnapshots: false,
        getEnrollment: false,
        resetClient: false,
        removeClient: false,
        listFolders: false,
      },
      error: {
        listClients: "",
        addClient: "",
        countSnapshots: "",
        getEnrollment: "",
        resetClient: "",
        removeClient: "",
        listFolders: "",
        newFolder: "",
        username: "",
        hostname: "",
        owner_email: "",
      },
    };
  },
  watch: {
    newUsername() {
      this.resetVerification();
    },
    newHostname() {
      this.resetVerification();
    },
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    i18nTableColumns() {
      return this.tableColumns.map((column) =>
        this.$t("clients.col_" + column)
      );
    },
  },
  created() {
    this.getConfiguration();
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
  methods: {
    stateKind(state) {
      if (state === "ok") return "green";
      if (state === "late_admin") return "red";
      // Carbon has no yellow tag, the tag-late class paints the late state
      return "gray";
    },
    formatDateTime(value) {
      const date = new Date(value);
      return isNaN(date.getTime()) ? value : date.toLocaleString();
    },
    formatRelative(value) {
      const date = this.parseIsoDate(value);
      if (isNaN(date.getTime())) {
        return value;
      }
      return this.formatDateDistance(date, new Date(), { addSuffix: true });
    },
    isEmail(value) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    getConfiguration() {
      this.loading.getConfiguration = true;
      const done = () => {
        this.loading.getConfiguration = false;
      };
      this.runModuleTask({
        action: "get-configuration",
        completed: (config) => {
          this.configured = config.host !== "";
          this.host = config.host;
          done();
          if (this.configured) {
            this.listClients();
          }
        },
        aborted: done,
        failed: done,
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
    showAddModal() {
      this.newUsername = "";
      this.newHostname = "";
      this.newOwnerEmail = "";
      this.resetVerification();
      this.error.addClient = "";
      this.error.username = "";
      this.error.hostname = "";
      this.error.owner_email = "";
      this.isShownAddModal = true;
    },
    validateAddClient() {
      this.error.username = "";
      this.error.hostname = "";
      this.error.owner_email = "";
      let focus = "";
      for (const field of ["username", "hostname"]) {
        const value =
          field === "username" ? this.newUsername : this.newHostname;
        if (!value) {
          this.error[field] = "common.required";
        } else if (!NAME_PATTERN.test(value)) {
          this.error[field] = "clients.name_format";
        }
        focus = focus || (this.error[field] ? field : "");
      }
      if (this.newOwnerEmail && !this.isEmail(this.newOwnerEmail)) {
        this.error.owner_email = "clients.owner_email_invalid";
        focus = focus || "owner_email";
      }
      if (focus) {
        this.focusElement(focus);
      }
      return !focus;
    },
    resetVerification() {
      this.verifiedName = "";
      this.existingSnapshots = null;
      this.error.countSnapshots = "";
    },
    verifyOrAddClient() {
      if (!this.validateAddClient()) {
        return;
      }
      const name = `${this.newUsername}@${this.newHostname}`;
      if (this.verifiedName === name) {
        this.addClient();
        return;
      }
      this.loading.countSnapshots = true;
      this.error.countSnapshots = "";
      // The admin may cancel or change the name while the check runs: ignore a stale answer
      const isCurrent = () =>
        this.isShownAddModal &&
        `${this.newUsername}@${this.newHostname}` === name;
      const fail = (message) => {
        this.loading.countSnapshots = false;
        if (isCurrent()) {
          this.error.countSnapshots = message;
        }
      };
      this.runModuleTask({
        action: "count-snapshots",
        data: { name },
        completed: (output) => {
          this.loading.countSnapshots = false;
          if (!isCurrent()) {
            return;
          }
          this.verifiedName = name;
          if (output.count > 0) {
            // The admin reads the warning, then saves on purpose
            this.existingSnapshots = output;
          } else {
            this.addClient();
          }
        },
        validationFailed: (validationErrors) => {
          this.loading.countSnapshots = false;
          if (!isCurrent()) {
            return;
          }
          for (const e of validationErrors) {
            this.error[e.parameter] = "clients." + e.error;
          }
          this.focusElement(validationErrors[0].parameter);
        },
        aborted: fail,
        failed: fail,
      });
    },
    addClient() {
      this.loading.addClient = true;
      this.error.addClient = "";
      const fail = (message) => {
        this.error.addClient = message;
        this.loading.addClient = false;
      };
      this.runModuleTask({
        action: "add-client",
        data: {
          username: this.newUsername,
          hostname: this.newHostname,
          owner_email: this.newOwnerEmail,
        },
        title: this.$t("clients.adding_machine"),
        // The output holds the machine password: keep it out of the notification list
        isNotificationHidden: true,
        completed: (output) => {
          this.loading.addClient = false;
          this.isShownAddModal = false;
          this.listClients();
          this.showEnrollment({ name: output.name }, output);
        },
        validationFailed: (validationErrors) => {
          this.loading.addClient = false;
          for (const e of validationErrors) {
            this.error[e.parameter] = "clients." + e.error;
          }
          this.focusElement(validationErrors[0].parameter);
        },
        aborted: fail,
        failed: fail,
      });
    },
    showEnrollment(client, output = null) {
      this.enrollment = null;
      this.enrollmentName = client.name;
      this.error.getEnrollment = "";
      if (output) {
        // add-client and reset-client-password are the only actions that return the password
        this.enrollment = output;
        this.loading.getEnrollment = false;
        this.isShownEnrollmentModal = true;
        return;
      }
      this.loading.getEnrollment = true;
      this.isShownEnrollmentModal = true;
      const fail = (message) => {
        this.error.getEnrollment = message;
        this.loading.getEnrollment = false;
      };
      this.runModuleTask({
        action: "get-client-enrollment",
        data: { name: client.name },
        completed: (output) => {
          this.enrollment = output;
          this.loading.getEnrollment = false;
        },
        aborted: fail,
        failed: fail,
      });
    },
    hideEnrollmentModal() {
      // The scripts hold the machine password: do not keep them in memory
      this.isShownEnrollmentModal = false;
      this.enrollment = null;
    },
    resetFromEnrollment() {
      const name = this.enrollmentName;
      this.hideEnrollmentModal();
      this.showResetModal(
        this.clients.find((c) => c.name === name) || { name }
      );
    },
    showResetModal(client) {
      this.clientToReset = client;
      this.error.resetClient = "";
      this.isShownResetModal = true;
    },
    hideResetModal() {
      this.isShownResetModal = false;
      this.clientToReset = null;
    },
    resetClient() {
      const client = this.clientToReset;
      this.loading.resetClient = true;
      this.error.resetClient = "";
      const fail = (message) => {
        this.error.resetClient = message;
        this.loading.resetClient = false;
      };
      this.runModuleTask({
        action: "reset-client-password",
        data: { name: client.name },
        title: this.$t("clients.resetting_password", { name: client.name }),
        // The output holds the machine password: keep it out of the notification list
        isNotificationHidden: true,
        completed: (output) => {
          this.loading.resetClient = false;
          this.hideResetModal();
          this.showEnrollment(client, output);
        },
        aborted: fail,
        failed: fail,
      });
    },
    showFoldersModal(client) {
      this.foldersClient = client.name;
      this.folders = [];
      this.newFolder = "";
      this.error.newFolder = "";
      this.isShownFoldersModal = true;
      this.listFolders();
    },
    listFolders() {
      const name = this.foldersClient;
      this.loading.listFolders = true;
      this.error.listFolders = "";
      const fail = (message) => {
        this.error.listFolders = message;
        this.loading.listFolders = false;
      };
      this.runModuleTask({
        action: "list-client-folders",
        data: { name },
        completed: (output) => {
          // The modal may show another machine by now
          if (name === this.foldersClient) {
            this.folders = output.folders;
          }
          this.loading.listFolders = false;
        },
        aborted: fail,
        failed: fail,
      });
    },
    // The Policies form of the Kopia web UI rejects user@host:/path (kopia/kopia#5815),
    // its editor accepts the target in the URL
    openFolderPolicy(path) {
      const [userName, host] = this.foldersClient.split("@");
      const query = new URLSearchParams({ userName, host, path });
      window.open(
        `https://${this.host}/policies/edit?${query}`,
        "_blank",
        "noopener"
      );
    },
    addFolder() {
      this.error.newFolder = "";
      if (!FOLDER_PATTERNS.some((p) => p.test(this.newFolder))) {
        this.error.newFolder = "clients.folder_invalid";
        this.focusElement("newFolder");
        return;
      }
      this.openFolderPolicy(this.newFolder);
    },
    showRemoveModal(client) {
      this.clientToRemove = client;
      this.deleteSnapshots = false;
      this.error.removeClient = "";
      this.isShownRemoveModal = true;
    },
    hideRemoveModal() {
      this.isShownRemoveModal = false;
      this.clientToRemove = null;
    },
    removeClient() {
      const client = this.clientToRemove;
      this.loading.removeClient = true;
      this.error.removeClient = "";
      const fail = (message) => {
        this.error.removeClient = message;
        this.loading.removeClient = false;
        this.hideRemoveModal();
      };
      this.runModuleTask({
        action: "remove-client",
        data: { name: client.name, delete_snapshots: this.deleteSnapshots },
        title: this.$t("clients.removing_machine", { name: client.name }),
        isNotificationHidden: false,
        completed: () => {
          this.loading.removeClient = false;
          this.hideRemoveModal();
          this.listClients();
        },
        aborted: fail,
        failed: fail,
      });
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.mg-bottom {
  margin-bottom: $spacing-05;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-03;
}

.folder-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: $spacing-03 $spacing-05;
}

.folder-path {
  flex: 1 1 14rem;
  font-family: monospace;
  overflow-wrap: anywhere;
}

.folders-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-03;
}

.folders-label {
  font-weight: 600;
}

.add-folder {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: $spacing-03 $spacing-05;
}

.add-folder-input {
  flex: 1 1 18rem;
}

// Line the button up with the input, below the label
.add-folder-button {
  margin-top: 1.5rem;
}

.folder-date {
  font-size: 0.75rem;
  color: $text-02;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-05;
  margin-bottom: $spacing-05;
}

.break-word {
  word-wrap: break-word;
  overflow-wrap: anywhere;
}

.absolute-date {
  font-size: 0.75rem;
  color: $text-02;
}

.tag-late {
  background-color: #f1c21b;
  color: #161616;
}

.enrollment-facts {
  display: flex;
  flex-direction: column;
  gap: $spacing-03;
}

.fact-label {
  display: inline-block;
  min-width: 8rem;
  font-weight: 600;
}
</style>
