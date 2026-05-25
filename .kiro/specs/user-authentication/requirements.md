# Requirements Document

## Introduction

This document defines the requirements for the Authentication & User System (Step 2) of SynapseAI — an AI Workspace SaaS. The system provides secure user registration, login, session management, password recovery, and email verification. It is built on a FastAPI (Python) backend with PostgreSQL and Redis, and a SvelteKit (TypeScript) frontend. The scaffold from Step 1 is already in place: the User and Subscription models exist, core security utilities (JWT, bcrypt) are available, and the frontend login/register page shells are wired up.

## Glossary

- **Auth_Service**: The backend authentication layer responsible for credential validation, token issuance, and session lifecycle management.
- **Registration_Handler**: The backend component that processes new user sign-up requests.
- **Login_Handler**: The backend component that validates credentials and issues tokens.
- **Token_Store**: The Redis-backed store used to track refresh token validity and blacklisted tokens.
- **Refresh_Token**: A long-lived (7-day) opaque token stored in an httpOnly cookie, used to obtain new access tokens without re-authentication.
- **Access_Token**: A short-lived (15-minute) JWT sent in the Authorization header to authenticate API requests.
- **Password_Reset_Token**: A single-use, time-limited token (1-hour TTL) used to authorize a password change.
- **Email_Verification_Token**: A single-use, time-limited token (24-hour TTL) sent to a user's email to confirm ownership.
- **Rate_Limiter**: The slowapi + Redis component that enforces per-IP request limits on sensitive endpoints.
- **Email_Worker**: The Celery background task that sends transactional emails (verification, password reset).
- **Auth_Guard**: The SvelteKit `/app` layout component that redirects unauthenticated users to `/login`.
- **Token_Refresh_Interceptor**: The Axios response interceptor in `client.ts` that silently retries failed requests after obtaining a new access token.
- **Subscription**: A record created alongside each new user that tracks their plan (free/pro/team) and token quota.

---

## Requirements

### Requirement 1: User Registration

**User Story:** As a new visitor, I want to create an account with my email and password, so that I can access the SynapseAI workspace.

#### Acceptance Criteria

1. WHEN a POST request is received at `/api/v1/auth/register` with a valid email, password (minimum 8 characters, at least one uppercase letter, at least one digit), and optional full_name, THE Registration_Handler SHALL hash the password using bcrypt and persist a new User record to the database.
2. WHEN a new User record is successfully created, THE Registration_Handler SHALL create an associated Subscription record with plan set to `free` and tokens_limit set to 50,000.
3. WHEN a new User record is successfully created, THE Registration_Handler SHALL enqueue an Email_Worker task to send an email verification message containing a signed Email_Verification_Token to the user's email address.
4. WHEN registration succeeds, THE Registration_Handler SHALL return an HTTP 201 response containing an Access_Token and the serialized User object (id, email, full_name, avatar_url, is_verified, is_superuser).
5. WHEN a POST request is received at `/api/v1/auth/register` with an email that already exists in the database, THE Registration_Handler SHALL return an HTTP 409 response with a descriptive error detail.
6. WHEN a POST request is received at `/api/v1/auth/register` with a password shorter than 8 characters or missing required complexity, THE Registration_Handler SHALL return an HTTP 422 response with field-level validation errors.
7. THE Registration_Handler SHALL NOT store plaintext passwords at any point during the registration process.

### Requirement 2: User Login

**User Story:** As a registered user, I want to sign in with my email and password, so that I can access my workspace.

#### Acceptance Criteria

1. WHEN a POST request is received at `/api/v1/auth/login` with a valid email and correct password, THE Login_Handler SHALL return an HTTP 200 response containing an Access_Token and the serialized User object.
2. WHEN a POST request is received at `/api/v1/auth/login` with valid credentials, THE Login_Handler SHALL set an httpOnly, Secure, SameSite=Lax cookie named `refresh_token` containing a Refresh_Token with a 7-day expiry.
3. WHEN a POST request is received at `/api/v1/auth/login` with valid credentials, THE Login_Handler SHALL persist a new refresh_tokens record containing the token hash, user_id, and expires_at timestamp.
4. WHEN a POST request is received at `/api/v1/auth/login` with an email that does not exist or an incorrect password, THE Login_Handler SHALL return an HTTP 401 response with the detail "Invalid credentials" (without distinguishing which field is wrong).
5. WHEN a POST request is received at `/api/v1/auth/login` for a user whose `is_active` flag is false, THE Login_Handler SHALL return an HTTP 403 response with the detail "Account is disabled".
6. WHILE the Rate_Limiter is active, WHEN more than 5 POST requests are received at `/api/v1/auth/login` from the same IP address within a 60-second window, THE Rate_Limiter SHALL return an HTTP 429 response.

