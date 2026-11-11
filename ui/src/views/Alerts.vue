<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("alerts.title") }}</h2>
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
    <cv-row v-if="!isConfigured && !loading.getConfiguration">
      <cv-column>
        <NsInlineNotification
          kind="info"
          :title="$t('alerts.not_configured_title')"
          :description="$t('alerts.not_configured_description')"
          :actionLabel="$t('alerts.go_to_settings')"
          @action="goToSettings"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <cv-form @submit.prevent="configureModule">
            <NsInlineNotification
              v-if="!smarthostEnabled && !loading.getConfiguration"
              kind="warning"
              :title="$t('alerts.smarthost_missing_title')"
              :description="$t('alerts.smarthost_missing_description')"
              :actionLabel="$t('alerts.go_to_smarthost')"
              @action="goToSmarthost"
              :showCloseButton="false"
              class="maxwidth"
            />
            <!-- Short numbers side by side on wide screens, like the Policies page -->
            <div class="field-grid">
              <NsTextInput
                type="number"
                min="1"
                max="8760"
                v-model.number="ownerAlertHours"
                :label="$t('alerts.owner_alert_hours')"
                :helper-text="$t('alerts.owner_alert_hours_helper')"
                :invalid-message="$t(error.owner_alert_hours)"
                :disabled="stillLoading || !isConfigured"
                class="mg-bottom"
                ref="owner_alert_hours"
              />
              <NsTextInput
                type="number"
                min="1"
                max="8760"
                v-model.number="adminAlertHours"
                :label="$t('alerts.admin_alert_hours')"
                :helper-text="$t('alerts.admin_alert_hours_helper')"
                :invalid-message="$t(error.admin_alert_hours)"
                :disabled="stillLoading || !isConfigured"
                class="mg-bottom"
                ref="admin_alert_hours"
              />
            </div>
            <div class="field-grid">
              <NsTextInput
                type="number"
                min="50"
                max="99"
                v-model.number="diskAlertPercent"
                :label="$t('alerts.disk_alert_percent')"
                :helper-text="$t('alerts.disk_alert_percent_helper')"
                :invalid-message="$t(error.disk_alert_percent)"
                :disabled="stillLoading || !isConfigured"
                class="mg-bottom"
                ref="disk_alert_percent"
              />
            </div>
            <cv-text-area
              v-model="adminRecipientsText"
              :label="$t('alerts.admin_recipients')"
              :helper-text="$t('alerts.admin_recipients_helper')"
              :invalid-message="$t(error.admin_recipients)"
              :disabled="stillLoading || !isConfigured"
              placeholder="it@example.org"
              class="mg-bottom maxwidth"
              ref="admin_recipients"
            />
            <NsTextInput
              v-model.trim="alertSender"
              :label="$t('alerts.alert_sender')"
              :placeholder="defaultSender || 'default_sender'"
              :helper-text="$t('alerts.alert_sender_helper')"
              :invalid-message="$t(error.alert_sender)"
              :disabled="stillLoading || !isConfigured"
              class="mg-bottom maxwidth"
              ref="alert_sender"
            />
            <NsComboBox
              v-model="alertLanguage"
              :options="languageOptions"
              auto-highlight
              :title="$t('alerts.alert_language')"
              :label="$t('alerts.choose_alert_language')"
              :invalid-message="$t(error.alert_language)"
              :disabled="stillLoading || !isConfigured"
              class="mg-bottom maxwidth"
              ref="alert_language"
            />
            <h6 class="mg-bottom">{{ $t("alerts.test_mail") }}</h6>
            <div class="test-mail-row">
              <NsTextInput
                v-model.trim="testRecipient"
                type="email"
                :label="$t('alerts.test_mail_recipient')"
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
                >{{ $t("alerts.send_test_mail") }}</NsButton
              >
            </div>
            <NsInlineNotification
              v-if="testMailSent"
              kind="success"
              :title="$t('alerts.test_mail_sent')"
              :description="
                $t('alerts.test_mail_sent_description', {
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
            <NsButton
              kind="primary"
              :icon="Save20"
              :loading="loading.configureModule"
              :disabled="stillLoading || !isConfigured"
              >{{ $t("alerts.save") }}</NsButton
            >
          </cv-form>
        </cv-tile>
      </cv-column>
    </cv-row>
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
} from "@nethserver/ns8-ui-lib";
import ModuleTask from "@/mixins/moduleTask";

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

export default {
  name: "Alerts",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
    ModuleTask,
  ],
  pageTitle() {
    return this.$t("alerts.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "alerts",
      },
      urlCheckInterval: null,
      firstError: "",
      configuredHost: "",
      smarthostEnabled: true,
      defaultSender: "",
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
    languageOptions() {
      return Object.keys(LANGUAGES).map((code) => ({
        name: code,
        value: code,
        label: LANGUAGES[code],
      }));
    },
    adminRecipients() {
      return [
        ...new Set(
          this.adminRecipientsText.split(/[\s,;]+/).filter((r) => r !== "")
        ),
      ];
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
    isHours(value, max = 8760) {
      return Number.isInteger(value) && value >= 1 && value <= max;
    },
    isCount(value, max) {
      return Number.isInteger(value) && value >= 0 && value <= max;
    },
    goToSettings() {
      this.goToAppPage(this.instanceName, "settings");
    },
    goToSmarthost() {
      this.core.$router.push("/settings/smarthost");
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
      this.configuredHost = config.host;
      this.smarthostEnabled = config.smarthost_enabled;
      this.defaultSender = config.default_sender || "";
      this.ownerAlertHours = config.owner_alert_hours;
      this.adminAlertHours = config.admin_alert_hours;
      this.adminRecipientsText = (config.admin_recipients || []).join("\n");
      this.alertSender = config.alert_sender || "";
      this.alertLanguage = config.alert_language;
      this.diskAlertPercent = config.disk_alert_percent;
      this.loading.getConfiguration = false;
    },
    fail(field, message) {
      this.error[field] = message;
      if (!this.firstError) {
        this.firstError = field;
      }
    },
    validateConfigureModule() {
      this.clearErrors(this);
      this.firstError = "";
      if (!this.isHours(this.ownerAlertHours)) {
        this.fail("owner_alert_hours", "settings.hours_range");
      }
      if (!this.isHours(this.adminAlertHours)) {
        this.fail("admin_alert_hours", "settings.hours_range");
      } else if (
        this.isHours(this.ownerAlertHours) &&
        this.adminAlertHours <= this.ownerAlertHours
      ) {
        this.fail("admin_alert_hours", "settings.admin_after_owner");
      }
      if (this.adminRecipients.some((r) => !this.isEmail(r))) {
        this.fail("admin_recipients", "settings.recipients_invalid");
      }
      if (this.alertSender && !this.isEmail(this.alertSender)) {
        this.fail("alert_sender", "settings.alert_sender_invalid");
      }
      if (
        !this.isCount(this.diskAlertPercent, 99) ||
        this.diskAlertPercent < 50
      ) {
        this.fail("disk_alert_percent", "settings.disk_percent_range");
      }
      if (this.firstError) {
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
          this.focusElement(param);
          focusAlreadySet = true;
        }
      }
    },
    configureModule() {
      if (!this.isConfigured || !this.validateConfigureModule()) {
        return;
      }
      this.loading.configureModule = true;
      this.error.configureModule = "";
      const data = {
        owner_alert_hours: this.ownerAlertHours,
        admin_alert_hours: this.adminAlertHours,
        admin_recipients: this.adminRecipients,
        alert_sender: this.alertSender,
        alert_language: this.alertLanguage,
        disk_alert_percent: this.diskAlertPercent,
      };
      this.runModuleTask({
        action: "configure-module",
        data,
        title: this.$t("alerts.configuring"),
        description: this.$t("alerts.instance_configuration", {
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

// Two short fields per line on wide screens, every other control takes the same width
.field-grid {
  display: grid;
  grid-template-columns: 1fr;
  column-gap: 1rem;
  max-width: 38rem;
}

@media (min-width: 672px) {
  .field-grid {
    grid-template-columns: repeat(2, 1fr);
  }
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
