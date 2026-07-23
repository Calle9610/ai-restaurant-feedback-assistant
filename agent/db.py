"""Supabase client helpers for the agent package.

Mirrors lib/supabase.ts on the frontend: two clients, not one.

- get_client() uses the anon key and respects Row Level Security.
  Use this by default, for all reads.
- get_service_client() uses the service role key, which BYPASSES RLS
  entirely. Only call this for writes that genuinely need to bypass RLS
  (e.g. agent actions, seeding). It is a deliberate escalation, not the
  default path — never swap get_client() for this out of convenience.
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv(".env.local")


def get_client() -> Client:
    url = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    key = os.environ["NEXT_PUBLIC_SUPABASE_ANON_KEY"]
    return create_client(url, key)


def get_service_client() -> Client:
    url = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)