### Requirement 3: Token Refresh

**User Story:** As an authenticated user, I want my session to be silently renewed, so that I am not logged out while actively using the application.

#### Acceptance Criteria

1. WHEN a POST request is received at `/api/v1/auth/refresh` with a valid `refresh_token` httpOnly cookie, THE Auth_Service SHALL validate the token signature, check that the corresponding refresh_tokens record exists and is not revoked, and return an HTTP 200 response containing a new Access_Token.
2. WHEN a POST request is received at `/api/v1/auth/refresh` with a Refresh_Token whose `expires_at` is in the past, THE Auth_Service SHALL return an HTTP 401 response with the detail "Refresh token expired".
3. WHEN a POST request is received at `/api/v1/auth/refresh` with a Refresh_Token that has been revoked in the Token_Store, THE Auth_Service SHALL return an HTTP 401 response with the detail "Refresh token revoked".
4. WHEN a POST request is received at `/api/v1/auth/refresh` with no `refresh_token` cookie present, THE Auth_Service SHALL return an HTTP 401 response.
5. WHEN the Token_Refresh_Interceptor receives an HTTP 401 response from any API call, THE Token_Refresh_Interceptor SHALL call `/api/v1/auth/refresh` once, update the stored Access_Token, and retry the original request with the new token.
6. WHEN the Token_Refresh_Interceptor's refresh call itself returns an HTTP 401, THE Token_Refresh_Interceptor SHALL clear the local auth state and redirect the user to `/login`.

### Requirement 4: Logout

**User Story:** As an authenticated user, I want to sign out, so that my session is terminated and my credentials are no longer usable.

#### Acceptance Criteria

1. WHEN a POST request is received at `/api/v1/auth/logout` with a valid `refresh_token` cookie, THE Auth_Service SHALL mark the corresponding refresh_tokens record as revoked in the database and set a blacklist key in the Token_Store with a TTL equal to the token's remaining lifetime.
2. WHEN logout succeeds, THE Auth_Service SHALL clear the `refresh_token` httpOnly cookie by setting it with an expired Max-Age and return an HTTP 200 response.
3. WHEN a POST request is received at `/api/v1/auth/logout` with no `refresh_token` cookie, THE Auth_Service SHALL return an HTTP 200 response (idempotent — no error for already-logged-out sessions).

### Requirement 5: Forgot Password

**User Story:** As a user who has forgotten their password, I want to request a reset link, so that I can regain access to my account.

#### Acceptance Criteria

1. WHEN a POST request is received at `/api/v1/auth/forgot-password` with a registered email address, THE Auth_Service SHALL generate a cryptographically random Password_Reset_Token, store its hash in the Token_Store with a 1-hour TTL, and enqueue an Email_Worker task to send a password reset email containing the token.
2. WHEN a POST request is received at `/api/v1/auth/forgot-password` with an email address that does not exist in the database, THE Auth_Service SHALL return an HTTP 200 response with the same generic message as a successful request (to prevent user enumeration).
3. THE Auth_Service SHALL return an HTTP 200 response for all valid forgot-password requests regardless of whether the email exists.

### Requirement 6: Password Reset

**User Story:** As a user with a valid reset link, I want to set a new password, so that I can log in again.

#### Acceptance Criteria

1. WHEN a POST request is received at `/api/v1/auth/reset-password` with a valid, unexpired Password_Reset_Token and a new password meeting complexity requirements, THE Auth_Service SHALL hash the new password, update the User record, and delete the token from the Token_Store.
2. WHEN a POST request is received at `/api/v1/auth/reset-password` with an expired or invalid Password_Reset_Token, THE Auth_Service SHALL return an HTTP 400 response with the detail "Invalid or expired reset token".
3. WHEN a password reset succeeds, THE Auth_Service SHALL revoke all existing Refresh_Tokens for that user in the database to force re-authentication on all devices.
4. WHEN a POST request is received at `/api/v1/auth/reset-password` with a new password shorter than 8 characters or missing required complexity, THE Auth_Service SHALL return an HTTP 422 response with field-level validation errors.

### Requirement 7: Email Verification

