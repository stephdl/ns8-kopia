<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("settings.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getConfiguration">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-configuration')"
          :description="error.getConfiguration"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="routeMissing && !loading.getConfiguration">
      <cv-column>
        <NsInlineNotification
          kind="warning"
          :title="$t('settings.route_missing_title')"
          :description="$t('settings.route_missing_description')"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <cv-form @submit.prevent="configureModule">
            <NsInlineNotification
              v-if="!isConfigured && !loading.getConfiguration"
              kind="info"
              :title="$t('settings.host_choose_title')"
              :description="$t('settings.host_choose_description')"
              :showCloseButton="false"
              class="maxwidth"
            />
            <NsTextInput
              :label="$t('settings.host')"
              placeholder="kopia.example.org"
              v-model.trim="host"
              class="mg-bottom maxwidth"
              :helper-text="hostHelperText"
              :invalid-message="$t(error.host)"
              :disabled="stillLoading || isLocked"
              ref="host"
            />
            <NsToggle
              value="letsEncrypt"
              :label="core.$t('apps_lets_encrypt.request_https_certificate')"
              v-model="isLetsEncryptEnabled"
              :disabled="stillLoading"
              class="mg-bottom"
            >
              <template #tooltip>
                <div class="mg-bottom-sm">
                  {{ core.$t("apps_lets_encrypt.lets_encrypt_tips") }}
                </div>
                <div class="mg-bottom-sm">
                  {{ $t("settings.lets_encrypt_admin_only") }}
                </div>
                <div class="mg-bottom-sm">
                  <cv-link @click="goToCertificates">
                    {{ core.$t("apps_lets_encrypt.go_to_tls_certificates") }}
                  </cv-link>
                </div>
              </template>
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <NsTextInput
              type="number"
              min="1024"
              max="65535"
              v-model.number="clientPort"
              :label="$t('settings.client_port')"
              :helper-text="clientPortHelperText"
              :invalid-message="$t(error.client_port)"
              :disabled="stillLoading || isLocked"
              class="mg-bottom maxwidth"
              ref="client_port"
            />
            <NsTextInput
              value="admin"
              :label="$t('settings.admin_user')"
              :helper-text="$t('settings.admin_user_helper')"
              disabled
              class="mg-bottom maxwidth"
            />
            <NsToggle
              v-if="adminPasswordSet"
              key="changeAdminPassword"
              value="changeAdminPassword"
              :label="$t('settings.change_admin_password')"
              v-model="isChangeAdminPassword"
              :disabled="stillLoading"
              class="mg-bottom"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <NsPasswordInput
              v-if="isAdminPasswordActive"
              key="adminPassword"
              :newPasswordLabel="$t('settings.admin_password')"
              :confirmPasswordLabel="$t('settings.admin_password_confirm')"
              v-model="adminPassword"
              @passwordValidation="onAdminPasswordValidation"
              :newPasswordInvalidMessage="$t(error.admin_password)"
              :confirmPasswordInvalidMessage="$t(error.admin_password_confirm)"
              :passwordHideLabel="core.$t('password.hide_password')"
              :passwordShowLabel="core.$t('password.show_password')"
              :lengthLabel="core.$t('password.long_enough')"
              :lowercaseLabel="core.$t('password.lowercase_letter')"
              :uppercaseLabel="core.$t('password.uppercase_letter')"
              :numberLabel="core.$t('password.number')"
              :symbolLabel="core.$t('password.symbol')"
              :equalLabel="core.$t('password.equal')"
              :focus="focusAdminPassword"
              :minLength="12"
              :disabled="stillLoading"
              class="mg-bottom maxwidth"
            />
            <!-- repository password -->
            <h6 class="mg-bottom">{{ $t("settings.repository_title") }}</h6>
            <div v-if="!loading.getConfiguration" class="maxwidth">
              <template v-if="!repositoryPasswordSet">
                <NsInlineNotification
                  kind="warning"
                  :title="$t('settings.repository_password_warning_title')"
                  :description="$t('settings.repository_password_warning')"
                  :showCloseButton="false"
                />
                <RepositoryPasswordInput
                  v-model="repositoryPassword"
                  :acknowledged="repositoryPasswordWritten"
                  :error="error.repository_password"
                  :confirmError="error.repository_password_confirm"
                  :focus="focusRepositoryPassword"
                  :disabled="stillLoading"
                  @validation="repositoryPasswordValidation = $event"
                  @acknowledge="repositoryPasswordWritten = $event"
                />
              </template>
              <template v-else>
                <NsInlineNotification
                  kind="warning"
                  :title="$t('settings.repository_password_warning_title')"
                  :description="$t('settings.repository_password_warning')"
                  :showCloseButton="false"
                />
                <div class="button-row mg-bottom">
                  <NsButton
                    type="button"
                    kind="tertiary"
                    :icon="View20"
                    :disabled="stillLoading"
                    @click="isShownShowPasswordModal = true"
                    >{{ $t("settings.show_repository_password") }}</NsButton
                  >
                  <NsButton
                    type="button"
                    kind="danger--tertiary"
                    :icon="Password20"
                    :disabled="stillLoading"
                    @click="isShownChangePasswordModal = true"
                    >{{ $t("settings.change_repository_password") }}</NsButton
                  >
                </div>
              </template>
            </div>
            <cv-skeleton-text v-else :paragraph="true" :line-count="3" />
            <cv-row v-if="error.configureModule">
              <cv-column>
                <NsInlineNotification
                  kind="error"
                  :title="$t('action.configure-module')"
                  :description="error.configureModule"
                  :showCloseButton="false"
                />
              </cv-column>
            </cv-row>
            <NsInlineNotification
              v-if="missingFields.length && !stillLoading"
              kind="info"
              :title="$t('settings.to_save')"
              :description="missingFields.join(', ')"
              :showCloseButton="false"
              class="mg-bottom maxwidth"
            />
            <NsButton
              kind="primary"
              :icon="Save20"
              :loading="loading.configureModule"
              :disabled="stillLoading || !isFormValid"
              >{{ $t("settings.save") }}</NsButton
            >
          </cv-form>
        </cv-tile>
      </cv-column>
    </cv-row>
    <ShowRepositoryPasswordModal
      :visible="isShownShowPasswordModal"
      @hide="isShownShowPasswordModal = false"
    />
    <ChangeRepositoryPasswordModal
      :visible="isShownChangePasswordModal"
      @hide="isShownChangePasswordModal = false"
      @changed="onRepositoryPasswordChanged"
    />
  </cv-grid>
</template>

<script>
import { mapState } from "vuex";
// Not in IconService.
import View20 from "@carbon/icons-vue/es/view/20";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";
import ModuleTask from "@/mixins/moduleTask";
import { passwordError } from "@/lib/password";
import RepositoryPasswordInput from "@/components/RepositoryPasswordInput.vue";
import ShowRepositoryPasswordModal from "@/components/ShowRepositoryPasswordModal.vue";
import ChangeRepositoryPasswordModal from "@/components/ChangeRepositoryPasswordModal.vue";

export default {
  name: "Settings",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
    ModuleTask,
  ],
  components: {
    RepositoryPasswordInput,
    ShowRepositoryPasswordModal,
    ChangeRepositoryPasswordModal,
  },
  pageTitle() {
    return this.$t("settings.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "settings",
      },
      urlCheckInterval: null,
      View20,
      firstError: "",
      host: "",
      configuredHost: "",
      isLetsEncryptEnabled: false,
      clientPort: 0,
      clientsCount: 0,
      routeMissing: false,
      adminPasswordSet: false,
      adminPassword: "",
      adminPasswordValidation: null,
      focusAdminPassword: { element: "" },
      isChangeAdminPassword: false,
      repositoryPasswordSet: false,
      repositoryPassword: "",
      repositoryPasswordValidation: null,
      repositoryPasswordWritten: false,
      focusRepositoryPassword: { element: "" },
      isShownShowPasswordModal: false,
      isShownChangePasswordModal: false,
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        host: "",
        client_port: "",
        admin_password: "",
        admin_password_confirm: "",
        repository_password: "",
        repository_password_confirm: "",
      },
    };
  },
  watch: {
    adminPassword() {
      this.error.admin_password = "";
      this.error.admin_password_confirm = "";
    },
    repositoryPassword() {
      this.error.repository_password = "";
      this.error.repository_password_confirm = "";
    },
    isChangeAdminPassword() {
      this.adminPassword = "";
      this.error.admin_password = "";
      this.error.admin_password_confirm = "";
    },
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    stillLoading() {
      return this.loading.getConfiguration || this.loading.configureModule;
    },
    isConfigured() {
      return this.configuredHost !== "";
    },
    // The host and the port are in the URL of every enrolled machine
    isLocked() {
      return this.isConfigured && this.clientsCount > 0;
    },
    hostHelperText() {
      return this.isLocked ? this.$t("settings.host_locked_helper") : "";
    },
    clientPortHelperText() {
      return this.isLocked
        ? this.$t("settings.host_locked_helper")
        : this.$t("settings.client_port_helper");
    },
    isAdminPasswordActive() {
      // Wait for the configuration: before it loads, every module looks unconfigured
      if (this.loading.getConfiguration) {
        return false;
      }
      return !this.adminPasswordSet || this.isChangeAdminPassword;
    },
    isRepositoryPasswordRequired() {
      return !this.loading.getConfiguration && !this.repositoryPasswordSet;
    },
    missingFields() {
      const missing = [];
      if (!this.host || !this.host.includes(".")) {
        missing.push(this.$t("settings.host"));
      }
      if (!this.isPort(this.clientPort)) {
        missing.push(this.$t("settings.client_port"));
      }
      if (this.isAdminPasswordActive && !this.adminPassword) {
        missing.push(this.$t("settings.admin_password"));
      }
      if (this.isRepositoryPasswordRequired) {
        if (!this.repositoryPassword) {
          missing.push(this.$t("settings.repository_password"));
        } else if (!this.repositoryPasswordWritten) {
          missing.push(this.$t("settings.repository_password_written_down"));
        }
      }
      return missing;
    },
    isFormValid() {
      return this.missingFields.length === 0;
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
    isPort(value) {
      return Number.isInteger(value) && value >= 1024 && value <= 65535;
    },
    onAdminPasswordValidation(validation) {
      this.adminPasswordValidation = validation;
    },
    goToCertificates() {
      this.core.$router.push("/settings/tls-certificates");
    },
    onRepositoryPasswordChanged() {
      this.isShownChangePasswordModal = false;
      this.getConfiguration();
    },
    getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      this.runModuleTask({
        action: "get-configuration",
        completed: this.getConfigurationCompleted,
        aborted: (message) => {
          this.error.getConfiguration = message;
          this.loading.getConfiguration = false;
        },
        failed: (message) => {
          this.error.getConfiguration = message;
          this.loading.getConfiguration = false;
        },
      });
    },
    getConfigurationCompleted(config) {
      this.host = config.host;
      this.configuredHost = config.host;
      this.isLetsEncryptEnabled = config.lets_encrypt;
      this.clientPort = config.client_port;
      this.clientsCount = config.clients_count;
      this.routeMissing = config.route_missing;
      this.adminPasswordSet = config.admin_password_set;
      this.repositoryPasswordSet = config.repository_password_set;
      this.loading.getConfiguration = false;
      this.focusElement("host");
    },
    validateConfigureModule() {
      this.clearErrors(this);
      this.firstError = "";
      if (!this.host || !this.host.includes(".")) {
        this.fail("host", "common.required");
      }
      if (!this.isPort(this.clientPort)) {
        this.fail("client_port", "settings.client_port_range");
      }
      if (this.isAdminPasswordActive) {
        const v = this.adminPasswordValidation;
        const error = passwordError(this.adminPassword);
        if (error) {
          this.error.admin_password = error;
          this.focusAdminPassword = { element: "newPassword" };
          this.firstError = this.firstError || "admin_password";
        } else if (!v || !v.isEqualOk) {
          this.error.admin_password_confirm = "settings.password_mismatch";
          this.focusAdminPassword = { element: "confirmPassword" };
          this.firstError = this.firstError || "admin_password";
        }
      }
      if (this.isRepositoryPasswordRequired) {
        const v = this.repositoryPasswordValidation;
        const error = passwordError(this.repositoryPassword);
        if (error) {
          this.error.repository_password = error;
          this.focusRepositoryPassword = { element: "newPassword" };
          this.firstError = this.firstError || "repository_password";
        } else if (!v || !v.isEqualOk) {
          this.error.repository_password_confirm = "settings.password_mismatch";
          this.focusRepositoryPassword = { element: "confirmPassword" };
          this.firstError = this.firstError || "repository_password";
        }
      }
      if (this.firstError && !this.firstError.endsWith("password")) {
        this.focusElement(this.firstError);
      }
      return !this.firstError;
    },
    configureModuleValidationFailed(validationErrors) {
      this.loading.configureModule = false;
      let focusAlreadySet = false;
      for (const validationError of validationErrors) {
        const param = validationError.parameter;
        // A key, translated by the template like the client side errors
        this.error[param] = "settings." + validationError.error;
        if (!focusAlreadySet) {
          if (param === "admin_password") {
            this.focusAdminPassword = { element: "newPassword" };
          } else if (param === "repository_password") {
            this.focusRepositoryPassword = { element: "newPassword" };
          } else {
            this.focusElement(param);
          }
          focusAlreadySet = true;
        }
      }
    },
    configureModule() {
      if (!this.validateConfigureModule()) {
        return;
      }
      this.loading.configureModule = true;
      this.error.configureModule = "";
      const data = {
        host: this.host,
        lets_encrypt: this.isLetsEncryptEnabled,
        client_port: this.clientPort,
      };
      // Without a new password the backend keeps the current one
      if (this.isAdminPasswordActive) {
        data.admin_password = this.adminPassword;
      }
      // Accepted only before the repository exists, a later change goes through its own action
      if (this.isRepositoryPasswordRequired) {
        data.repository_password = this.repositoryPassword;
      }
      this.runModuleTask({
        action: "configure-module",
        data,
        title: this.$t("settings.configuring"),
        description: this.$t("settings.instance_configuration", {
          instance: this.instanceName,
        }),
        isNotificationHidden: false,
        completed: this.configureModuleCompleted,
        validationFailed: this.configureModuleValidationFailed,
        aborted: (message) => {
          this.error.configureModule = message;
          this.loading.configureModule = false;
        },
        failed: (message) => {
          this.error.configureModule = message;
          this.loading.configureModule = false;
        },
      });
    },
    configureModuleCompleted() {
      this.loading.configureModule = false;
      this.adminPassword = "";
      this.isChangeAdminPassword = false;
      this.repositoryPassword = "";
      this.repositoryPasswordWritten = false;
      this.getConfiguration();
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.mg-bottom {
  margin-bottom: $spacing-06;
}

.maxwidth {
  max-width: 38rem;
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-05;
  margin-top: $spacing-05;
}
</style>
