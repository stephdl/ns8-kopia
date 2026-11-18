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
              :loading="isPageLoading"
              :disabled="isPageLoading || !configured"
              @click="showAddModal"
              >{{ $t("clients.add_machine") }}</NsButton
            >
            <NsButton
              kind="secondary"
              :icon="Restart20"
              :loading="isPageLoading"
              :disabled="isPageLoading || !configured"
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
                  <!-- A green OK next to an errors tag reads as a contradiction -->
                  <NsTag
                    v-if="!(row.state === 'ok' && row.error_count > 0)"
                    :label="$t('clients.state_' + row.state)"
                    :kind="stateKind(row.state)"
                    :class="{ 'tag-late': row.state === 'late' }"
                  />
                  <button
                    v-if="row.error_count > 0"
                    type="button"
                    class="errors-button"
                    :title="$t('clients.folder_show_errors')"
                    @click="showFoldersModal(row, true)"
                  >
                    <NsTag
                      kind="red"
                      :label="
                        $tc('clients.errors_count', row.error_count, {
                          count: row.error_count,
                        })
                      "
                    />
                  </button>
                </cv-data-table-cell>
                <cv-data-table-cell>
                  <!-- A desktop backs up nothing until the admin adds its folders: keep the way in sight -->
                  <NsButton
                    kind="ghost"
                    size="small"
                    :icon="Folder20"
                    @click="showFoldersModal(row)"
                    >{{ $t("clients.manage_folders") }}</NsButton
                  >
                </cv-data-table-cell>
                <cv-data-table-cell class="table-overflow-menu-cell">
                  <cv-overflow-menu flip-menu class="table-overflow-menu">
                    <cv-overflow-menu-item @click="showEnrollment(row)">
                      <NsMenuItem
                        :icon="Document20"
                        :label="$t('clients.show_enrollment')"
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
              $tc(
                'clients.existing_snapshots_description',
                existingSnapshots.count,
                {
                  count: existingSnapshots.count,
                  first: formatDateTime(existingSnapshots.first),
                  last: formatDateTime(existingSnapshots.last),
                }
              )
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
          <template v-if="enrollment.password">
            <!-- One warning for the three rules, so the script stays in view -->
            <NsInlineNotification
              kind="warning"
              :title="$t('clients.enrollment_once_title')"
              :showCloseButton="false"
              class="enrollment-warning"
            >
              <template slot="description">
                <ul class="warning-list">
                  <li>{{ $t("clients.enrollment_once_description") }}</li>
                  <li>
                    <strong>{{ $t("clients.enrollment_user_title") }}.</strong>
                    {{ $t("clients.enrollment_user_description") }}
                  </li>
                  <li>
                    <strong
                      >{{ $t("clients.enrollment_secret_title") }}.</strong
                    >
                    {{ $t("clients.enrollment_secret_description") }}
                  </li>
                </ul>
              </template>
            </NsInlineNotification>
            <NsInlineNotification
              kind="info"
              :description="$t('clients.enrollment_intro')"
              :showCloseButton="false"
              class="enrollment-info"
            />
            <NsTabs
              :container="false"
              :aria-label="$t('clients.script_tabs')"
              class="enrollment-tabs"
            >
              <cv-tab
                v-for="(tab, index) in scriptTabs"
                :key="tab.id"
                :id="tab.id"
                :label="$t(tab.label)"
                :selected="index === 0"
              >
                <!-- Folded to a few lines: the copy button still takes the whole script -->
                <NsCodeSnippet
                  :copyTooltip="$t('clients.copy')"
                  :copyFeedback="$t('clients.copied')"
                  :feedbackAriaLabel="$t('clients.copied')"
                  :moreText="$t('clients.show_script')"
                  :lessText="$t('clients.hide_script')"
                  :wrapText="true"
                  >{{ enrollment[tab.script] }}</NsCodeSnippet
                >
              </cv-tab>
            </NsTabs>
          </template>
          <NsInlineNotification
            v-else
            kind="info"
            :title="$t('clients.enrollment_hidden_title')"
            :description="$t('clients.enrollment_hidden_description')"
            :actionLabel="$t('clients.reset_password')"
            @action="resetFromEnrollment"
            :showCloseButton="false"
          />
          <p class="facts-caption">
            {{ $t("clients.enrollment_details_intro") }}
          </p>
          <dl class="enrollment-facts">
            <dt>{{ $t("clients.url") }}</dt>
            <dd>
              <code>{{ enrollment.url }}</code>
            </dd>
            <dt>{{ $t("clients.fingerprint") }}</dt>
            <dd>
              <code>{{ enrollment.fingerprint }}</code>
            </dd>
            <dt>{{ $t("clients.identity") }}</dt>
            <dd>
              <code>{{ enrollment.username }}@{{ enrollment.hostname }}</code>
            </dd>
          </dl>
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
      :size="folderErrors ? 'large' : 'default'"
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
        <!-- Outside the chain below: a failed action must not hide the folder list -->
        <NsInlineNotification
          v-if="error.folderAction"
          kind="error"
          :title="$t('action.' + error.folderAction.action)"
          :description="error.folderAction.message"
          :showCloseButton="false"
        />
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
        <!-- Confirmation in place: a second modal over this one would hide the folder list -->
        <div v-else-if="folderToRemove" class="folder-remove">
          <h6 class="mg-bottom-sm">
            {{ $t("clients.folder_remove_title", { path: folderToRemove }) }}
          </h6>
          <NsInlineNotification
            kind="warning"
            :description="$t('clients.folder_remove_description')"
            :showCloseButton="false"
          />
          <NsInlineNotification
            v-if="error.removeFolder"
            kind="error"
            :title="$t('action.remove-client-folder')"
            :description="error.removeFolder"
            :showCloseButton="false"
          />
          <div class="folder-remove-buttons">
            <NsButton
              kind="secondary"
              size="field"
              :disabled="loading.removeFolder"
              @click="cancelRemoveFolder"
              >{{ core.$t("common.cancel") }}</NsButton
            >
            <NsButton
              kind="danger"
              size="field"
              :icon="TrashCan20"
              :loading="loading.removeFolder"
              :disabled="loading.removeFolder"
              @click="removeFolder"
              >{{ $t("clients.folder_remove") }}</NsButton
            >
          </div>
        </div>
        <div v-else-if="folderErrors" class="folder-errors">
          <h6 class="mg-bottom-sm">
            {{ $t("clients.folder_errors_title", { path: folderErrors.path }) }}
          </h6>
          <p class="mg-bottom-sm">
            {{ $t("clients.folder_errors_description") }}
          </p>
          <p
            v-if="
              folderErrors.errors.length <
              folderErrors.error_count + folderErrors.ignored_count
            "
            class="mg-bottom-sm"
          >
            {{
              $t("clients.folder_errors_partial", {
                shown: folderErrors.errors.length,
                count: folderErrors.error_count + folderErrors.ignored_count,
              })
            }}
          </p>
          <!-- Kopia mixes the errors a policy ignores into the same list, with nothing to tell them apart -->
          <p v-if="folderErrors.ignored_count > 0" class="mg-bottom-sm">
            {{
              $tc("clients.folder_errors_ignored", folderErrors.ignored_count, {
                count: folderErrors.ignored_count,
              })
            }}
          </p>
          <NsDataTable
            class="mg-bottom"
            :allRows="folderErrors.errors"
            :columns="[
              $t('clients.col_error_path'),
              $t('clients.col_error_reason'),
            ]"
            :rawColumns="['path', 'error']"
            :sortable="true"
            :pageSizes="[10, 25, 50, 100]"
            isSearchable
            :searchPlaceholder="$t('clients.search_errors')"
            :searchClearLabel="core.$t('common.clear_search')"
            :noSearchResultsLabel="core.$t('common.no_search_results')"
            :noSearchResultsDescription="
              core.$t('common.no_search_results_description')
            "
            :isLoading="false"
            :itemsPerPageLabel="core.$t('pagination.items_per_page')"
            :rangeOfTotalItemsLabel="core.$t('pagination.range_of_total_items')"
            :ofTotalPagesLabel="core.$t('pagination.of_total_pages')"
            :backwardText="core.$t('pagination.previous_page')"
            :forwardText="core.$t('pagination.next_page')"
            :pageNumberLabel="core.$t('pagination.page_number')"
            @updatePage="errorsPage = $event"
          >
            <template slot="data">
              <cv-data-table-row
                v-for="(row, rowIndex) in errorsPage"
                :key="`${rowIndex}`"
                :value="`${rowIndex}`"
              >
                <cv-data-table-cell class="break-word error-path">{{
                  row.path || "/"
                }}</cv-data-table-cell>
                <cv-data-table-cell class="break-word">{{
                  row.error
                }}</cv-data-table-cell>
              </cv-data-table-row>
            </template>
          </NsDataTable>
          <NsButton
            kind="secondary"
            size="field"
            :icon="ArrowLeft20"
            @click="folderErrors = null"
            >{{ $t("clients.folder_errors_back") }}</NsButton
          >
        </div>
        <template v-else>
          <p v-if="!folders.length" class="mg-bottom">
            {{ $t("clients.no_folders") }}
          </p>
          <ul v-else class="folder-list mg-bottom">
            <li v-for="folder in folders" :key="folder.path" class="folder-row">
              <div class="folder-main">
                <div class="folder-path">{{ folder.path }}</div>
                <div class="folder-meta">
                  <NsTag
                    v-if="folder.disabled"
                    size="sm"
                    kind="gray"
                    :label="$t('clients.folder_disabled')"
                  />
                  <!-- Gray: a disabled folder does not count for the machine state nor the mails -->
                  <NsTag
                    v-if="folder.error_count > 0"
                    size="sm"
                    :kind="folder.disabled ? 'gray' : 'red'"
                    :label="
                      $tc('clients.errors_count', folder.error_count, {
                        count: folder.error_count,
                      })
                    "
                  />
                  <span>{{
                    folder.last_backup
                      ? formatDateTime(folder.last_backup)
                      : $t("clients.folder_never")
                  }}</span>
                </div>
              </div>
              <cv-inline-loading
                v-if="busyFolder === foldersClient + ':' + folder.path"
                state="loading"
                :loading-text="
                  folder.disabled
                    ? $t('clients.folder_enable')
                    : $t('clients.folder_disable')
                "
              />
              <!-- Same menu as the machine rows: the list stays readable with long paths -->
              <cv-overflow-menu
                v-else
                flip-menu
                class="folder-menu"
                :label="$t('clients.folder_actions')"
              >
                <cv-overflow-menu-item
                  v-if="folder.error_count > 0"
                  @click="folderErrors = folder"
                >
                  <NsMenuItem
                    :icon="WarningAlt20"
                    :label="$t('clients.folder_show_errors')"
                  />
                </cv-overflow-menu-item>
                <cv-overflow-menu-item @click="openFolderPolicy(folder.path)">
                  <NsMenuItem
                    :icon="Launch20"
                    :label="$t('clients.folder_open')"
                  />
                </cv-overflow-menu-item>
                <cv-overflow-menu-item
                  v-if="folder.disabled"
                  :disabled="!!busyFolder"
                  @click="setFolderEnabled(folder, true)"
                >
                  <NsMenuItem
                    :icon="Play20"
                    :label="$t('clients.folder_enable')"
                  />
                </cv-overflow-menu-item>
                <cv-overflow-menu-item
                  v-else
                  :disabled="!!busyFolder"
                  @click="setFolderEnabled(folder, false)"
                >
                  <NsMenuItem
                    :icon="Pause20"
                    :label="$t('clients.folder_disable')"
                  />
                </cv-overflow-menu-item>
                <NsMenuDivider />
                <cv-overflow-menu-item
                  danger
                  :disabled="!!busyFolder"
                  @click="askRemoveFolder(folder)"
                >
                  <NsMenuItem
                    :icon="TrashCan20"
                    :label="$t('clients.folder_remove')"
                  />
                </cv-overflow-menu-item>
              </cv-overflow-menu>
            </li>
          </ul>
        </template>
        <cv-form
          v-if="!folderToRemove && !folderErrors"
          @submit.prevent="addFolder"
          class="add-folder"
        >
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
            :icon="Add20"
            type="submit"
            :loading="loading.addFolder"
            :disabled="loading.addFolder"
            class="add-folder-button"
            >{{ $t("clients.folder_add") }}</NsButton
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
import { createSealKey, openSealed } from "@/lib/seal";
import Play20 from "@carbon/icons-vue/es/play/20";
import Pause20 from "@carbon/icons-vue/es/pause/20";
import WarningAlt20 from "@carbon/icons-vue/es/warning--alt/20";
import ArrowLeft20 from "@carbon/icons-vue/es/arrow--left/20";

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
      // Not in the icon service of ns8-ui-lib
      Play20,
      Pause20,
      WarningAlt20,
      ArrowLeft20,
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
      tableColumns: ["name", "owner_email", "last_backup", "state", "folders"],
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
      folderToRemove: "",
      // Folder whose read errors replace the list in the window
      folderErrors: null,
      errorsPage: [],
      openErrorsOnLoad: false,
      busyFolder: "",
      folders: [],
      newFolder: "",
      host: "",
      loading: {
        removeFolder: false,
        addFolder: false,
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
        removeFolder: "",
        folderAction: null,
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
    // The configuration loads first, then the machines: one state for both, so the two buttons
    // spin together instead of one after the other
    isPageLoading() {
      return this.loading.getConfiguration || this.loading.listClients;
    },
    i18nTableColumns() {
      return this.tableColumns.map((column) =>
        this.$t("clients.col_" + column)
      );
    },
  },
  created() {
    // One key pair for the page, ready before any click. Without WebCrypto (page not served
    // over HTTPS) it is null and the actions answer in plain text.
    this.sealKey = createSealKey().catch(() => null);
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
    async addClient() {
      this.loading.addClient = true;
      this.error.addClient = "";
      const fail = (message) => {
        this.error.addClient = message;
        this.loading.addClient = false;
      };
      // Read before the await: these are the values the snapshot check verified
      const data = {
        username: this.newUsername,
        hostname: this.newHostname,
        owner_email: this.newOwnerEmail,
      };
      const seal = await this.sealKey;
      if (seal) {
        data.public_key = seal.publicKey;
      }
      this.runModuleTask({
        action: "add-client",
        data,
        title: this.$t("clients.adding_machine"),
        // The output holds the machine password: keep it out of the notification list
        isNotificationHidden: true,
        completed: async (sealed) => {
          // The machine exists whatever happens to its script
          this.listClients();
          let output;
          try {
            output = await openSealed(sealed, seal);
          } catch (e) {
            console.error("cannot read the add-client output", e);
            fail(this.$t("error.generic_error"));
            return;
          }
          this.loading.addClient = false;
          this.isShownAddModal = false;
          this.showEnrollment({ name: output.name }, output);
        },
        validationFailed: (validationErrors) => {
          const fields = validationErrors.filter(
            (e) => e.parameter in this.error
          );
          if (!fields.length) {
            // public_key has no input to show an error on
            fail(this.$t("error.generic_error"));
            return;
          }
          this.loading.addClient = false;
          for (const e of fields) {
            this.error[e.parameter] = "clients." + e.error;
          }
          this.focusElement(fields[0].parameter);
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
    async resetClient() {
      const client = this.clientToReset;
      this.loading.resetClient = true;
      this.error.resetClient = "";
      const fail = (message) => {
        this.error.resetClient = message;
        this.loading.resetClient = false;
      };
      const data = { name: client.name };
      const seal = await this.sealKey;
      if (seal) {
        data.public_key = seal.publicKey;
      }
      this.runModuleTask({
        action: "reset-client-password",
        data,
        title: this.$t("clients.resetting_password", { name: client.name }),
        // The output holds the machine password: keep it out of the notification list
        isNotificationHidden: true,
        completed: async (sealed) => {
          let output;
          try {
            output = await openSealed(sealed, seal);
          } catch (e) {
            console.error("cannot read the reset-client-password output", e);
            fail(this.$t("error.generic_error"));
            return;
          }
          this.loading.resetClient = false;
          this.hideResetModal();
          this.showEnrollment(client, output);
        },
        validationFailed: () => fail(this.$t("error.generic_error")),
        aborted: fail,
        failed: fail,
      });
    },
    showFoldersModal(client, openErrors = false) {
      this.openErrorsOnLoad = openErrors;
      this.foldersClient = client.name;
      this.folderToRemove = "";
      this.folderErrors = null;
      this.error.folderAction = null;
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
            // From the errors tag: go straight to the errors when only one folder has some
            const failing = this.folders.filter(
              (f) => f.error_count > 0 && !f.disabled
            );
            if (this.openErrorsOnLoad && failing.length === 1) {
              this.folderErrors = failing[0];
            }
            this.openErrorsOnLoad = false;
          }
          this.loading.listFolders = false;
        },
        aborted: fail,
        failed: fail,
      });
    },
    // Disable keeps the snapshots and is undone with Enable: no confirmation needed
    setFolderEnabled(folder, enabled) {
      const name = this.foldersClient;
      const action = enabled ? "enable-client-folder" : "disable-client-folder";
      this.busyFolder = name + ":" + folder.path;
      this.error.folderAction = null;
      const done = (message) => {
        this.busyFolder = "";
        // The window may show another machine by now
        if (name !== this.foldersClient) {
          return;
        }
        if (message) {
          this.error.folderAction = { action, message };
        }
        this.listFolders();
      };
      this.runModuleTask({
        action,
        data: { name, path: folder.path },
        title: this.$t(
          enabled ? "clients.enabling_folder" : "clients.disabling_folder",
          { path: folder.path }
        ),
        completed: () => done(""),
        validationFailed: () => done(this.$t("clients.folder_not_found")),
        aborted: done,
        failed: done,
      });
    },
    askRemoveFolder(folder) {
      this.error.removeFolder = "";
      this.folderToRemove = folder.path;
    },
    cancelRemoveFolder() {
      this.folderToRemove = "";
      this.error.removeFolder = "";
    },
    removeFolder() {
      const name = this.foldersClient;
      this.loading.removeFolder = true;
      this.error.removeFolder = "";
      const fail = (message) => {
        this.loading.removeFolder = false;
        if (name === this.foldersClient) {
          this.error.removeFolder = message;
        }
      };
      this.runModuleTask({
        action: "remove-client-folder",
        data: {
          name,
          path: this.folderToRemove,
        },
        title: this.$t("clients.removing_folder", {
          path: this.folderToRemove,
        }),
        completed: () => {
          this.loading.removeFolder = false;
          if (name === this.foldersClient) {
            this.folderToRemove = "";
            this.listFolders();
          }
        },
        validationFailed: () => fail(this.$t("clients.folder_not_found")),
        aborted: fail,
        failed: fail,
      });
    },
    // The Policies form of the Kopia web UI rejects user@host:/path (kopia/kopia#5815),
    // its editor accepts the target in the URL. folder-policy.html sends the new tab there.
    openFolderPolicy(path) {
      const [userName, host] = this.foldersClient.split("@");
      const page = new URL("folder-policy.html", window.location.href);
      page.hash = "";
      page.search = new URLSearchParams({ userName, host, path });
      try {
        localStorage.setItem(`kopia-host:${page.pathname}`, this.host);
      } catch (e) {
        // Without storage the page asks to open the link from here
      }
      window.open(page, "_blank", "noopener");
    },
    addFolder() {
      this.error.newFolder = "";
      if (!FOLDER_PATTERNS.some((p) => p.test(this.newFolder))) {
        this.error.newFolder = "clients.folder_invalid";
        this.focusElement("newFolder");
        return;
      }
      const name = this.foldersClient;
      const path = this.newFolder;
      this.loading.addFolder = true;
      this.error.folderAction = null;
      const fail = (message) => {
        this.loading.addFolder = false;
        if (name === this.foldersClient) {
          this.error.folderAction = { action: "add-client-folder", message };
        }
      };
      this.runModuleTask({
        action: "add-client-folder",
        data: { name, path },
        title: this.$t("clients.adding_folder", { path }),
        completed: () => {
          this.loading.addFolder = false;
          if (name === this.foldersClient) {
            this.newFolder = "";
            this.listFolders();
          }
        },
        validationFailed: (errors) => {
          this.loading.addFolder = false;
          if (name !== this.foldersClient) {
            return;
          }
          // Only folder_exists has a string: schema errors mean the path is not valid
          this.error.newFolder =
            errors[0].error === "folder_exists"
              ? "clients.folder_exists"
              : "clients.folder_invalid";
          this.focusElement("newFolder");
        },
        aborted: fail,
        failed: fail,
      });
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

// One grid for the whole list, so dates and actions line up from one folder to the next
.folder-list {
  border-top: 1px solid $ui-03;
  // The hidden tooltip of each menu sits right of its button and made the window scroll sideways
  overflow-x: hidden;
}

.folder-row {
  display: flex;
  align-items: center;
  gap: $spacing-05;
  padding: $spacing-04 0;
  border-bottom: 1px solid $ui-03;
}

// The table menu style is absolute for table cells: in this list the menu sits in the row
.folder-menu {
  position: relative;
  flex: 0 0 auto;
}

.folder-main {
  flex: 1 1 auto;
  min-width: 0;
}

.folder-path {
  font-family: monospace;
  overflow-wrap: anywhere;
}

.folder-meta {
  display: flex;
  align-items: center;
  gap: $spacing-03;
  margin-top: $spacing-02;
  font-size: 0.75rem;
  color: $text-02;
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

.errors-button {
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
}

.error-path {
  font-family: monospace;
}

.folder-remove {
  padding: $spacing-05;
  border: 1px solid $ui-03;
  margin-bottom: $spacing-05;
}

.folder-remove-buttons {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-03;
  margin-top: $spacing-05;
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

// Title above the list, not beside it as Carbon does for a short description
.enrollment-warning ::v-deep .bx--inline-notification__subtitle {
  flex-basis: 100%;
}

// Carbon caps notifications, tabs and snippets at different widths: line them up with the details
.enrollment-warning,
.enrollment-info,
.enrollment-tabs ::v-deep .bx--snippet {
  max-width: none;
}

.enrollment-tabs ::v-deep .bx--tabs__nav-item {
  max-width: none;
}

.warning-list {
  list-style: disc;
  padding-left: $spacing-05;

  li + li {
    margin-top: $spacing-02;
  }
}

.enrollment-tabs {
  margin-top: $spacing-05;
}

.facts-caption {
  margin-top: $spacing-06;
  margin-bottom: $spacing-03;
  font-size: 0.875rem;
  color: $text-02;
}

.enrollment-facts {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: $spacing-03 $spacing-06;
  padding: $spacing-05;
  border: 1px solid $ui-03;

  dt {
    font-weight: 600;
  }

  dd code {
    overflow-wrap: anywhere;
  }
}

// On a phone the value goes under its label
@media (max-width: 42rem) {
  .enrollment-facts {
    grid-template-columns: minmax(0, 1fr);
    row-gap: $spacing-02;

    dd {
      margin-bottom: $spacing-03;
    }
  }
}
</style>
