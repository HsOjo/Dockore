import { api } from "@dockore/shared";

export interface UpdateAsset {
  name: string;
  url: string;
}

export interface UpdateCheckResult {
  current: string;
  latest: string;
  haveNew: boolean;
  name: string;
  tagName: string;
  publishedAt: string;
  htmlUrl: string;
  body: string;
  downloadUrl: string | null;
  assets: UpdateAsset[];
}

export async function checkForUpdate(): Promise<UpdateCheckResult> {
  const { data, error } = await api.GET("/api/update");
  if (error) {
    throw error;
  }
  return {
    current: data.current,
    latest: data.latest,
    haveNew: data.have_new,
    name: data.name,
    tagName: data.tag_name,
    publishedAt: data.published_at,
    htmlUrl: data.html_url,
    body: data.body,
    downloadUrl: data.download_url || null,
    assets: (data.assets || []).map((a: any) => ({ name: a.name, url: a.url })),
  };
}
