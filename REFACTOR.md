# Goal Description

The current application structure is monolithic, with all logic, configuration, database access, and routing combined into a single [app.py](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py) file. This makes the project highly coupled and difficult to extend. Furthermore, the front end is redundant with duplicated HTML boilerplates and inline CSS. The goal of this restructuring is to refactor the application into a maintainable modular structure using Flask Blueprints and a unified frontend templating system, maintaining exactly the same behavior.

## Task Breakdown

- [/] Clean up unused scripts ([check_routes.py](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/check_routes.py), [check_users.py](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/check_users.py), [debug_passkey.py](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/debug_passkey.py))
- [/] Restructure [app.py](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py) into a modular Flask application
  - [/] Move configuration to `config.py`
  - [/] Move database connections to `app/database.py`
  - [/] Move utility functions and encryption to `app/utils/`
  - [/] Create blueprints for routes (`app/routes/`)
    - [/] Main routes ([index](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#190-200), [dashboard](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#492-499))
    - [/] Classic Auth
    - [/] MFA Auth
    - [/] Passkey Auth
    - [/] Social Auth
- [ ] Refactor Frontend Templates
  - [ ] Create `static/css/style.css` with CSS variables for dynamic theming
  - [ ] Create root skeleton `templates/base.html`
  - [ ] Create flow layouts `templates/layouts/login_base.html` and `templates/layouts/setup_base.html`
  - [ ] Update all HTML files to extend appropriate layouts
- [ ] Update imports and `__init__.py` files
- [ ] Verify application works locally
- [ ] Update README

## Proposed Changes

We will refactor the application to use the Flask "Application Factory" pattern with Blueprints and layout-based frontend templates.

### Target Repository Structure
```text
passkey-instead-of-MFA/
├── modules/
│   ├── __init__.py           # App factory
│   ├── database.py           # Supabase client
│   ├── routes/               # Blueprints
│   │   ├── __init__.py
│   │   ├── auth_classic.py
│   │   ├── auth_otp.py
│   │   ├── auth_passkey.py
│   │   ├── auth_social.py
│   │   └── main.py
│   ├── services/
│   │   └── user_service.py   # DB queries
│   └── utils/
│       ├── decorators.py
│       ├── encryptor.py
│       └── passkey_helpers.py
├── config.py                 # Configuration variables
├── app.py                    # App entry point (simplified)
├── static/
│   └── css/
│       └── style.css         # Global and theme styles
└── templates/
    ├── base.html             # Root skeleton
    ├── layouts/
    │   ├── login_base.html
    │   └── setup_base.html
    └── *.html                # Refactored specific templates
```

### Core Application Setup
#### [NEW] `app/__init__.py`
Will initialize the Flask app and register blueprints.
#### [NEW] `config.py`
Will store all configuration variables and environment parsing logic currently in [app.py](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py).

---

### Database and Data Access
#### [NEW] `app/database.py`
Will initialize the Supabase client.
#### [NEW] `app/services/user_service.py`
Will contain functions like [get_user](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#143-152), [create_user](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#153-156), [update_mfa_secret](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#163-166), [add_passkey_credential](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#167-172), [create_social_user](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#157-162).

---

### Utilities and Middleware
#### [NEW] `app/utils/encryption.py`
Will house [encrypt_data](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#137-139) and [decrypt_data](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#140-142) as well as the Fernet key initialization logic.
#### [NEW] `app/utils/passkey_helpers.py`
Will contain [normalize_passkey_host](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#100-122), [get_passkey_rp_id](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#124-129), and [normalize_local_passkey_origin](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#202-223).
#### [NEW] `app/utils/decorators.py`
Will contain the [login_required](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#173-189) decorator.

---

### Routes (Blueprints)
#### [NEW] `app/routes/__init__.py`
#### [NEW] `app/routes/main.py`
Blueprint for [index](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#190-200) and [dashboard](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py#492-499) routes.
#### [NEW] `app/routes/auth_classic.py`
Blueprint for Registration and Password Login.
#### [NEW] `app/routes/auth_mfa.py`
Blueprint for MFA Setup, Login, and Verification.
#### [NEW] `app/routes/auth_passkey.py`
Blueprint for Passkey Login, Registration, and API endpoints.
#### [NEW] `app/routes/auth_social.py`
Blueprint for Google OAuth login and callbacks.

---

### Frontend Restructuring
#### [NEW] `static/css/style.css`
Will contain global styles (body, buttons, cards, typography). To handle different flow colors, we will use modern **CSS Variables** (e.g., `--theme-primary-color`). Different flows will simply add a class to the `<body>` (like `class="theme-mfa"` or `class="theme-passkey"`) which will override the color variables, keeping the CSS DRY (Don't Repeat Yourself) while avoiding multiple stylesheets.
#### [NEW] `templates/base.html`
The absolute root skeleton containing `<html>`, `<head>`, global metadata, and linking `style.css`.
#### [NEW] `templates/layouts/login_base.html` and `templates/layouts/setup_base.html`
Since each flow has Login and Setup parts, we will create layered template bases that extend `base.html`. These will define the layout structure (like the centered card) so the individual flow pages only provide the specific content.
#### [MODIFY] `templates/*.html`
All existing templates will extend the appropriate layout template, passing in their specific theme classes and content blocks.

---

### Application Entry Point
#### [MODIFY] [app.py](file:///Users/lejanskas/PycharmProjects/passkey-instead-of-MFA/app.py)
Will be simplified to just import the application factory `create_app()` from `app/__init__.py` and run it. The existing 500+ lines of code will be distributed to the modules.

## Verification Plan

### Automated Tests
* (No existing tests to run, but we will check that the app starts up without syntax errors or circular imports).

### Manual Verification
* Run the application locally and verify that:
  - The index page loads correctly with the new stylesheet.
  - Classic login and registration work.
  - MFA setup and login work.
  - Passkey registration and login work.
  - OAuth redirects to Google correctly.
