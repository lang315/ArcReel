[🇬🇧 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

# Jianying Draft Export Guide

Export video clips already generated in ArcReel — organized by episode — as Jianying (JianYing) draft files. Open them directly in the Jianying desktop app for further editing: adjusting pacing, adding subtitles, transitions, voiceovers, and more.

## Prerequisites

- At least one episode's video clips have been generated in ArcReel
- **Jianying desktop app** (5.x or 6+) is installed locally

## Steps

### 1. Find the Jianying Draft Directory

You need to know the local path where Jianying stores its drafts before exporting.

**macOS:**
```
/Users/<username>/Movies/JianyingPro/User Data/Projects/com.lveditor.draft
```

**Windows:**
```
C:\Users\<username>\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
```

> **Tip**: You can find the "Draft Path" location in Jianying's settings. If you have changed the default path, use your actual draft directory.

### 2. Initiate the Export in ArcReel

1. Open the target project
2. Click the **Export** button in the upper-right corner
3. Select **Export as Jianying Draft**

### 3. Fill in the Export Parameters

| Parameter | Description |
|-----------|-------------|
| **Episode** | Select the episode to export (a dropdown selector appears for multi-episode projects) |
| **Jianying Version** | Select **6.0+** (recommended) or **5.x** — must match your locally installed Jianying version |
| **Draft Directory** | Enter the Jianying draft path found above (remembered automatically after the first entry) |

Click **Export Draft** — the browser will download a ZIP file.

### 4. Extract to the Draft Directory

Extract the downloaded ZIP file into the Jianying draft directory entered above. The extracted structure is as follows:

```
com.lveditor.draft/
├── ... (other existing drafts)
└── {project-name}_Episode{N}/          ← extracted folder
    ├── draft_info.json        (Jianying 6+) or draft_content.json (5.x)
    ├── draft_meta_info.json
    └── assets/
        ├── segment_S1.mp4
        ├── segment_S2.mp4
        └── ...
```

### 5. Open in Jianying

1. Open (or restart) the Jianying desktop app
2. Find the newly appeared **{project-name}\_Episode{N}** draft in the "Drafts" list
3. Double-click to open it and see all video clips on the timeline

## Export Content Description

### Narration Mode

- **Video track**: All generated video clips arranged in order
- **Subtitle track**: Automatically includes the original novel text for each clip as subtitles (white text with black stroke); style and position can be freely adjusted in Jianying

### Drama Mode

- **Video track**: All generated video clips arranged in scene order
- No subtitles included (subtitle structure for multi-character dialogue scenes is complex; it is recommended to add them manually in Jianying)

### Canvas Size

Determined automatically based on project settings:
- Portrait (9:16) → 1080×1920
- Landscape (16:9) → 1920×1080

If no aspect ratio is set for the project, it is auto-detected from the first video file.

## Frequently Asked Questions

### Cannot see the exported draft in Jianying?

- Confirm the ZIP was extracted to the correct draft directory
- Confirm the extracted folder is directly inside the draft directory (do not nest it in an extra subfolder)
- Try restarting Jianying

### Version mismatch — what to do?

The Jianying version selected during export must match your locally installed version:
- Jianying 6.0 and above → select **6.0+**
- Jianying 5.x → select **5.x**

If you selected the wrong version, simply re-export and choose the correct version.

### Some video clips are missing?

The export only includes video clips that have been successfully generated. If certain clips have not yet been generated or generation failed, they will not appear in the draft. Go back to ArcReel to generate the missing clips, then re-export.

---

<a name="chinese"></a>

# 剪映草稿导出指南

将 ArcReel 已生成的视频片段按集导出为剪映（JianYing）草稿文件，在剪映桌面版中直接打开并进行二次编辑——调整节奏、添加字幕、转场、配音等。

## 前置条件

- 已在 ArcReel 中完成至少一集的视频片段生成
- 本地已安装 **剪映桌面版**（5.x 或 6+）

## 操作步骤

### 1. 找到剪映草稿目录

导出前需要知道本地剪映草稿的存放路径。

**macOS：**
```
/Users/<用户名>/Movies/JianyingPro/User Data/Projects/com.lveditor.draft
```

**Windows：**
```
C:\Users\<用户名>\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
```

> **提示**：可在剪映设置中查看"草稿路径"的位置。如果你修改过默认路径，请使用实际的草稿目录。

### 2. 在 ArcReel 中发起导出

1. 打开目标项目
2. 点击右上角 **导出** 按钮
3. 选择 **导出为剪映草稿**

### 3. 填写导出参数

| 参数 | 说明 |
|------|------|
| **集数** | 选择要导出的集（多集项目会出现下拉选择器） |
| **剪映版本** | 选择 **6.0+**（推荐）或 **5.x**，需与本地安装的剪映版本匹配 |
| **草稿目录** | 填入上面找到的剪映草稿路径（首次填写后会自动记忆） |

点击 **导出草稿**，浏览器会下载一个 ZIP 文件。

### 4. 解压到草稿目录

将下载的 ZIP 文件解压到上面填写的剪映草稿目录中。解压后的结构如下：

```
com.lveditor.draft/
├── ... (其他已有草稿)
└── {项目名}_第{N}集/          ← 解压出来的文件夹
    ├── draft_info.json        (剪映 6+) 或 draft_content.json (5.x)
    ├── draft_meta_info.json
    └── assets/
        ├── segment_S1.mp4
        ├── segment_S2.mp4
        └── ...
```

### 5. 在剪映中打开

1. 打开（或重启）剪映桌面版
2. 在"草稿"列表中找到新出现的 **{项目名}\_第{N}集** 草稿
3. 双击打开即可在时间线上看到所有视频片段

## 导出内容说明

### 说书模式（Narration）

- **视频轨**：所有已生成的视频片段按顺序排列
- **字幕轨**：自动附带每个片段对应的小说原文作为字幕（白色文字、黑色描边），可在剪映中自由调整样式和位置

### 剧集模式（Drama）

- **视频轨**：按场景顺序排列所有已生成的视频片段
- 不附带字幕（多角色对话场景的字幕结构较复杂，建议在剪映中手动添加）

### 画布尺寸

自动根据项目设置确定：
- 竖屏（9:16）→ 1080×1920
- 横屏（16:9）→ 1920×1080

如项目未设置宽高比，会从首个视频文件自动检测。

## 常见问题

### 剪映中看不到导出的草稿？

- 确认 ZIP 解压到了正确的草稿目录
- 确认解压后的文件夹直接位于草稿目录下（不要多套一层文件夹）
- 尝试重启剪映

### 版本不匹配怎么办？

导出时选择的剪映版本必须与本地安装版本对应：
- 剪映 6.0 及以上 → 选择 **6.0+**
- 剪映 5.x → 选择 **5.x**

如果选错了版本，重新导出并选择正确版本即可。

### 部分视频片段缺失？

导出仅包含已成功生成的视频片段。如果某些片段尚未生成或生成失败，它们不会出现在草稿中。回到 ArcReel 补充生成后重新导出即可。
