export type EmbyLayoutPayload = Record<string, unknown>;

export type EmbyLayoutMap = Record<string, EmbyLayoutPayload>;

export interface EmbyLayoutTemplate {
  id: number;
  name: string;
  description?: string | null;
  json_blob: EmbyLayoutMap;
  created_at?: string | null;
}

export interface EmbyLayoutUser {
  Id: string;
  Name: string;
  PrimaryImageTag?: string;
}
