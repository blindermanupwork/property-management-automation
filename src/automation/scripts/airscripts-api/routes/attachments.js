const express = require('express');
const router = express.Router();
const { copyAttachmentsToFutureJobs } = require('../handlers/attachments');

// Copy attachments from source job to future jobs
router.post('/copy-to-future-jobs', copyAttachmentsToFutureJobs);

module.exports = router;