const form = document.getElementById('passkeyLoginForm');
const messageDiv = document.getElementById('message');
const loginBtn = document.getElementById('loginBtn');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;

    try {
        loginBtn.disabled = true;
        loginBtn.textContent = 'Authenticating...';
        messageDiv.innerHTML = '';

        console.log('Requesting login options for:', username);

        // Get authentication options from server
        const optionsResponse = await fetch('/api/passkey/login-options', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        console.log('Options response status:', optionsResponse.status);

        if (!optionsResponse.ok) {
            const error = await optionsResponse.json();
            console.error('Server error:', error);
            throw new Error(error.error || 'Failed to get authentication options');
        }

        const options = await optionsResponse.json();
        console.log('Login options:', options);

        // Convert challenge and credential IDs from base64url
        options.challenge = Uint8Array.from(
            atob(options.challenge.replace(/-/g, '+').replace(/_/g, '/')), 
            c => c.charCodeAt(0)
        );

        options.allowCredentials = options.allowCredentials.map(cred => ({
            ...cred,
            id: Uint8Array.from(
                atob(cred.id.replace(/-/g, '+').replace(/_/g, '/')), 
                c => c.charCodeAt(0)
            )
        }));

        console.log('Requesting credential from authenticator...');

        // Get credential from authenticator
        const credential = await navigator.credentials.get({ publicKey: options });
        console.log('Credential received:', credential);

        // Prepare credential for server
        const credentialJSON = {
            id: credential.id,
            rawId: arrayBufferToBase64(credential.rawId),
            type: credential.type,
            response: {
                authenticatorData: arrayBufferToBase64(credential.response.authenticatorData),
                clientDataJSON: arrayBufferToBase64(credential.response.clientDataJSON),
                signature: arrayBufferToBase64(credential.response.signature),
                userHandle: credential.response.userHandle ? arrayBufferToBase64(credential.response.userHandle) : null
            }
        };

        console.log('Verifying with server...');

        // Verify with server
        const verifyResponse = await fetch('/api/passkey/login-verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentialJSON)
        });

        const result = await verifyResponse.json();
        console.log('Verification result:', result);

        if (result.success) {
            messageDiv.innerHTML = '<div class="success">Login successful! Redirecting...</div>';
            setTimeout(() => window.location.href = '/questionnaire', 1000);
        } else {
            throw new Error('Authentication failed');
        }

    } catch (error) {
        console.error('Error:', error);
        let errorMsg = error.message;

        // User-friendly error messages
        if (error.name === 'NotAllowedError') {
            errorMsg = 'Authentication cancelled or timed out';
        } else if (error.message.includes('No passkey registered')) {
            errorMsg = 'No passkey found for this user. Please register a passkey first.';
        } else if (error.message.includes('User not found')) {
            errorMsg = 'User not found. Please check your username or register.';
        }

        messageDiv.innerHTML = '<div class="error">❌ ' + errorMsg + '</div>';
        loginBtn.disabled = false;
        loginBtn.textContent = '🔑 Login with Passkey';
    }
});

function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}