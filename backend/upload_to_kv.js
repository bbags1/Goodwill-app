const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

function uploadToKV(key, data) {
    // Create a temporary file
    const tempFile = path.join(os.tmpdir(), `kv-upload-${Date.now()}.json`);
    try {
        // Write data to temporary file
        fs.writeFileSync(tempFile, JSON.stringify(data));
        
        // Upload using the temporary file
        execSync(`wrangler kv:key put --binding=GOODWILL_KV "${key}" --preview=false < ${tempFile}`);
        console.log(`Successfully uploaded ${key}`);
    } catch (error) {
        console.error(`Error uploading ${key}:`, error);
        throw error;
    } finally {
        // Clean up temporary file
        if (fs.existsSync(tempFile)) {
            fs.unlinkSync(tempFile);
        }
    }
}

async function main() {
    const kvDataDir = path.join(__dirname, 'kv_data');
    
    // Upload main data files
    const files = ['items.json', 'settings.json', 'favorites.json', 'promising.json'];
    for (const file of files) {
        const filePath = path.join(kvDataDir, file);
        if (fs.existsSync(filePath)) {
            const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            try {
                uploadToKV(file, data);
            } catch (error) {
                console.error(`Error uploading ${file}:`, error);
            }
        }
    }
    
    // Upload search index
    const searchIndexPath = path.join(kvDataDir, 'search_index.json');
    if (fs.existsSync(searchIndexPath)) {
        const searchIndex = JSON.parse(fs.readFileSync(searchIndexPath, 'utf8'));
        for (const [term, itemIds] of Object.entries(searchIndex)) {
            try {
                uploadToKV(`search:${term}`, itemIds);
                console.log(`Successfully uploaded search index for term ${term}`);
            } catch (error) {
                console.error(`Error uploading search index for term ${term}:`, error);
            }
        }
    }
}

main().catch(console.error); 