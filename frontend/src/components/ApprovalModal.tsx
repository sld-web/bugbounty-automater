import React, { useState } from 'react';
import { Box, Button, Text, Textarea, Switch, Toaster, Toast } from '@chakra-ui/react';
import { useApi } from '../../hooks/useApi';
import { useAuth } from '../../contexts/AuthContext';
import { v4 as uuidv4 } from 'uuid';
import { ClipboardList, RefreshCw, X } from 'lucide-react';

interface ApprovalRequest {
  id: string;
  step_id: string;
  step_name: string;
  description: string;
  risk_level: string;
  requires_approval: boolean;
  approval_reason: string | null;
  proposed_action: string;
  requested_by: string;
  requested_at: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  response_note?: string;
  responded_at?: string;
  responded_by?: string;
}

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  approvalRequest: ApprovalRequest;
  onApprovalUpdate: (updatedRequest: ApprovalRequest) => void;
}

const ApprovalModal: React.FC<ApprovalModalProps> = ({
  isOpen,
  onClose,
  approvalRequest,
  onApprovalUpdate
}) => {
  const { api } = useApi();
  const { user } = useAuth();
  const [responseNote, setResponseNote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [toast] = useToast();

  const handleApprove = async () => {
    if (!user || isLoading) return;
    setIsLoading(true);
    try {
      // In a real implementation, we would update the approval request via API
      // For now, we'll simulate the update
      const updatedRequest = {
        ...approvalRequest,
        status: 'APPROVED',
        responded_at: new Date().toISOString(),
        responded_by: user.id || 'unknown_user',
        responseNote: responseNote
      };
      
      // Simulate API call
      // await api.approvals.updateApproval(approvalRequest.id, { status: 'APPROVED', responseNote });
      
      onApprovalUpdate(updatedRequest);
      
      toast.success('Approval granted');
      onClose();
    } catch (error) {
      toast.error(`Failed to grant approval: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    if (!user || isLoading) return;
    setIsLoading(true);
    try {
      // In a real implementation, we would update the approval request via API
      // For now, we'll simulate the update
      const updatedRequest = {
        ...approvalRequest,
        status: 'REJECTED',
        responded_at: new Date().toISOString(),
        responded_by: user.id || 'unknown_user',
        responseNote: responseNote
      };
      
      // Simulate API call
      // await api.approvals.updateApproval(approvalRequest.id, { status: 'REJECTED', responseNote });
      
      onApprovalUpdate(updatedRequest);
      
      toast.error('Approval rejected');
      onClose();
    } catch (error) {
      toast.error(`Failed to reject approval: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Box position="fixed" top="0" left="0" width="100vw" height="100vh" backgroundColor="rgba(0, 0, 0, 0.5)" display="flex" justifyContent="center" alignItems="center" zIndex={1100}>
      <Box backgroundColor="white" borderRadius="lg" p={6} w={[4, '500px']} maxH="90vh" overflow="auto" boxShadow="lg">
        <Box display="flex" justifyContent="between" alignItems="center" mb={4}>
          <Text fontSize="2xl" fontWeight="bold">
            Approval Required
          </Text>
          <Button onClick={onClose} variant="outline" colorScheme="red" size="sm">
            <X />
          </Button>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Step:</Text>
          <Text mt={1} fontFamily="monospace">{approvalRequest.step_name}</Text>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Description:</Text>
          <Text mt={1}>{approvalRequest.description}</Text>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Risk Level:</Text>
          <Text mt={1} fontSize="xl" fontWeight="bold" 
            color={approvalRequest.risk_level === 'low' ? 'green.500' : 
                   approvalRequest.risk_level === 'medium' ? 'yellow.500' : 
                   'red.500'}>
            {approvalRequest.risk_level.toUpperCase()}
          </Text>
          <Badge 
            ml={2} 
            colorScheme={approvalRequest.risk_level === 'low' ? 'green' : 
                       approvalRequest.risk_level === 'medium' ? 'yellow' : 
                       'red'}
          >
            {approvalRequest.risk_level}
          </Badge>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Reason for Approval:</Text>
          <Text mt={1}>{approvalRequest.approval_reason || 'No reason provided'}</Text>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Proposed Action:</Text>
          <Text mt={1} fontFamily="monospace" bg="gray.50" p={2} rounded>
            {approvalRequest.proposed_action}
          </Text>
        </Box>
        
        <Box mb={4}>
          <Text fontWeight="medium">Response Note (optional):</Text>
          <Textarea 
            value={responseNote}
            onChange={(e) => setResponseNote(e.target.value)}
            placeholder="Add any notes or conditions for your decision"
            rows={4}
            isDisabled={isLoading}
          />
        </Box>
        
        <Box mt={6} display="flex" justifyContent="between">
          <Button 
            onClick={handleReject}
            isLoading={isLoading}
            colorScheme="red"
            disabled={isLoading}
          >
            {isLoading ? 'Rejecting...' : 'Reject'}
          </Button>
          <Button 
            onClick={handleApprove}
            isLoading={isLoading}
            colorScheme="green"
            disabled={isLoading}
            ml={3}
          >
            {isLoading ? 'Approving...' : 'Approve'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default ApprovalModal;