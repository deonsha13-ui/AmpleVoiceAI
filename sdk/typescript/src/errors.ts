// SDK-level exceptions. All subclass `AmpleVoiceAISdkError` so callers can
// catch them as one category.

export class AmpleVoiceAISdkError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "AmpleVoiceAISdkError";
    }
}

/**
 * Raised when node data fails client-side validation (unknown field,
 * missing required field, obvious type mismatch).
 *
 * Server-side Pydantic validation runs on save and may raise further
 * errors via `ApiError` — this class covers the fast-fail cases caught
 * at the `Workflow.add()` call site.
 */
export class ValidationError extends AmpleVoiceAISdkError {
    constructor(message: string) {
        super(message);
        this.name = "ValidationError";
    }
}

/** Raised when the AmpleVoiceAI backend returns a non-2xx response. */
export class ApiError extends AmpleVoiceAISdkError {
    readonly statusCode: number;
    readonly body: unknown;

    constructor(statusCode: number, message: string, body?: unknown) {
        super(`[${statusCode}] ${message}`);
        this.name = "ApiError";
        this.statusCode = statusCode;
        this.body = body;
    }
}

/** Raised when a referenced node type isn't registered on the server. */
export class SpecMismatchError extends AmpleVoiceAISdkError {
    constructor(message: string) {
        super(message);
        this.name = "SpecMismatchError";
    }
}
