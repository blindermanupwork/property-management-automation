const express = require('express');
const router = express.Router();
const { checkSchedules, updateSchedule } = require('../handlers/schedules');

// POST /api/schedules - Check all schedules
router.post('/', checkSchedules);

// POST /api/schedules/:recordId - Update single schedule
router.post('/:recordId', updateSchedule);

// Legacy routes for backward compatibility
router.post('/check', checkSchedules);
router.post('/update', async (req, res) => {
  try {
    const { recordId } = req.body;
    if (!recordId) {
      return res.status(400).json({ error: 'recordId is required' });
    }
    
    req.params.recordId = recordId;
    await updateSchedule(req, res);
  } catch (error) {
    console.error('Update schedule error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;