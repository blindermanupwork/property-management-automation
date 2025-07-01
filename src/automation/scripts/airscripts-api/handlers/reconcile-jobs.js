const { spawn } = require('child_process');
const path = require('path');

/**
 * Handle HCP job reconciliation requests from Airtable
 * Can be triggered via Run Now button or scheduled automation
 */
async function handleReconcileJobs(req, res) {
    try {
        const { 
            environment = 'dev', 
            mode = 'dry_run',  // 'dry_run' or 'execute'
            limit = null 
        } = req.body;

        console.log(`[Reconcile Jobs] Starting reconciliation - Environment: ${environment}, Mode: ${mode}`);

        // Build command arguments
        const scriptPath = path.join(__dirname, '../../../hcp/reconcile-jobs-optimized.py');
        const args = ['python3', scriptPath, '--env', environment, '--json'];
        
        if (mode === 'execute') {
            args.push('--execute');
        }
        
        if (limit) {
            args.push('--limit', limit.toString());
        }

        // Execute the Python script
        const pythonProcess = spawn(args[0], args.slice(1), {
            cwd: path.dirname(scriptPath)
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
            console.error(`[Reconcile Jobs] Python stderr: ${data}`);
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                console.error(`[Reconcile Jobs] Process exited with code ${code}`);
                console.error(`[Reconcile Jobs] stderr: ${stderr}`);
                
                res.status(500).json({
                    success: false,
                    error: 'Reconciliation process failed',
                    details: stderr,
                    environment,
                    mode
                });
                return;
            }

            try {
                // Parse the JSON output from the Python script
                const result = JSON.parse(stdout);
                
                // Format response for Airtable
                const response = {
                    success: result.success,
                    environment: result.environment,
                    mode: result.mode,
                    timestamp: new Date().toISOString(),
                    summary: {
                        total_processed: result.results.total,
                        matched: result.results.matched,
                        unmatched: result.results.unmatched,
                        match_rate: result.results.total > 0 
                            ? `${((result.results.matched / result.results.total) * 100).toFixed(1)}%`
                            : '0%'
                    },
                    message: result.message || 'Reconciliation completed',
                    details: result.results
                };

                console.log(`[Reconcile Jobs] Success - Matched: ${result.results.matched}, Unmatched: ${result.results.unmatched}`);
                res.json(response);
                
            } catch (parseError) {
                console.error(`[Reconcile Jobs] Failed to parse output: ${parseError}`);
                console.error(`[Reconcile Jobs] Raw output: ${stdout}`);
                
                res.status(500).json({
                    success: false,
                    error: 'Failed to parse reconciliation results',
                    details: stdout,
                    environment,
                    mode
                });
            }
        });

        pythonProcess.on('error', (error) => {
            console.error(`[Reconcile Jobs] Failed to start process: ${error}`);
            res.status(500).json({
                success: false,
                error: 'Failed to start reconciliation process',
                details: error.message,
                environment,
                mode
            });
        });

    } catch (error) {
        console.error('[Reconcile Jobs] Error:', error);
        res.status(500).json({
            success: false,
            error: error.message,
            environment: req.body.environment || 'dev',
            mode: req.body.mode || 'dry_run'
        });
    }
}

module.exports = { handleReconcileJobs };