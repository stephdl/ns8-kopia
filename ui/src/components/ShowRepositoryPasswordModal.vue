<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <NsModal size="default" :visible="visible" @modal-hidden="onModalHidden">
    <template slot="title">{{
      $t("settings.show_repository_password")
    }}</template>
    <template slot="content">
      <NsInlineNotification
        kind="warning"
        :title="$t('settings.repository_password_warning_title')"
        :description="$t('settings.show_repository_password_warning')"
        :showCloseButton="false"
      />
      <cv-skeleton-text v-if="loading" :paragraph="false" />
      <NsCodeSnippet
        v-else-if="password"
        :copyTooltip="$t('settings.copy')"
        :copyFeedback="$t('settings.copied')"
        :feedbackAriaLabel="$t('settings.copied')"
        :wrapText="true"
        :hideExpandButton="true"
        class="mg-bottom"
        >{{ password }}</NsCodeSnippet
      >
      <NsInlineNotification
        v-if="error"
        kind="error"
        :title="$t('action.get-repository-password')"
        :description="error"
        :showCloseButton="false"
      />
    </template>
    <template slot="secondary-button">{{ core.$t("common.close") }}</template>
  </NsModal>
</template>

<script>
import { mapState } from "vuex";
import { UtilService, TaskService } from "@nethserver/ns8-ui-lib";
import ModuleTask from "@/mixins/moduleTask";

export default {
  name: "ShowRepositoryPasswordModal",
  mixins: [UtilService, TaskService, ModuleTask],
  props: {
    visible: { type: Boolean, required: true },
  },
  data() {
    return {
      password: "",
      loading: false,
      error: "",
    };
  },
  computed: {
    ...mapState(["instanceName", "core"]),
  },
  watch: {
    visible(isVisible) {
      if (isVisible) {
        this.getRepositoryPassword();
      }
    },
  },
  methods: {
    getRepositoryPassword() {
      this.loading = true;
      this.error = "";
      this.password = "";
      this.runModuleTask({
        action: "get-repository-password",
        completed: (output) => {
          this.password = output.repository_password;
          this.loading = false;
        },
        aborted: (message) => {
          this.error = message;
          this.loading = false;
        },
        failed: (message) => {
          this.error = message;
          this.loading = false;
        },
      });
    },
    onModalHidden() {
      // Do not keep the secret in memory once the window is closed
      this.password = "";
      this.$emit("hide");
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.mg-bottom {
  margin-top: $spacing-05;
  margin-bottom: $spacing-05;
}
</style>
