#!/usr/bin/env node

import { AnalysisService } from '../hcp-mcp-common/dist/analysisService.js';

async function testAnalysis() {
  console.log('🧪 Testing Bulletproof Analysis Service...');
  
  const analysisService = new AnalysisService('dev');
  
  try {
    console.log('📊 Running laundry analysis...');
    const result = await analysisService.analyzeLaundryJobs();
    console.log('✅ Laundry Analysis Result:');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('❌ Laundry analysis failed:', error.message);
  }
  
  try {
    console.log('📊 Running job statistics analysis...');
    const result = await analysisService.analyzeJobStatistics();
    console.log('✅ Job Statistics Result:');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('❌ Job statistics analysis failed:', error.message);
  }
  
  try {
    console.log('📊 Running towel analysis...');
    const result = await analysisService.analyzeServiceItems('towel');
    console.log('✅ Towel Analysis Result:');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('❌ Towel analysis failed:', error.message);
  }
}

testAnalysis().then(() => {
  console.log('🎉 Analysis testing complete!');
  process.exit(0);
}).catch(error => {
  console.error('💥 Test failed:', error);
  process.exit(1);
});