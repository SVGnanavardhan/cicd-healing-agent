import {
  createClient,
} from "@supabase/supabase-js";


const supabaseUrl =
  import.meta.env
    .VITE_SUPABASE_URL;

const supabasePublishableKey =
  import.meta.env
    .VITE_SUPABASE_PUBLISHABLE_KEY ||
  import.meta.env
    .VITE_SUPABASE_ANON_KEY;


if (!supabaseUrl) {
  throw new Error(
    "VITE_SUPABASE_URL is missing in frontend/.env"
  );
}


if (!supabasePublishableKey) {
  throw new Error(
    "VITE_SUPABASE_PUBLISHABLE_KEY is missing in frontend/.env"
  );
}


export const supabase =
  createClient(
    supabaseUrl,
    supabasePublishableKey,
    {
      auth: {
        persistSession:
          true,

        autoRefreshToken:
          true,

        detectSessionInUrl:
          true,
      },
    }
  );