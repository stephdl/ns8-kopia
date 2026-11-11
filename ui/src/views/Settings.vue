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
            <!-- backup policy -->
            <cv-accordion ref="accordionPolicy" class="maxwidth mg-bottom">
              <cv-accordion-item>
                <template slot="title">{{
                  $t("settings.backup_policy")
                }}</template>
                <template slot="content">
                  <p class="mg-bottom">
                    {{ $t("settings.backup_policy_description") }}
                  </p>
                  <NsComboBox
                    v-model="snapshotInterval"
                    :options="intervalOptions"
                    auto-highlight
                    :title="$t('settings.snapshot_interval')"
                    :label="$t('settings.choose_snapshot_interval')"
                    :invalid-message="$t(error.snapshot_interval)"
                    :disabled="stillLoading"
                    class="mg-bottom"
                    ref="snapshot_interval"
                  />
                  <NsTextInput
                    v-for="field in keepFields"
                    :key="field"
                    type="number"
                    min="0"
                    :max="field === 'annual' ? 100 : 1000"
                    v-model.number="keep[field]"
                    :label="$t('settings.keep_' + field)"
                    :invalid-message="$t(error['keep_' + field])"
                    :disabled="stillLoading"
                    class="mg-bottom"
                  />
                  <NsComboBox
                    v-model="compression"
                    :options="compressionOptions"
                    auto-highlight
                    :title="$t('settings.compression')"
                    :label="$t('settings.choose_compression')"
                    :invalid-message="$t(error.compression)"
                    :disabled="stillLoading"
                    class="mg-bottom"
                    ref="compression"
                  />
                  <cv-text-area
                    v-model="excludesText"
                    :label="$t('settings.excludes')"
                    :helper-text="$t('settings.excludes_helper')"
                    :invalid-message="$t(error.excludes)"
                    :disabled="stillLoading"
                    placeholder="node_modules"
                    class="mg-bottom"
                    ref="excludes"
                  />
                </template>
              </cv-accordion-item>
            </cv-accordion>
            <!-- alerts -->
            <cv-accordion ref="accordionAlerts" class="maxwidth mg-bottom">
              <cv-accordion-item>
                <template slot="title">{{ $t("settings.alerts") }}</template>
                <template slot="content">
                  <NsInlineNotification
                    v-if="!smarthostEnabled"
                    kind="warning"
                    :title="$t('settings.smarthost_missing_title')"
                    :description="$t('settings.smarthost_missing_description')"
                    :actionLabel="$t('settings.go_to_smarthost')"
                    @action="goToSmarthost"
                    :showCloseButton="false"
                  />
                  <NsTextInput
                    type="number"
                    min="1"
                    max="8760"
                    v-model.number="ownerAlertHours"
                    :label="$t('settings.owner_alert_hours')"
                    :helper-text="$t('settings.owner_alert_hours_helper')"
                    :invalid-message="$t(error.owner_alert_hours)"
                    :disabled="stillLoading"
                    class="mg-bottom"
                    ref="owner_alert_hours"
                  />
                  <NsTextInput
                    type="number"
                    min="1"
                    max="8760"
                    v-model.number="adminAlertHours"
                    :label="$t('settings.admin_alert_hours')"
                    :helper-text="$t('settings.admin_alert_hours_helper')"
                    :invalid-message="$t(error.admin_alert_hours)"
                    :disabled="stillLoading"
                    class="mg-bottom"
                    ref="admin_alert_hours"
                  />
                  <cv-text-area
                    v-model="adminRecipientsText"
                    :label="$t('settings.admin_recipients')"
                    :helper-text="$t('settings.admin_recipients_helper')"
                    :invalid-message="$t(error.admin_recipients)"
                    :disabled="stillLoading"
                    placeholder="it@example.org"
                    class="mg-bottom"
                    ref="admin_recipients"
                  />
                  <NsTextInput
                    v-model.trim="alertSender"
                    :label="$t('settings.alert_sender')"
                    :placeholder="defaultSender || 'default_sender'"
                    :helper-text="$t('settings.alert_sender_helper')"
                    :invalid-message="$t(error.alert_sender)"
                    :disabled="stillLoading"
                    class="mg-bottom"
                    ref="alert_sender"
                  />
                  <NsComboBox
                    v-model="alertLanguage"
                    :options="languageOptions"
                    auto-highlight
                    :title="$t('settings.alert_language')"
                    :label="$t('settings.choose_alert_language')"
                    :invalid-message="$t(error.alert_language)"
                    :disabled="stillLoading"
                    class="mg-bottom"
                    ref="alert_language"
                  />
                  <NsTextInput
                    type="number"
                    min="50"
                    max="99"
                    v-model.number="diskAlertPercent"
                    :label="$t('settings.disk_alert_percent')"
                    :helper-text="$t('settings.disk_alert_percent_helper')"
                    :invalid-message="$t(error.disk_alert_percent)"
                    :disabled="stillLoading"
                    class="mg-bottom"
                    ref="disk_alert_percent"
                  />
                  <h6 class="mg-bottom">{{ $t("settings.test_mail") }}</h6>
                  <div class="test-mail-row">
                    <NsTextInput
                      v-model.trim="testRecipient"
                      type="email"
                      :label="$t('settings.test_mail_recipient')"
                      placeholder="it@example.org"
                      :invalid-message="$t(error.recipient)"
                      :disabled="stillLoading || !smarthostEnabled"
                      class="test-mail-field"
                      ref="recipient"
                    />
                    <NsButton
                      type="button"
                      kind="tertiary"
                      size="field"
                      :icon="Email20"
                      :loading="loading.sendTestMail"
                      :disabled="
                        stillLoading ||
                        !smarthostEnabled ||
                        loading.sendTestMail ||
                        !isEmail(testRecipient)
                      "
                      class="test-mail-button"
                      @click="sendTestMail"
                      >{{ $t("settings.send_test_mail") }}</NsButton
                    >
                  </div>
                  <NsInlineNotification
                    v-if="testMailSent"
                    kind="success"
                    :title="$t('settings.test_mail_sent')"
                    :description="
                      $t('settings.test_mail_sent_description', {
                        recipient: testMailSent,
                      })
                    "
                    :showCloseButton="false"
                  />
                  <NsInlineNotification
                    v-if="error.sendTestMail"
                    kind="error"
                    :title="$t('action.send-test-mail')"
                    :description="error.sendTestMail"
                    :showCloseButton="false"
                  />
                </template>
              </cv-accordion-item>
            </cv-accordion>
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

