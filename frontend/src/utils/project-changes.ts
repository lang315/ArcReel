import i18n from "@/i18n";
import type { ProjectChange } from "@/types";

const GROUP_NAME_LIMIT = 5;

type EntityType = ProjectChange["entity_type"];

const ENTITY_LABEL_KEYS: Record<EntityType, string> = {
  project: "entityLabels.project",
  character: "entityLabels.character",
  clue: "entityLabels.clue",
  segment: "entityLabels.segment",
  episode: "entityLabels.episode",
  overview: "entityLabels.overview",
  draft: "entityLabels.draft",
};

export interface GroupedProjectChange {
  key: string;
  entityType: ProjectChange["entity_type"];
  action: ProjectChange["action"];
  changes: ProjectChange[];
}

export function buildEntityRevisionKey(
  entityType: ProjectChange["entity_type"],
  entityId: string,
): string {
  return `${entityType}:${entityId}`;
}

export function buildVersionResourceRevisionKey(
  resourceType: "storyboards" | "videos" | "characters" | "clues",
  resourceId: string,
): string {
  if (resourceType === "storyboards" || resourceType === "videos") {
    return buildEntityRevisionKey("segment", resourceId);
  }
  if (resourceType === "characters") {
    return buildEntityRevisionKey("character", resourceId);
  }
  return buildEntityRevisionKey("clue", resourceId);
}

export function groupChangesByType(
  changes: ProjectChange[],
): GroupedProjectChange[] {
  const groups = new Map<string, GroupedProjectChange>();

  for (const change of changes) {
    const key = `${change.entity_type}:${change.action}`;
    const existing = groups.get(key);
    if (existing) {
      existing.changes.push(change);
      continue;
    }
    groups.set(key, {
      key,
      entityType: change.entity_type,
      action: change.action,
      changes: [change],
    });
  }

  return [...groups.values()];
}

function getEntityLabel(group: GroupedProjectChange): string {
  if (group.action === "storyboard_ready") {
    return i18n.t("entityLabels.storyboard");
  }
  if (group.action === "video_ready") {
    return i18n.t("entityLabels.video");
  }
  return i18n.t(ENTITY_LABEL_KEYS[group.entityType] ?? "entityLabels.content");
}

function getChangeListLabel(change: ProjectChange): string {
  if (
    change.entity_type === "character" ||
    change.entity_type === "clue" ||
    change.entity_type === "segment"
  ) {
    return change.entity_id;
  }
  return change.label;
}

function summarizeGroupNames(group: GroupedProjectChange): string {
  const names = group.changes.slice(0, GROUP_NAME_LIMIT).map(getChangeListLabel);
  const suffix = group.changes.length > GROUP_NAME_LIMIT ? i18n.t("notifications.etc") : "";
  return `${names.join(i18n.t("notifications.listSeparator"))}${suffix}`;
}

function formatSingleNotificationText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return i18n.t("notifications.storyboardReady", { label: change.label });
  }
  if (change.action === "video_ready") {
    return i18n.t("notifications.videoReady", { label: change.label });
  }
  if (change.action === "created") {
    return i18n.t("notifications.created", { label: change.label });
  }
  if (change.action === "deleted") {
    return i18n.t("notifications.deleted", { label: change.label });
  }
  return i18n.t("notifications.updated", { label: change.label });
}

function formatSingleDeferredText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return i18n.t("deferred.storyboardReady", { label: change.label });
  }
  if (change.action === "video_ready") {
    return i18n.t("deferred.videoReady", { label: change.label });
  }
  if (change.action === "created") {
    return i18n.t("deferred.created", { label: change.label });
  }
  if (change.action === "deleted") {
    return i18n.t("deferred.deleted", { label: change.label });
  }
  return i18n.t("deferred.updated", { label: change.label });
}

export function formatGroupedNotificationText(
  group: GroupedProjectChange,
): string {
  if (group.changes.length === 1) {
    return formatSingleNotificationText(group.changes[0]);
  }

  const count = group.changes.length;
  const entity = getEntityLabel(group);
  const summary = summarizeGroupNames(group);

  if (group.action === "storyboard_ready" || group.action === "video_ready") {
    return i18n.t("notifications.storyboardReadyMulti", { count, entity, summary });
  }
  if (group.action === "created") {
    return i18n.t("notifications.createdMulti", { count, entity, summary });
  }
  if (group.action === "deleted") {
    return i18n.t("notifications.deletedMulti", { count, entity, summary });
  }
  return i18n.t("notifications.updatedMulti", { count, entity, summary });
}

export function formatGroupedDeferredText(
  group: GroupedProjectChange,
): string {
  if (group.changes.length === 1) {
    return formatSingleDeferredText(group.changes[0]);
  }

  const count = group.changes.length;
  const entity = getEntityLabel(group);
  const summary = summarizeGroupNames(group);

  if (group.action === "storyboard_ready" || group.action === "video_ready") {
    return i18n.t("deferred.storyboardReadyMulti", { count, entity, summary });
  }
  if (group.action === "created") {
    return i18n.t("deferred.createdMulti", { count, entity, summary });
  }
  if (group.action === "deleted") {
    return i18n.t("deferred.deletedMulti", { count, entity, summary });
  }
  return i18n.t("deferred.updatedMulti", { count, entity, summary });
}
