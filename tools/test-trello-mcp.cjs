const { spawn } = require('child_process');
const path = require('path');

async function testTrelloMCP() {
    console.log('Testing Trello MCP Server...\n');
    
    const serverPath = path.join(__dirname, 'trello-mcp-server', 'build', 'index.js');
    
    // Set environment variable
    process.env.TRELLO_API_KEY = 'ATATT3xFfGF01CeHncg8jc_JLplKrfzRVt2JOUiCApluqax6fxkEyv-IWYGqx54E24eTfTFcZ0z3FKbyETg-sJjqoqMH6w0ERrdEClxYcU7Fh_rpeCecZyFPLDyIDfEGnJ27uqXhJiGyOi9INIkYGgI8lum1NxamY0LPPOusT8Rc7mwxODBCu10=FF6F9290';
    
    const server = spawn('node', [serverPath], {
        env: process.env,
        stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    
    server.stdout.on('data', (data) => {
        output += data.toString();
        console.log('Server output:', data.toString());
    });
    
    server.stderr.on('data', (data) => {
        console.error('Server error:', data.toString());
    });
    
    server.on('error', (error) => {
        console.error('Failed to start server:', error);
    });
    
    // Send a test request
    setTimeout(() => {
        const testRequest = {
            jsonrpc: '2.0',
            method: 'tools/list',
            id: 1
        };
        
        server.stdin.write(JSON.stringify(testRequest) + '\n');
        
        setTimeout(() => {
            console.log('\nTest complete. Shutting down server...');
            server.kill();
            process.exit(0);
        }, 2000);
    }, 1000);
}

testTrelloMCP().catch(console.error);