import React, { useState } from 'react';
import { bankAPI } from '../../services/api.js';
import toast from 'react-hot-toast';
import { DollarSign, X, CheckCircle, Loader2 } from 'lucide-react';

const AddFundsModal = ({ isOpen, onClose, onFundsAdded }) => {
  const [amount, setAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAddFunds = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount.');
      return;
    }

    setIsProcessing(true);
    try {
      const userId = localStorage.getItem('userId');
      const response = await bankAPI.creditAccount({
        user_id: parseInt(userId),
        amount: parseFloat(amount),
      });

      if (response.data.success || response.data.new_balance) {
        toast.success(`Successfully added $${amount} to your account.`);
        onFundsAdded(response.data.new_balance);
        setAmount('');
        onClose();
      } else {
        throw new Error(response.data.error || 'Failed to add funds.');
      }
    } catch (error) {
      toast.error(error.message || 'An error occurred while adding funds.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-sm w-full">
        <div className="p-6 border-b border-slate-200 flex justify-between items-center">
          <h3 className="text-xl font-semibold text-slate-900">Add Funds</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div className="form-group">
            <label htmlFor="amount" className="form-label">
              Amount to Add
            </label>
            <div className="relative">
              <DollarSign className="w-5 h-5 text-slate-400 absolute left-3 top-3" />
              <input
                id="amount"
                name="amount"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="input pl-10"
                placeholder="e.g., 1000"
                disabled={isProcessing}
              />
            </div>
          </div>
        </div>
        <div className="p-6 border-t border-slate-200 flex space-x-3">
          <button
            onClick={onClose}
            className="btn btn-outline flex-1"
            disabled={isProcessing}
          >
            Cancel
          </button>
          <button
            onClick={handleAddFunds}
            className="btn btn-success flex-1 flex items-center justify-center space-x-2"
            disabled={isProcessing}
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Confirm Deposit</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddFundsModal;
