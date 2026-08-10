import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  supabase,
} from "../services/supabaseClient";


const AuthContext =
  createContext(null);


export function AuthProvider({
  children,
}) {
  const [user, setUser] =
    useState(null);

  const [session, setSession] =
    useState(null);

  const [profile, setProfile] =
    useState(null);

  const [authLoading, setAuthLoading] =
    useState(true);


  async function loadProfile(
    userId
  ) {
    if (!userId) {
      setProfile(null);
      return null;
    }

    const {
      data,
      error,
    } = await supabase
      .from("profiles")
      .select(
        `
          user_id,
          full_name,
          github_username,
          avatar_url,
          created_at,
          updated_at
        `
      )
      .eq(
        "user_id",
        userId
      )
      .maybeSingle();

    if (error) {
      console.error(
        "Profile loading failed:",
        error.message
      );

      setProfile(null);

      return null;
    }

    setProfile(data);

    return data;
  }


  useEffect(() => {
    let mounted = true;

    async function loadSession() {
      try {
        const {
          data: {
            session:
              currentSession,
          },
          error,
        } =
          await supabase.auth.getSession();

        if (!mounted) {
          return;
        }

        if (error) {
          console.error(
            "Session loading failed:",
            error.message
          );
        }

        const currentUser =
          currentSession?.user ??
          null;

        setSession(
          currentSession
        );

        setUser(
          currentUser
        );

        if (currentUser) {
          await loadProfile(
            currentUser.id
          );
        } else {
          setProfile(null);
        }
      } finally {
        if (mounted) {
          setAuthLoading(false);
        }
      }
    }

    loadSession();

    const {
      data: {
        subscription,
      },
    } =
      supabase.auth.onAuthStateChange(
        async (
          _event,
          updatedSession
        ) => {
          if (!mounted) {
            return;
          }

          const updatedUser =
            updatedSession?.user ??
            null;

          setSession(
            updatedSession
          );

          setUser(
            updatedUser
          );

          if (updatedUser) {
            await loadProfile(
              updatedUser.id
            );
          } else {
            setProfile(null);
          }

          if (mounted) {
            setAuthLoading(false);
          }
        }
      );

    return () => {
      mounted = false;

      subscription.unsubscribe();
    };
  }, []);


  async function signUp(
    email,
    password,
    fullName
  ) {
    const normalizedEmail =
      email
        .trim()
        .toLowerCase();

    const {
      data,
      error,
    } =
      await supabase.auth.signUp({
        email:
          normalizedEmail,

        password,

        options: {
          data: {
            full_name:
              fullName.trim(),
          },
        },
      });

    if (error) {
      throw error;
    }

    return data;
  }


  async function signIn(
    email,
    password
  ) {
    const normalizedEmail =
      email
        .trim()
        .toLowerCase();

    const {
      data,
      error,
    } =
      await supabase.auth
        .signInWithPassword({
          email:
            normalizedEmail,
          password,
        });

    if (error) {
      throw error;
    }

    return data;
  }


  async function signOut() {
    const {
      error,
    } =
      await supabase.auth.signOut();

    if (error) {
      throw error;
    }

    setSession(null);
    setUser(null);
    setProfile(null);
  }


  async function resetPassword(
    email
  ) {
    const normalizedEmail =
      email
        .trim()
        .toLowerCase();

    const {
      data,
      error,
    } =
      await supabase.auth
        .resetPasswordForEmail(
          normalizedEmail,
          {
            redirectTo:
              `${window.location.origin}/reset-password`,
          }
        );

    if (error) {
      throw error;
    }

    return data;
  }


  async function updatePassword(
    password
  ) {
    const {
      data,
      error,
    } =
      await supabase.auth.updateUser({
        password,
      });

    if (error) {
      throw error;
    }

    return data;
  }


  async function updateProfile(
    profileData
  ) {
    if (!user?.id) {
      throw new Error(
        "User must be logged in"
      );
    }

    const payload = {
      user_id:
        user.id,

      full_name:
        profileData.full_name
          ?.trim() ||
        null,

      github_username:
        profileData
          .github_username
          ?.trim() ||
        null,

      avatar_url:
        profileData.avatar_url
          ?.trim() ||
        null,

      updated_at:
        new Date()
          .toISOString(),
    };

    const {
      data,
      error,
    } = await supabase
      .from("profiles")
      .upsert(
        payload,
        {
          onConflict:
            "user_id",
        }
      )
      .select(
        `
          user_id,
          full_name,
          github_username,
          avatar_url,
          created_at,
          updated_at
        `
      )
      .single();

    if (error) {
      throw error;
    }

    setProfile(data);

    return data;
  }


  async function refreshProfile() {
    if (!user?.id) {
      setProfile(null);
      return null;
    }

    return loadProfile(
      user.id
    );
  }


  async function getAccessToken() {
    const {
      data: {
        session:
          currentSession,
      },
      error,
    } =
      await supabase.auth.getSession();

    if (error) {
      throw error;
    }

    return (
      currentSession
        ?.access_token ??
      null
    );
  }


  const value =
    useMemo(
      () => ({
        user,
        session,
        profile,
        authLoading,

        isAuthenticated:
          Boolean(user),

        signUp,
        signIn,
        signOut,
        resetPassword,
        updatePassword,
        updateProfile,
        refreshProfile,
        getAccessToken,
      }),
      [
        user,
        session,
        profile,
        authLoading,
      ]
    );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {
  const context =
    useContext(
      AuthContext
    );

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}