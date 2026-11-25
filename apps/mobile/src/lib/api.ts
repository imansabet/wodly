import { API_URL } from "./config";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong";
}

type Options = { method?: string; body?: unknown };

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: options.method ?? "GET",
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check your connection.");
  }

  if (!response.ok) {
    let detail = response.status === 422 ? "Invalid input" : "Something went wrong";
    try {
      const data = await response.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch {
      // keep the default message
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}
