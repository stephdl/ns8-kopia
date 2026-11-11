<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <NsModal
    size="default"
    kind="danger"
    :visible="visible"
    :isLoading="loading"
    :primary-button-disabled="loading || !isValid"
    @modal-hidden="onModalHidden"
    @primary-click="changeRepositoryPassword"
  >
    <template slot="title">{{
      $t("settings.change_repository_password")
    }}</template>
    <template slot="content">
      <p class="mg-bottom">
        {{ $t("settings.change_repository_password_intro") }}
      </p>
      <ul class="mg-bottom bullets">
        <li>{{ $t("settings.change_repository_password_key") }}</li>
        <li>{{ $t("settings.change_repository_password_old_backups") }}</li>
        <li>{{ $t("settings.change_repository_password_restart") }}</li>
      </ul>
      <RepositoryPasswordInput
        v-model="password"
        :acknowledged="acknowledged"
        :error="errors.repository_password"
        :confirmError="errors.confirm"
        :focus="focus"
        :disabled="loading"
        @validation="validation = $event"
        @acknowledge="acknowledged = $event"
      />
      <NsInlineNotification
        v-if="errors.change"
        kind="error"
        :title="$t('action.change-repository-password')"
        :description="errors.change"
        :showCloseButton="false"
      />
    </template>
    <template slot="secondary-button">{{ core.$t("common.cancel") }}</template>
    <template slot="primary-button">{{
      $t("settings.change_repository_password")
    }}</template>
  </NsModal>
</template>

<script>
import { mapState } from "vuex";
import { UtilService, TaskService } from "@nethserver/ns8-ui-lib";
import ModuleTask from "@/mixins/moduleTask";
import RepositoryPasswordInput from "@/components/RepositoryPasswordInput.vue";
import { passwordError } from "@/lib/password";

export default {
  name: "ChangeRepositoryPasswordModal",
  components: { RepositoryPasswordInput },
  mixins: [UtilService, TaskService, ModuleTask],
  props: {
    visible: { type: Boolean, required: true },
  },
  data() {
    return {
      password: "",
      acknowledged: false,
      validation: null,
      focus: { element: "" },
      loading: false,
      errors: { repository_password: "", confirm: "", change: "" },
    };
  },
  computed: {
    ...mapState(["instanceName", "core"]),
    isValid() {
      return this.acknowledged && this.password !== "";
    },
  },
  watch: {
    password() {
      this.errors.repository_password = "";
      this.errors.confirm = "";
    },
  },
  methods: {
    reset() {
      this.password = "";
      this.acknowledged = false;
      this.errors = { repository_password: "", confirm: "", change: "" };
    },
    onModalHidden() {
      this.reset();
      this.$emit("hide");
    },
    changeRepositoryPassword() {
      const error = passwordError(this.password);
      if (error) {
        this.errors.repository_password = error;
        this.focus = { element: "newPassword" };
        return;
      }
      if (!this.validation || !this.validation.isEqualOk) {
        this.errors.confirm = "settings.password_mismatch";
        this.focus = { element: "confirmPassword" };
        return;
      }
      this.loading = true;
      this.errors.change = "";
      this.runModuleTask({
        action: "change-repository-password",
        data: { repository_password: this.password },
        title: this.$t("settings.changing_repository_password"),
        isNotificationHidden: false,
        completed: () => {
          this.loading = false;
          this.reset();
          this.$emit("changed");
        },
        aborted: (message) => {
          this.errors.change = message;
          this.loading = false;
        },
        failed: (message) => {
          this.errors.change = message;
          this.loading = false;
        },
        validationFailed: (validationErrors) => {
          this.loading = false;
          for (const e of validationErrors) {
            this.errors[e.parameter] = "settings." + e.error;
          }
          this.focus = { element: "newPassword" };
        },
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

.bullets {
  list-style: disc;
  padding-left: $spacing-06;
}
</style>
