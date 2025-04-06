package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Evidence structure
type Evidence struct {
	ID            string            `json:"id"`
	CID           string            `json:"cid"`
	FileHash      string            `json:"fileHash"`
	EvdName       string            `json:"evd_name"`
	CaseNum       string            `json:"case_num"`
	Description   string            `json:"description"`
	FileType      string            `json:"fileType"`
	Metadata      map[string]string `json:"metadata"`
	CustomData    string            `json:"customData,omitempty"`
	AddedByFabric string            `json:"addedByFabric"`
	AddedByDjango string            `json:"addedByDjango"`
	Timestamp     string            `json:"timestamp"`
}

// HistoryRecord structure for evidence history
type HistoryRecord struct {
	TxID      string    `json:"txId"`
	Timestamp string    `json:"timestamp"`
	Evidence  *Evidence `json:"evidence"`
	AddedByDjango string `json:"addedByDjango"`
}

// SmartContract for managing evidence
type SmartContract struct {
	contractapi.Contract
}

// AddEvidence function
func (s *SmartContract) AddEvidence(ctx contractapi.TransactionContextInterface, id, cid, fileHash, evdName, caseNum, description, fileType, metadataJSON, customData, addedByDjango string) error {
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}

	var metadata map[string]string
	if err := json.Unmarshal([]byte(metadataJSON), &metadata); err != nil {
		return fmt.Errorf("failed to parse metadata: %v", err)
	}

	txTime, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return fmt.Errorf("failed to get transaction timestamp: %v", err)
	}

	evidence := Evidence{
		ID:            id,
		CID:           cid,
		FileHash:      fileHash,
		EvdName:       evdName,
		CaseNum:       caseNum,
		Description:   description,
		FileType:      fileType,
		Metadata:      metadata,
		CustomData:    customData,
		AddedByFabric: clientID,
		AddedByDjango: addedByDjango,
		Timestamp:     txTime.String(),
	}

	evidenceJSON, err := json.Marshal(evidence)
	if err != nil {
		return fmt.Errorf("failed to serialize evidence: %v", err)
	}

	return ctx.GetStub().PutState(id, evidenceJSON)
}

// GetEvidence retrieves evidence from the ledger
func (s *SmartContract) GetEvidence(ctx contractapi.TransactionContextInterface, id string) (*Evidence, error) {
	evidenceJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve evidence: %v", err)
	}
	if evidenceJSON == nil {
		return nil, fmt.Errorf("evidence with ID %s not found", id)
	}

	var evidence Evidence
	err = json.Unmarshal(evidenceJSON, &evidence)
	if err != nil {
		return nil, fmt.Errorf("failed to parse evidence data: %v", err)
	}

	return &evidence, nil
}

// TransferEvidence function
func (s *SmartContract) TransferEvidence(ctx contractapi.TransactionContextInterface, id, newOwnerDjango string) error {
	evidenceJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return fmt.Errorf("failed to retrieve evidence: %v", err)
	}
	if evidenceJSON == nil {
		return fmt.Errorf("evidence with ID %s not found", id)
	}

	var evidence Evidence
	if err := json.Unmarshal(evidenceJSON, &evidence); err != nil {
		return fmt.Errorf("failed to parse evidence data: %v", err)
	}

	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}

	if evidence.AddedByFabric != clientID {
		return fmt.Errorf("only the current owner (%s) can transfer this evidence", evidence.AddedByFabric)
	}

	evidence.AddedByDjango = newOwnerDjango

	updatedEvidenceJSON, err := json.Marshal(evidence)
	if err != nil {
		return fmt.Errorf("failed to serialize updated evidence: %v", err)
	}

	return ctx.GetStub().PutState(id, updatedEvidenceJSON)
}

// GetEvidenceHistory retrieves the full history of an evidence record, including transaction metadata
func (s *SmartContract) GetEvidenceHistory(ctx contractapi.TransactionContextInterface, id string) ([]*HistoryRecord, error) {
	resultsIterator, err := ctx.GetStub().GetHistoryForKey(id)
	if err != nil {
		return nil, fmt.Errorf("failed to get history for evidence: %v", err)
	}
	defer resultsIterator.Close()

	var history []*HistoryRecord
	for resultsIterator.HasNext() {
		modification, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate history: %v", err)
		}

		var evidence Evidence
		if len(modification.Value) > 0 {
			if err := json.Unmarshal(modification.Value, &evidence); err != nil {
				return nil, fmt.Errorf("failed to parse historical record: %v", err)
			}
		} else {
			// If Value is empty (e.g., deleted), still record the event with empty addedByDjango
			evidence = Evidence{ID: id}
		}

		// Create a simplified HistoryRecord
		record := &HistoryRecord{
			TxID:          modification.TxId,
			Timestamp:     modification.Timestamp.String(),
			AddedByDjango: evidence.AddedByDjango,
		}

		history = append(history, record)
	}

	return history, nil
}

// Main function
func main() {
	chaincode, err := contractapi.NewChaincode(new(SmartContract))
	if err != nil {
		fmt.Printf("Error creating chaincode: %v", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting chaincode: %v", err)
	}
}
