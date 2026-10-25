# Cookbook: Enable SSO

Add company single sign-on on top of tokens - the **full** posture, where people are sent to their company login and then mint their own tokens. This is the ordered task; the concepts and login flow are in [Security: Advanced - Single sign-on](Security-Advanced.md#single-sign-on-full-setting) and the configuration mechanism (files, defaults, couplings) in [Configuration: Advanced - Single sign-on](Configuration-Advanced.md#single-sign-on-sso).

**Audience:** Operator, with your identity-provider administrator for the registration step.
**Prerequisites:** [Cookbook: Enable Tokens](Cookbook-Enable-Tokens.md) done, and a SAML identity provider you can register a service provider with.

---

## Before you start

- **Full** is tokens-only **plus** the login doorway. Until the single sign-on files are provisioned, the deployment stays at tokens-only.
- Single sign-on changes how **people in a browser** authenticate (the dashboard bounces them to company login). Command-line callers still carry a personal token, exactly as under tokens-only.

---

## Steps

1. **Drop the SAML files into `resources/rest.sso/`** on the gateway deploy project: the SAML configuration, the service-provider keystore, the identity provider's certificate, and the doorway's own signing keystore. *(→ [Configuration: Advanced - Single sign-on](Configuration-Advanced.md#single-sign-on-sso))*
2. **Give the gateway the doorway's public signing certificate**, so it verifies single sign-on access tokens offline. *(→ [Configuration: Advanced - Single sign-on](Configuration-Advanced.md#single-sign-on-sso))*
3. **Set the allowed-origins** for the dashboard - it calls the gateway cross-origin. *(→ [Configuration: Advanced - Single sign-on](Configuration-Advanced.md#single-sign-on-sso))*
4. **Confirm the two couplings agree.** Issuer and audience must match across the doorway and the gateway (they already agree at their defaults), and the certificate the gateway holds must be the public half of the doorway's signing keypair. *(→ [Configuration: Advanced - Single sign-on](Configuration-Advanced.md#single-sign-on-sso))*
5. **Register the service provider at your identity provider:** the entityID `MetaFluentJMS` (keep the default so existing registrations still match), the doorway's assertion-consumer (ACS) URL, and the role attribute that delivers `metafluent-admin` / `metafluent-guest`. *(→ [Security: Advanced - The company-login contract](Security-Advanced.md#the-company-login-contract-saml))*
6. **Bring the doorway up** (restart, or deploy the `-cfg-<tag>` image if you baked the config in).

---

## Verify

- **Dashboard:** open it - the browser bounces to company login and returns signed in, with no token handling by the user.
- **Pasted URL:** paste an API URL (the doorway host) into a browser - after the login bounce it returns the raw result.
- **Self-report:** the configuration self-report shows the gateway with single sign-on enforcement armed (see [Configuration: Basics](Configuration-Basics.md)).
- **Roles:** a user in the `metafluent-admin` group can mint their own token at the token page; a `metafluent-guest` user gets look-only access.

If single sign-on calls are silently rejected, re-check step 4 - a mismatched issuer / audience or an unpaired signing certificate fails every token with no startup error.

---

## Turn it off

Remove the single sign-on files from `resources/rest.sso/`, along with the gateway's signing certificate and allowed-origins, and restart. The deployment falls back to **tokens-only** - personal tokens stay enforced; only the company-login layer is gone.

---

## Related pages

- [Cookbook: Enable Tokens](Cookbook-Enable-Tokens.md) - the prerequisite posture.
- [Configuration: Advanced - Single sign-on](Configuration-Advanced.md#single-sign-on-sso) - the files, the defaults, and the couplings.
- [Security: Advanced - Single sign-on](Security-Advanced.md#single-sign-on-full-setting) - the login and token-refresh flow, and the SAML contract.
- [API Token Administration - Personal tokens via single sign-on](API-Token-Administration.md#7-personal-tokens-via-single-sign-on) - personal tokens obtained through single sign-on.
