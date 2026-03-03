/**
 * Script / segment / scene type definitions.
 *
 * Maps to backend models in:
 * - lib/script_models.py (NarrationSegment, DramaScene, ImagePrompt, VideoPrompt, etc.)
 */

export const SHOT_TYPES = [
  "Extreme Close-up",
  "Close-up",
  "Medium Close-up",
  "Medium Shot",
  "Medium Long Shot",
  "Long Shot",
  "Extreme Long Shot",
  "Over-the-shoulder",
  "Point-of-view",
] as const;

export type ShotType = (typeof SHOT_TYPES)[number];

export const CAMERA_MOTIONS = [
  "Static",
  "Pan Left",
  "Pan Right",
  "Tilt Up",
  "Tilt Down",
  "Zoom In",
  "Zoom Out",
  "Tracking Shot",
] as const;

export type CameraMotion = (typeof CAMERA_MOTIONS)[number];

export type TransitionType = "cut" | "fade" | "dissolve";
export type DurationSeconds = 4 | 6 | 8;
export type AssetStatus = "pending" | "storyboard_ready" | "completed";

export interface Dialogue {
  speaker: string;
  line: string;
}

export interface Composition {
  shot_type: ShotType;
  lighting: string;
  ambiance: string;
}

export interface ImagePrompt {
  scene: string;
  composition: Composition;
}

export interface VideoPrompt {
  action: string;
  camera_motion: CameraMotion;
  ambiance_audio: string;
  dialogue: Dialogue[];
}

export interface GeneratedAssets {
  storyboard_image: string | null;
  video_clip: string | null;
  video_uri: string | null;
  status: AssetStatus;
}

export interface NarrationSegment {
  item_uid: string;
  segment_id: string;
  episode: number;
  duration_seconds: DurationSeconds;
  segment_break: boolean;
  novel_text: string;
  characters_in_segment: string[];
  clues_in_segment: string[];
  image_prompt: ImagePrompt | string;
  video_prompt: VideoPrompt | string;
  transition_to_next: TransitionType;
  generated_assets?: GeneratedAssets;
}

export interface DramaScene {
  item_uid: string;
  scene_id: string;
  duration_seconds: DurationSeconds;
  segment_break: boolean;
  scene_type: string;
  characters_in_scene: string[];
  clues_in_scene: string[];
  image_prompt: ImagePrompt | string;
  video_prompt: VideoPrompt | string;
  transition_to_next: TransitionType;
  generated_assets?: GeneratedAssets;
}

/** Novel source information (present in both episode script types). */
export interface NovelInfo {
  title: string;
  chapter: string;
  source_file: string;
}

export interface ScriptMetadata {
  created_at: string;
  updated_at: string;
}

export interface NarrationEpisodeScript {
  schema_version?: 2;
  episode: number;
  title: string;
  content_mode: "narration";
  duration_seconds: number;
  summary: string;
  novel: NovelInfo;
  characters_in_episode: string[];
  clues_in_episode: string[];
  segments: NarrationSegment[];
  metadata?: ScriptMetadata;
}

export interface DramaEpisodeScript {
  schema_version?: 2;
  episode: number;
  title: string;
  content_mode: "drama";
  duration_seconds: number;
  summary: string;
  novel: NovelInfo;
  characters_in_episode: string[];
  clues_in_episode: string[];
  scenes: DramaScene[];
  metadata?: ScriptMetadata;
}

export type EpisodeScript = NarrationEpisodeScript | DramaEpisodeScript;
