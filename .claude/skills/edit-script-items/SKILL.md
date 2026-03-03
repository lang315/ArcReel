---
name: edit-script-items
description: 剧本分镜进行 insert/update/delete 结构编辑。适用于修改 narration/drama 的分镜信息、执行镜头拆分、插入分镜、删除分镜等操作。绝不应该使用 Write 工具直接改写 scripts/*.json。
---

# edit-script-items

使用本 skill 时，必须：

1. 先读取最新 `project.json` 与目标 `scripts/*.json`
2. 始终用 `item_uid` 定位目标 item
3. 通过本地 CLI 调用 `lib/script_item_service.py`
4. 每次只做一个操作：`insert` / `update` / `delete`
5. 每步成功后重新读取最新 script，再决定下一步
6. 绝不直接写 `scripts/*.json`

## 适用场景

- 新增一个 narration segment / drama scene
- 修改单个 item 的时长、prompt、角色/线索、scene_type 等字段
- 删除单个 item，并把当前素材送入回收站
- 编排“拆分镜头”这类复合动作

## 命令

```bash
# insert
python .claude/skills/edit-script-items/scripts/edit_script_items.py \
  <project> <script_file> insert \
  --base-updated-at "<updated_at>" \
  --position after \
  --anchor-item-uid itm_123456abcdef \
  --payload '{"duration_seconds":4,"segment_break":false,"novel_text":"原文","characters_in_segment":[],"clues_in_segment":[],"image_prompt":"...","video_prompt":"...","transition_to_next":"cut"}'

# update
python .claude/skills/edit-script-items/scripts/edit_script_items.py \
  <project> <script_file> update \
  --item-uid itm_123456abcdef \
  --base-updated-at "<updated_at>" \
  --payload '{"image_prompt":"新的 prompt"}'

# delete
python .claude/skills/edit-script-items/scripts/edit_script_items.py \
  <project> <script_file> delete \
  --item-uid itm_123456abcdef \
  --base-updated-at "<updated_at>" \
  --reason "assistant_delete"
```

## 复合动作

如果用户要求“拆分镜头”，assistant 必须自己编排：

1. 如果需要保留原分镜的素材，则先执行一次 update，修改原分镜信息，再执行一次 insert，在原分镜后新增一个分镜。
2. 如果不需要保留原分镜的素材，则先执行一次 delete，删除原分镜，再分步执行多次 insert，在原分镜位置插入新分镜。

每一步之后都重新读取 script，刷新 anchor 与 `updated_at`。