**User Story:** As a newly registered user, I want to verify my email address, so that my account is fully activated.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/auth/verify-email/{token}` with a valid, unexpired Email_Verification_Token, THE Auth_Service SHALL set the User's `is_verified` flag to true and delete the token from the Token_Store.
2. WHEN a GET request is received at `/api/v1/auth/verify-email/{token}` with an invalid or expired Email_Verification_Token, THE Auth_Service SHALL return an HTTP 400 response with the detail "Invalid or expired verification token".
3. WHEN a GET request is received at `/api/v1/auth/verify-email/{token}` for a user whose `is_verified` flag is already true, THE Auth_Service SHALL return an HTTP 200 response (idempotent).

### Requirement 8: Current User Profile

**User Story:** As an authenticated user, I want to retrieve my profile, so that the frontend can display my account information.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/auth/me` with a valid Access_Token in the Authorization header, THE Auth_Service SHALL return an HTTP 200 response containing the serialized User object (id, email, full_name, avatar_url, is_verified, is_superuser).
2. WHEN a GET request is received at `/api/v1/auth/me` with an expired or missing Access_Token, THE Auth_Service SHALL return an HTTP 401 response.
3. WHEN a GET request is received at `/api/v1/auth/me` with a valid Access_Token for a user whose `is_active` flag is false, THE Auth_Service SHALL return an HTTP 403 response.

### Requirement 9: Refresh Token Persistence

**User Story:** As a system operator, I want refresh tokens stored in the database, so that sessions can be audited and revoked server-side.

#### Acceptance Criteria

1. THE Auth_Service SHALL maintain a `refresh_tokens` table with columns: id (UUID primary key), user_id (foreign key to users, CASCADE delete), token_hash (SHA-256 hash of the raw token, unique), expires_at (timestamp with timezone), revoked (boolean, default false), and created_at (timestamp with timezone).
2. WHEN a User record is deleted, THE Auth_Service SHALL automatically delete all associated refresh_tokens records via the CASCADE constraint.
3. THE Auth_Service SHALL store only the SHA-256 hash of the Refresh_Token in the database, never the raw token value.
4. THE Auth_Service SHALL provide an Alembic migration that creates the `refresh_tokens` table.

### Requirement 10: Frontend Auth Guard

**User Story:** As an unauthenticated visitor, I want to be redirected to the login page when I try to access protected routes, so that I cannot access the workspace without signing in.

#### Acceptance Criteria

1. WHEN the `/app` layout mounts and the auth state is not loading and the user is not authenticated, THE Auth_Guard SHALL redirect the browser to `/login`.
2. WHEN the auth state transitions from loading to unauthenticated (e.g., after a failed token refresh on startup), THE Auth_Guard SHALL redirect the browser to `/login`.
3. WHEN the application loads in the browser and a stored Access_Token exists in localStorage, THE Auth_Guard SHALL call `GET /api/v1/auth/me` to validate the token and populate the user state before rendering protected content.

### Requirement 11: Frontend Forgot Password Page

**User Story:** As a user who has forgotten their password, I want a dedicated page to request a reset email, so that I can recover my account from the browser.

#### Acceptance Criteria

1. THE Frontend SHALL provide a page at `/forgot-password` that renders a form with an email input field and a submit button.
2. WHEN the forgot-password form is submitted with a valid email, THE Frontend SHALL call `POST /api/v1/auth/forgot-password` and display a success message instructing the user to check their email.
3. WHEN the forgot-password form is submitted with an invalid email format, THE Frontend SHALL display a field-level validation error without making a network request.
4. IF the API call to `/api/v1/auth/forgot-password` returns an error, THEN THE Frontend SHALL display a toast notification with the error detail.

### Requirement 12: Frontend Email Verification Page

**User Story:** As a user who clicked a verification link, I want a dedicated page that processes the token, so that my account is marked as verified.

#### Acceptance Criteria

1. THE Frontend SHALL provide a page at `/verify-email/[token]` that automatically calls `GET /api/v1/auth/verify-email/{token}` on mount using the token from the URL path parameter.
2. WHEN the verification API call succeeds, THE Frontend SHALL display a success message and a link to `/login`.
3. WHEN the verification API call returns an error, THE Frontend SHALL display a descriptive error message and a link to request a new verification email.
4. WHILE the verification API call is in progress, THE Frontend SHALL display a loading indicator.

### Requirement 13: Email Delivery

**User Story:** As a user, I want to receive transactional emails (verification, password reset) reliably, so that I can complete account setup and recovery flows.

#### Acceptance Criteria

1. WHEN the Email_Worker task is invoked with a recipient address, subject, and HTML body, THE Email_Worker SHALL send the email via SMTP using the credentials defined in the application configuration (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD).
2. IF the SMTP connection fails, THEN THE Email_Worker SHALL retry the task up to 3 times with exponential backoff before marking the task as failed.
3. THE Email_Worker SHALL log the recipient address and subject for each email sent, without logging the email body content.
