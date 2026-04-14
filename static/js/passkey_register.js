document.getElementById('credentialsSection').style.display = 'none';
document.getElementById('registerSection').style.display = 'block';

async function registerPasskey() {
    const btn = document.getElementById('registerBtn');
    const msg = document.getElementById('message');

    try {
        btn.disabled = true;
        btn.textContent = '🔄 Registering...';

        const res = await fetch('/api/passkey/register-options', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });

        if (!res.ok) {
            throw new Error('Failed to get registration options');
        }

        const opts = await res.json();
        console.log('Registration options:', opts);

        // Convert challenge from base64url to Uint8Array
        opts.challenge = Uint8Array.from(
            atob(opts.challenge.replace(/-/g, '+').replace(/_/g, '/')), 
            c => c.charCodeAt(0)
        );

        // Convert user.id from base64url to Uint8Array
        opts.user.id = Uint8Array.from(
            atob(opts.user.id.replace(/-/g, '+').replace(/_/g, '/')), 
            c => c.charCodeAt(0)
        );

        console.log('Creating credential...');
        const cred = await navigator.credentials.create({ publicKey: opts });
        console.log('Credential created:', cred);

        // Prepare credential for server
        const credJSON = {
            id: cred.id,
            rawId: arrayBufferToBase64(cred.rawId),
            type: cred.type,
            response: {
                attestationObject: arrayBufferToBase64(cred.response.attestationObject),
                clientDataJSON: arrayBufferToBase64(cred.response.clientDataJSON)
            }
        };

        console.log('Verifying with server...');
        const verifyRes = await fetch('/api/passkey/register-verify', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(credJSON)
        });

        const result = await verifyRes.json();
        console.log('Verification result:', result);

        if (result.success) {
            msg.innerHTML = '<div class="success">✅ Success! Redirecting...</div>';
            setTimeout(() => window.location.href = '/dashboard', 1500);
        } else {
            throw new Error('Verification failed');
        }

    } catch (error) {
        console.error('Error:', error);
        msg.innerHTML = '<div class="error">❌ ' + error.message + '</div>';
        btn.disabled = false;
        btn.textContent = '🔑 Register Passkey';
    }
}

function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}
