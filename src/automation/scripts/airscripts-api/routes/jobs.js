const express = require('express');
const router = express.Router();
const { createJob, deleteJob } = require('../handlers/jobs');

// POST /api/jobs/:recordId - Create a single HCP job
router.post('/:recordId', createJob);

// POST /api/jobs/create-batch - Create multiple HCP jobs
router.post('/create-batch', async (req, res) => {
  try {
    const { recordIds } = req.body;
    if (!recordIds || !Array.isArray(recordIds)) {
      return res.status(400).json({ error: 'recordIds array is required' });
    }
    
    const results = await Promise.all(
      recordIds.map(id => createJob(id).catch(err => ({ error: err.message, recordId: id })))
    );
    
    res.json({ results });
  } catch (error) {
    console.error('Batch create error:', error);
    res.status(500).json({ error: error.message });
  }
});

// DELETE /api/jobs/:recordId - Delete a single HCP job schedule
router.delete('/:recordId', deleteJob);

module.exports = router;