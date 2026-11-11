<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <div>
    <NsPasswordInput
      ref="password"
      :value="value"
      @input="$emit('input', $event)"
      @passwordValidation="$emit('validation', $event)"
      :newPasswordLabel="$t('settings.repository_password')"
      :confirmPasswordLabel="$t('settings.repository_password_confirm')"
      :newPasswordInvalidMessage="$t(error)"
      :confirmPasswordInvalidMessage="$t(confirmError)"
      :newPasswordVisible="isVisible"
      :confirmPasswordVisible="isVisible"
      :passwordHideLabel="core.$t('password.hide_password')"
      :passwordShowLabel="core.$t('password.show_password')"
      :lengthLabel="core.$t('password.long_enough')"
      :lowercaseLabel="core.$t('password.lowercase_letter')"
      :uppercaseLabel="core.$t('password.uppercase_letter')"
      :numberLabel="core.$t('password.number')"
      :symbolLabel="core.$t('password.symbol')"
      :equalLabel="core.$t('password.equal')"
      :focus="focus"
      :minLength="12"
      :disabled="disabled"
      class="mg-bottom"
    />
    <NsButton
      type="button"
      kind="tertiary"
      size="field"
      :icon="Password20"
      :disabled="disabled"
      class="mg-bottom"
      @click="generate"
      >{{ $t("settings.generate_password") }}</NsButton
    >
    <cv-checkbox
      :label="$t('settings.repository_password_written_down')"
      :checked="acknowledged"
      :disabled="disabled"
      value="written-down"
      @change="$emit('acknowledge', $event)"
      class="mg-bottom"
    />
  </div>
</template>

<script>
import { mapState } from "vuex";
import { IconService } from "@nethserver/ns8-ui-lib";
import { generatePassword } from "@/lib/password";

export default {
  name: "RepositoryPasswordInput",
  mixins: [IconService],
  props: {
    value: { type: String, default: "" },
    acknowledged: { type: Boolean, default: false },
    error: { type: String, default: "" },
    confirmError: { type: String, default: "" },
    focus: { type: Object, default: undefined },
    disabled: Boolean,
  },
  data() {
    return {
      isVisible: false,
    };
  },
  computed: {
    ...mapState(["core"]),
  },
  methods: {
    generate() {
      const password = generatePassword();
      this.$emit("input", password);
      // The confirmation field keeps its own copy: fill it too, and show both to copy them
      this.$refs.password.confirmPassword = password;
      this.isVisible = true;
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.mg-bottom {
  margin-bottom: $spacing-06;
}
</style>
