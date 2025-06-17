const { execSync } = require('child_process');

// Function to run wrangler commands
function runWranglerCommand(command) {
    try {
        execSync(command, { stdio: 'inherit' });
        return true;
    } catch (error) {
        console.error(`Error executing command: ${command}`, error);
        return false;
    }
}

async function setupDomain() {
    console.log('Setting up custom domain...');

    // Create DNS record for the API subdomain
    console.log('Creating DNS record for api.cdatileandbath.com...');
    runWranglerCommand('wrangler dns create cdatileandbath.com api --type CNAME --content goodwill-app.cdatileandbath.workers.dev');

    // Enable SSL/TLS
    console.log('Enabling SSL/TLS...');
    runWranglerCommand('wrangler dns enable-ssl api.cdatileandbath.com');

    // Verify DNS propagation
    console.log('Verifying DNS propagation...');
    runWranglerCommand('wrangler dns verify api.cdatileandbath.com');

    console.log('Domain setup complete!');
}

setupDomain().catch(console.error); 