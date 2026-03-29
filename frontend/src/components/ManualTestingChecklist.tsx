import React, { useState, useEffect } from 'react';
import { Box, Button, Text, Textarea, Input, Switch, Badge, Spinner, Toaster, Toast } from '@chakra-ui/react';
import { useApi } from '../../hooks/useApi';
import { useAuth } from '../../contexts/AuthContext';
import { v4 as uuidv4 } from 'uuid';

interface Hypothesis {
  id: string;
  description: string;
  type: string; // e.g., 'IDOR', 'XSS', 'SQLi', etc.
  endpoint: string;
  method: string;
  payload: string;
  expected_behavior: string;
  test_results?: TestResult[];
}

interface TestResult {
  id: string;
  hypothesis_id: string;
  timestamp: string;
  payload_used: string;
  response_status: number;
  response_body: string;
  success: boolean;
  notes: string;
  screenshot?: string; // base64 or URL
}

interface ManualTestingChecklistProps {
  targetId: string;
  endpoint: string;
  hypotheses: Hypothesis[];
  onHypothesisTested: (hypothesisId: string, result: TestResult) => void;
}

const ManualTestingChecklist: React.FC<ManualTestingChecklistProps> = ({
  targetId,
  endpoint,
  hypotheses,
  onHypothesisTested
}) => {
  const { api } = useApi();
  const { user } = useAuth();
  const [currentHypothesisIndex, setCurrentHypothesisIndex] = useState(0);
  const [testResults, setTestResults] = useState<Record<string, TestResult[]>>({});
  const [isTesting, setIsTesting] = useState(false);
  const [testPayload, setTestPayload] = useState('');
  const [testNotes, setTestNotes] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null);
  const [toast] = useToast();

  const currentHypothesis = hypotheses[currentHypothesisIndex];

  useEffect(() => {
    // Reset form when hypothesis changes
    setTestPayload('');
    setTestNotes('');
  }, [currentHypothesisIndex]);

  const handleTestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentHypothesis || !user) return;

    setIsTesting(true);
    
    try {
      // In a real implementation, this would make an actual HTTP request
      // For now, we'll simulate the test
      const testResult: TestResult = {
        id: uuidv4(),
        hypothesis_id: currentHypothesis.id,
        timestamp: new Date().toISOString(),
        payload_used: testPayload || currentHypothesis.payload,
        response_status: 200, // Simulated
        response_body: '{"message": "Test successful"}', // Simulated
        success: Math.random() > 0.5, // Random success for demo
        notes: testNotes,
        // screenshot: ... would be captured in real implementation
      };

      // Save result
      setTestResults(prev => ({
        ...prev,
        [currentHypothesis.id]: [...(prev[currentHypothesis.id] || []), testResult]
      }));

      // Notify parent
      onHypothesisTested(currentHypothesis.id, testResult);

      // Show toast
      toast({
        title: testResult.success ? 'Test Completed' : 'Test Failed',
        description: testResult.success 
          ? 'The test was successful - potential vulnerability detected!' 
          : 'The test did not produce the expected result.',
        status: testResult.success ? 'success' : 'error',
        duration: 5000,
        isClosable: true,
      });

      // Auto-advance to next hypothesis if successful
      if (testResult.success && currentHypothesisIndex < hypotheses.length - 1) {
        setCurrentHypothesisIndex(currentHypothesisIndex + 1);
      }

    } catch (error) {
      toast({
        title: 'Test Error',
        description: `An error occurred during testing: ${error.message}`,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSkipHypothesis = () => {
    if (currentHypothesisIndex < hypotheses.length - 1) {
      setCurrentHypothesisIndex(currentHypothesisIndex + 1);
      setTestPayload('');
      setTestNotes('');
    }
  };

  const handleViewResult = (result: TestResult) => {
    setSelectedResult(result);
    setShowResults(true);
  };

  const handleCloseResultView = () => {
    setSelectedResult(null);
    setShowResults(false);
  };

  const getProgressPercent = () => {
    return ((currentHypothesisIndex + 1) / hypotheses.length) * 100;
  };

  if (hypotheses.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Text color="gray.500">No hypotheses to test for this endpoint</Text>
      </Box>
    );
  }

  const progress = getProgressPercent();
  const isLastHypothesis = currentHypothesisIndex === hypotheses.length - 1;

  return (
    <Box>
      {/* Header */}
      <Box borderBottom="1px" borderColor="gray.200" pb={4} mb={6}>
        <Text fontSize="2xl" fontWeight="bold">
          Manual Testing Checklist
        </Text>
        <Text color="gray.500" mt={2}>
          Testing {currentHypothesisIndex + 1} of {hypotheses.length} hypotheses
        </Text>
        <Box mt={3} w="100%" h={4} borderWidth="1px" borderColor="gray.300" borderRadius="2px" overflow="hidden">
          <Box 
            bg="teal.500" 
            h="100%" 
            width={`${progress}%`} 
            transition="width 0.3s ease"
          />
        </Box>
      </Box>

      {/* Current Hypothesis */}
      <Box borderWidth="1px" borderColor="gray.200" borderRadius="lg" p={6} mb={6}>
        <Text fontSize="xl" fontWeight="600" mb={4}>
          Hypothesis {currentHypothesisIndex + 1}: {currentHypothesis.type}
        </Text>
        
        <Box mb={4}>
          <Text fontWeight="medium">Description:</Text>
          <Text mt={1} mb={3}>{currentHypothesis.description}</Text>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Endpoint:</Text>
          <Text mt={1} fontFamily="monospace" mb={3}>
            {currentHypothesis.method} {currentHypothesis.endpoint}
          </Text>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Expected Behavior:</Text>
          <Text mt={1} mb={3}>{currentHypothesis.expected_behavior}</Text>
        </Box>
        
        {/* Test Results History */}
        <Box mb={4}>
          <Text fontWeight="medium">Test History:</Text>
          {testResults[currentHypothesis.id] && testResults[currentHypothesis.id].length > 0 ? (
            <Box mt={2}>
              {testResults[currentHypothesis.id].map((result, index) => (
                <Box 
                  key={index} 
                  borderWidth="1px" 
                  borderColor="gray.200" 
                  borderRadius="md" 
                  p={3} 
                  mb={2}
                  backgroundColor={result.success ? 'green.50' : 'red.50'}
                >
                  <Box display="flex" justifyContent="between">
                    <Text fontSize="sm" fontWeight="medium">
                      Test #{index + 1} - {result.success ? 'SUCCESS' : 'FAILED'}
                    </Text>
                    <Text fontSize="xs" color="gray.500">
                      {new Date(result.timestamp).toLocaleTimeString()}
                    </Text>
                  </Box>
                  <Text mt={1} fontSize="sm">
                    Payload: {result.payload_used}
                  </Text>
                  {result.notes && (
                    <Box mt={1}>
                      <Text fontSize="sm" fontWeight="medium">Notes:</Text>
                      <Text mt={0.5} fontSize="xs">{result.notes}</Text>
                    </Box>
                  )}
                </Box>
              ))}
            </Box>
          ) : (
            <Text color="gray.500" fontSize="sm">
              No tests performed yet for this hypothesis
            </Text>
          )}
        </Box>
      </Box>

      {/* Testing Form */}
      <Box borderWidth="1px" borderColor="gray.200" borderRadius="lg" p={6}>
        <Text fontSize="xl" fontWeight="600" mb={4}>
          Test Hypothesis
        </Text>
        
        <form onSubmit={handleTestSubmit}>
          <Box mb={4}>
            <Text fontWeight="medium">Test Payload:</Text>
            <Textarea 
              value={testPayload}
              onChange={(e) => setTestPayload(e.target.value)}
              placeholder="Enter the payload to test (leave empty to use default)"
              rows={4}
              isDisabled={isTesting}
              placeholderText="Using default hypothesis payload if empty"
            />
          </Box>
          
          <Box mb={4}>
            <Text fontWeight="medium">Test Notes (optional):</Text>
            <Textarea 
              value={testNotes}
              onChange={(e) => setTestNotes(e.target.value)}
              placeholder="Add any observations or notes about the test"
              rows={3}
              isDisabled={isTesting}
            />
          </Box>
          
          <Box display="flex" justifyContent="between" alignItems="center" mb={6}>
            <Button 
              onClick={handleTestSubmit}
              isLoading={isTesting}
              colorScheme={isLastHypothesis ? 'teal' : 'blue'}
              disabled={isTesting}
              width="auto"
            >
              {isTesting ? 'Testing...' : isLastHypothesis ? 'Final Test' : 'Run Test'}
            </Button>
            
            <Button 
              onClick={handleSkipHypothesis}
              isLoading={isTesting}
              colorScheme="gray"
              disabled={isTesting || isLastHypothesis}
              ml={3}
              width="auto"
            >
              {isLastHypothesis ? 'Complete Testing' : 'Skip to Next'}
            </Button>
          </Box>
        </form>
      </Box>

      {/* Results Viewer Modal */}
      <Box 
        position="fixed"
        top="0"
        left="0"
        width="100vw"
        height="100vh"
        backgroundColor="rgba(0, 0, 0, 0.5)"
        display={showResults ? 'flex' : 'none'}
        justifyContent="center"
        alignItems="center"
        zIndex={1000}
      >
        <Box 
          backgroundColor="white"
          borderRadius="lg"
          p={6}
          w={[5, '750px']}
          maxH="90vh"
          overflow="auto"
          boxShadow="lg"
        >
          <Box display="flex" justifyContent="between" alignItems="center" mb={4}>
            <Text fontSize="2xl" fontWeight="bold">
              Test Results Details
            </Text>
            <Button 
              onClick={handleCloseResultView}
              variant="outline"
              colorScheme="red"
              size="sm"
            >
              Close
            </Button>
          </Box>
          
          {selectedResult && (
            <Box>
              <Box mb={4}>
                <Text fontWeight="medium">Test ID:</Text>
                <Text mt={1} fontFamily="monospace">{selectedResult.id}</Text>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="medium">Timestamp:</Text>
                <Text mt={1} fontFamily="monospace">
                  {new Date(selectedResult.timestamp).toLocaleString()}
                </Text>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="medium">Hypothesis ID:</Text>
                <Text mt={1} fontFamily="monospace">{selectedResult.hypothesis_id}</Text>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="medium">Payload Used:</Text>
                <Text mt={1} fontFamily="monospace" bg="gray.50" p={2} rounded>
                  {selectedResult.payload_used}
                </Text>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="medium">Response Status:</Text>
                <Text mt={1} fontSize="2xl" fontWeight="bold" 
                  color={selectedResult.response_status >= 200 && selectedResult.response_status < 300 ? 'teal.600' : 
                         selectedResult.response_status >= 400 && selectedResult.response_status < 500 ? 'orange.600' : 
                         'red.600'}>
                  {selectedResult.response_status}
                </Text>
                <Badge 
                  ml={2} 
                  colorScheme={selectedResult.response_status >= 200 && selectedResult.response_status < 300 ? 'green' : 
                            selectedResult.response_status >= 400 && selectedResult.response_status < 500 ? 'orange' : 
                            'red'}
                >
                  {selectedResult.response_status >= 200 && selectedResult.response_status < 300 ? 'Success' : 
                    selectedResult.response_status >= 400 && selectedResult.response_status < 500 ? 'Client Error' : 
                    'Other'}
                </Badge>
              </Box>
              
              <Box mb={4}>
                <Text fontWeight="medium">Response Body:</Text>
                <Textarea 
                  value={selectedResult.response_body}
                  isReadOnly
                  rows={10}
                  fontFamily="monospace"
                  bg="gray.50"
                  p={2}
                />
              </Box>
              
              {selectedResult.notes && (
                <Box mb={4}>
                  <Text fontWeight="medium">Test Notes:</Text>
                  <Text mt={1}>{selectedResult.notes}</Text>
                </Box>
              )}
              
              {selectedResult.screenshot && (
                <Box mb={4}>
                  <Text fontWeight="medium">Screenshot:</Text>
                  <Image 
                    src={`data:image/png;base64,${selectedResult.screenshot}`}
                    alt="Test screenshot"
                    maxW="100%"
                    borderRadius="md"
                  />
                </Box>
              )}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default ManualTestingChecklist;