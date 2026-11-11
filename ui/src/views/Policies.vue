<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("policies.title") }}</h2>
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
          :title="$t('policies.not_configured_title')"
          :description="$t('policies.not_configured_description')"
          :actionLabel="$t('policies.go_to_settings')"
          @action="goToSettings"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <cv-form @submit.prevent="configureModule">
            <p class="mg-bottom maxwidth">
              {{ $t("policies.backup_policy_description") }}
            </p>
            <NsComboBox
              v-model="snapshotInterval"
              :options="intervalOptions"
              auto-highlight
              :title="$t('policies.snapshot_interval')"
              :label="$t('policies.choose_snapshot_interval')"
              :invalid-message="$t(error.snapshot_interval)"
              :disabled="stillLoading || !isConfigured"
              class="mg-bottom maxwidth"
              ref="snapshot_interval"
            />
            <!-- Six short numbers: side by side on wide screens -->
            <div class="field-grid">
              <NsTextInput
                v-for="field in keepFields"
                :key="field"
                type="number"
                min="0"
                :max="field === 'annual' ? 100 : 1000"
                v-model.number="keep[field]"
                :label="$t('policies.keep_' + field)"
                :invalid-message="$t(error['keep_' + field])"
                :disabled="stillLoading || !isConfigured"
                class="mg-bottom"
                :ref="'keep_' + field"
              />
            </div>
            <NsComboBox
              v-model="compression"
              :options="compressionOptions"
              auto-highlight
              :title="$t('policies.compression')"
              :label="$t('policies.choose_compression')"
              :invalid-message="$t(error.compression)"
              :disabled="stillLoading || !isConfigured"
              class="mg-bottom maxwidth"
              ref="compression"
            />
            <cv-text-area
              v-model="excludesText"
              :label="$t('policies.excludes')"
              :helper-text="$t('policies.excludes_helper')"
              :invalid-message="$t(error.excludes)"
              :disabled="stillLoading || !isConfigured"
              placeholder="node_modules"
              class="mg-bottom maxwidth"
              ref="excludes"
            />
            <h6 class="mg-bottom">{{ $t("policies.integrity_check") }}</h6>
            <div class="verify-slider maxwidth">
              <NsSlider
                v-model="verifyPercent"
                :label="$t('policies.verify_percent')"
                min="0"
                max="100"
                step="5"
                minLabel=""
                maxLabel=""
                unitLabel="%"
                :invalidMessage="$t(error.verify_percent)"
                :disabled="stillLoading || !isConfigured"
                ref="verify_percent"
              />
            </div>
            <p class="verify-helper mg-bottom maxwidth">
              {{ verifyHelperText }}
            </p>
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
              >{{ $t("policies.save") }}</NsButton
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

const INTERVALS = [0, 1, 2, 4, 6, 8, 12, 24];
const COMPRESSIONS = [
  "none",
  "zstd",
  "zstd-fastest",
  "zstd-better-compression",
  "s2-default",
  "pgzip",
];
const KEEP_FIELDS = [
  "latest",
  "hourly",
  "daily",
  "weekly",
  "monthly",
  "annual",
];

export default {
  name: "Policies",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
    ModuleTask,
  ],
  pageTitle() {
    return this.$t("policies.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "policies",
      },
      urlCheckInterval: null,
      firstError: "",
      configuredHost: "",
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
      // NsSlider works with strings
      verifyPercent: "10",
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        snapshot_interval: "",
        keep_latest: "",
        keep_hourly: "",
        keep_daily: "",
        keep_weekly: "",
        keep_monthly: "",
        keep_annual: "",
        compression: "",
        excludes: "",
        verify_percent: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    stillLoading() {
      return this.loading.getConfiguration || this.loading.configureModule;
    },
    isConfigured() {
      return this.configuredHost !== "";
    },
    intervalOptions() {
      return INTERVALS.map((hours) => ({
        name: "interval-" + hours,
        value: String(hours),
        label: hours
          ? this.$tc("policies.interval_hours", hours, { count: hours })
          : this.$t("policies.interval_manual"),
      }));
    },
    compressionOptions() {
      return COMPRESSIONS.map((name) => ({
        name,
        value: name,
        label: this.$t("policies.compression_" + name.replace(/-/g, "_")),
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
    verifyPercentNumber() {
      // Number() refuses "10abc" and "10.5" passes as a non integer, unlike parseInt()
      return Number(this.verifyPercent);
    },
    verifyHelperText() {
      const percent = this.verifyPercentNumber;
      if (percent === 0) {
        return this.$t("policies.verify_helper_none");
      }
      if (percent === 100) {
        return this.$t("policies.verify_helper_all");
      }
      return this.$t("policies.verify_helper_partial", { percent });
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
    isCount(value, max) {
      return Number.isInteger(value) && value >= 0 && value <= max;
    },
    goToSettings() {
      this.goToAppPage(this.instanceName, "settings");
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
      this.snapshotInterval = String(config.snapshot_interval);
      for (const field of KEEP_FIELDS) {
        this.keep[field] = config["keep_" + field];
      }
      this.compression = config.compression;
      this.excludesText = (config.excludes || []).join("\n");
      this.verifyPercent = String(config.verify_percent);
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
      for (const field of KEEP_FIELDS) {
        const max = field === "annual" ? 100 : 1000;
        if (!this.isCount(this.keep[field], max)) {
          this.fail("keep_" + field, "settings.keep_range");
        }
      }
      if (this.excludes.some((pattern) => pattern.length > 255)) {
        this.fail("excludes", "settings.excludes_too_long");
      }
      if (this.excludes.length > 200) {
        this.fail("excludes", "settings.excludes_too_many");
      }
      if (!this.isCount(this.verifyPercentNumber, 100)) {
        this.fail("verify_percent", "settings.verify_percent_range");
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
        snapshot_interval: parseInt(this.snapshotInterval, 10),
        compression: this.compression,
        excludes: this.excludes,
        verify_percent: this.verifyPercentNumber,
      };
      for (const field of KEEP_FIELDS) {
        data["keep_" + field] = this.keep[field];
      }
      this.runModuleTask({
        action: "configure-module",
        data,
        title: this.$t("policies.configuring"),
        description: this.$t("policies.instance_configuration", {
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

// The slider root does not carry the page scope: reach it through a wrapper of the page.
// On small screens Carbon wraps the number input under the slider, which fits the width.
.verify-slider ::v-deep .wrapper,
.verify-slider ::v-deep .bx--slider-container {
  max-width: 100%;
}

.verify-slider ::v-deep .bx--slider {
  min-width: 0;
  margin-right: 1rem;
}

@media (min-width: 672px) {
  .verify-slider ::v-deep .wrapper,
  .verify-slider ::v-deep .bx--slider-container {
    width: 100%;
  }

  .verify-slider ::v-deep .bx--slider-container {
    flex-wrap: nowrap;
  }

  .verify-slider ::v-deep .bx--slider {
    flex: 1;
  }
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

.verify-helper {
  margin-top: $spacing-03;
}
</style>
