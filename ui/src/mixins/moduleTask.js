//
// Copyright (C) 2026 Nethesis S.r.l.
// SPDX-License-Identifier: GPL-3.0-or-later
//

import to from "await-to-js";

// Runs a module action with the usual events: completed, aborted and validation-failed.
// Needs the TaskService and UtilService mixins and the "core" and "instanceName" state.
export default {
  methods: {
    async runModuleTask({
      action,
      data,
      title,
      description,
      isNotificationHidden = true,
      completed,
      aborted,
      validationFailed,
      failed,
    }) {
      const eventId = this.getUuid();
      this.core.$root.$once(
        `${action}-aborted-${eventId}`,
        (taskResult, taskContext) => {
          console.error(`${taskContext.action} aborted`, taskResult);
          aborted(this.$t("error.generic_error"));
        }
      );
      this.core.$root.$once(
        `${action}-completed-${eventId}`,
        (taskContext, taskResult) => completed(taskResult.output)
      );
      if (validationFailed) {
        this.core.$root.$once(
          `${action}-validation-failed-${eventId}`,
          validationFailed
        );
      }
      const extra = {
        title: title || this.$t("action." + action),
        isNotificationHidden,
        eventId,
      };
      if (description) {
        extra.description = description;
      }
      const task = { action, extra };
      if (data) {
        task.data = data;
      }
      const res = await to(
        this.createModuleTaskForApp(this.instanceName, task)
      );
      if (res[0]) {
        console.error(`error creating task ${action}`, res[0]);
        failed(this.getErrorMessage(res[0]));
      }
    },
  },
};
