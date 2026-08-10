import {
  supabase,
} from "./supabaseClient";


function ensureUser(
  userId
) {
  if (!userId) {
    throw new Error(
      "User ID is required"
    );
  }
}


function cleanRepositoryUrl(
  repositoryUrl
) {
  const cleaned =
    repositoryUrl?.trim();

  if (!cleaned) {
    throw new Error(
      "Repository URL is required"
    );
  }

  return cleaned;
}


export async function getPinnedRepositories(
  userId
) {
  ensureUser(
    userId
  );

  const {
    data,
    error,
  } = await supabase
    .from(
      "repository_preferences"
    )
    .select(
      `
        repository_url,
        is_pinned,
        created_at,
        updated_at
      `
    )
    .eq(
      "user_id",
      userId
    )
    .eq(
      "is_pinned",
      true
    )
    .order(
      "updated_at",
      {
        ascending:
          false,
      }
    );

  if (error) {
    throw error;
  }

  return data || [];
}


export async function pinRepository(
  userId,
  repositoryUrl
) {
  ensureUser(
    userId
  );

  const repository =
    cleanRepositoryUrl(
      repositoryUrl
    );

  const {
    data,
    error,
  } = await supabase
    .from(
      "repository_preferences"
    )
    .upsert(
      {
        user_id:
          userId,

        repository_url:
          repository,

        is_pinned:
          true,

        updated_at:
          new Date()
            .toISOString(),
      },
      {
        onConflict:
          "user_id,repository_url",
      }
    )
    .select()
    .single();

  if (error) {
    throw error;
  }

  return data;
}


export async function unpinRepository(
  userId,
  repositoryUrl
) {
  ensureUser(
    userId
  );

  const repository =
    cleanRepositoryUrl(
      repositoryUrl
    );

  const {
    error,
  } = await supabase
    .from(
      "repository_preferences"
    )
    .delete()
    .eq(
      "user_id",
      userId
    )
    .eq(
      "repository_url",
      repository
    );

  if (error) {
    throw error;
  }
}