const INTERVALS = [0, 1, 2, 4, 6, 8, 12, 24];
const COMPRESSIONS = [
  "none",
  "zstd",
  "zstd-fastest",
  "zstd-better-compression",
  "s2-default",
  "pgzip",
];
// Language names stay in their own language, like in a language switcher
const LANGUAGES = {
  en: "English",
  fr: "Français",
  it: "Italiano",
  de: "Deutsch",
  es: "Español",
  pt: "Português",
  pt_BR: "Português (Brasil)",
  eu: "Euskara",
};
const KEEP_FIELDS = [
  "latest",
  "hourly",
  "daily",
  "weekly",
  "monthly",
  "annual",
];

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
      smarthostEnabled: true,
      defaultSender: "",
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
      // Empty until the configuration is loaded: NsComboBox writes its label only
      // when the value changes while the option already exists
      snapshotInterval: "",
      keepFields: KEEP_FIELDS,
      keep: {
        latest: 10,
        hourly: 48,
        daily: 14,
        weekly: 8,
        monthly: 12,
        annual: 2,
      },
      compression: "",
      excludesText: "",
      ownerAlertHours: 48,
      adminAlertHours: 96,
      adminRecipientsText: "",
      alertSender: "",
      alertLanguage: "",
      diskAlertPercent: 85,
      testRecipient: "",
      testMailSent: "",
      loading: {
        getConfiguration: false,
        configureModule: false,
        sendTestMail: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        sendTestMail: "",
        host: "",
        client_port: "",
        admin_password: "",
        admin_password_confirm: "",
        repository_password: "",
        repository_password_confirm: "",
        snapshot_interval: "",
        keep_latest: "",
        keep_hourly: "",
        keep_daily: "",
        keep_weekly: "",
        keep_monthly: "",
        keep_annual: "",
        compression: "",
        excludes: "",
        owner_alert_hours: "",
        admin_alert_hours: "",
        admin_recipients: "",
        alert_sender: "",
        alert_language: "",
        disk_alert_percent: "",
        recipient: "",
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
    testRecipient() {
      this.testMailSent = "";
      this.error.sendTestMail = "";
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
    intervalOptions() {
      return INTERVALS.map((hours) => ({
        name: "interval-" + hours,
        value: String(hours),
        label: hours
          ? this.$tc("settings.interval_hours", hours, { count: hours })
          : this.$t("settings.interval_manual"),
      }));
    },
    compressionOptions() {
      return COMPRESSIONS.map((name) => ({
        name,
        value: name,
        label: this.$t("settings.compression_" + name.replace(/-/g, "_")),
      }));
    },
    languageOptions() {
      return Object.keys(LANGUAGES).map((code) => ({
        name: code,
        value: code,
        label: LANGUAGES[code],
      }));
    },
    excludes() {
      return [
        ...new Set(
          this.excludesText
            .split("\n")
            .map((line) => line.trim())
            .filter((line) => line !== "")
        ),
      ];
    },
    adminRecipients() {
      return [
        ...new Set(
          this.adminRecipientsText.split(/[\s,;]+/).filter((r) => r !== "")
        ),
      ];
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
    isEmail(value) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    isPort(value) {
      return Number.isInteger(value) && value >= 1024 && value <= 65535;
    },
    isHours(value, max = 8760) {
      return Number.isInteger(value) && value >= 1 && value <= max;
    },
    isCount(value, max) {
      return Number.isInteger(value) && value >= 0 && value <= max;
    },
    onAdminPasswordValidation(validation) {
      this.adminPasswordValidation = validation;
    },
    goToSmarthost() {
      this.core.$router.push("/settings/smarthost");
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
      this.smarthostEnabled = config.smarthost_enabled;
      this.defaultSender = config.default_sender || "";
      this.adminPasswordSet = config.admin_password_set;
      this.repositoryPasswordSet = config.repository_password_set;
      this.snapshotInterval = String(config.snapshot_interval);
      for (const field of KEEP_FIELDS) {
        this.keep[field] = config["keep_" + field];
      }
      this.compression = config.compression;
      this.excludesText = (config.excludes || []).join("\n");
      this.ownerAlertHours = config.owner_alert_hours;
      this.adminAlertHours = config.admin_alert_hours;
      this.adminRecipientsText = (config.admin_recipients || []).join("\n");
      this.alertSender = config.alert_sender || "";
      this.alertLanguage = config.alert_language;
      this.diskAlertPercent = config.disk_alert_percent;
      this.loading.getConfiguration = false;
      this.focusElement("host");
    },
    // Opens the accordion that holds the field, so the error is visible
    openAccordion(name) {
      const accordion = this.$refs[name];
      if (accordion && accordion.$children[0]) {
        accordion.$children[0].dataVisible = true;
      }
    },
    fail(field, message, accordion) {
      this.error[field] = message;
      if (!this.firstError) {
        this.firstError = field;
        if (accordion) {
          this.openAccordion(accordion);
        }
      }
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
      for (const field of KEEP_FIELDS) {
        const max = field === "annual" ? 100 : 1000;
        if (!this.isCount(this.keep[field], max)) {
          this.fail("keep_" + field, "settings.keep_range", "accordionPolicy");
        }
      }
      if (this.excludes.some((pattern) => pattern.length > 255)) {
        this.fail("excludes", "settings.excludes_too_long", "accordionPolicy");
      }
      if (this.excludes.length > 200) {
        this.fail("excludes", "settings.excludes_too_many", "accordionPolicy");
      }
      if (!this.isHours(this.ownerAlertHours)) {
        this.fail(
          "owner_alert_hours",
          "settings.hours_range",
          "accordionAlerts"
        );
      }
      if (!this.isHours(this.adminAlertHours)) {
        this.fail(
          "admin_alert_hours",
          "settings.hours_range",
          "accordionAlerts"
        );
      } else if (
        this.isHours(this.ownerAlertHours) &&
        this.adminAlertHours <= this.ownerAlertHours
      ) {
        this.fail(
          "admin_alert_hours",
          "settings.admin_after_owner",
          "accordionAlerts"
        );
      }
      if (this.adminRecipients.some((r) => !this.isEmail(r))) {
        this.fail(
          "admin_recipients",
          "settings.recipients_invalid",
          "accordionAlerts"
        );
      }
      if (this.alertSender && !this.isEmail(this.alertSender)) {
        this.fail(
          "alert_sender",
          "settings.alert_sender_invalid",
          "accordionAlerts"
        );
      }
      if (
        !this.isCount(this.diskAlertPercent, 99) ||
        this.diskAlertPercent < 50
      ) {
        this.fail(
          "disk_alert_percent",
          "settings.disk_percent_range",
          "accordionAlerts"
        );
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
        this.error[param] = this.$t("settings." + validationError.error);
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
        snapshot_interval: parseInt(this.snapshotInterval, 10),
        compression: this.compression,
        excludes: this.excludes,
        owner_alert_hours: this.ownerAlertHours,
        admin_alert_hours: this.adminAlertHours,
        admin_recipients: this.adminRecipients,
        alert_sender: this.alertSender,
        alert_language: this.alertLanguage,
        disk_alert_percent: this.diskAlertPercent,
      };
      for (const field of KEEP_FIELDS) {
        data["keep_" + field] = this.keep[field];
      }
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
    sendTestMail() {
      this.error.recipient = "";
      this.error.sendTestMail = "";
      this.testMailSent = "";
      this.loading.sendTestMail = true;
      const recipient = this.testRecipient;
      this.runModuleTask({
        action: "send-test-mail",
        data: { recipient },
        completed: () => {
          this.testMailSent = recipient;
          this.loading.sendTestMail = false;
        },
        validationFailed: (validationErrors) => {
          this.loading.sendTestMail = false;
          this.error.sendTestMail = this.$t(
            "settings." + validationErrors[0].error
          );
        },
        aborted: (message) => {
          this.error.sendTestMail = message;
          this.loading.sendTestMail = false;
        },
        failed: (message) => {
          this.error.sendTestMail = message;
          this.loading.sendTestMail = false;
        },
      });
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

.test-mail-row {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: $spacing-05;
  margin-bottom: $spacing-05;
}

.test-mail-field {
  flex: 0 1 20rem;
}

// Level with the field, not with its label
.test-mail-button {
  margin-top: $spacing-06;
}
</style>
